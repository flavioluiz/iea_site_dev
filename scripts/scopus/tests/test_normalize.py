from pathlib import Path
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "normalize.py"
SPEC = importlib.util.spec_from_file_location("scopus_normalize", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def entry(
    number: int,
    citations: int = 4,
    title: str | None = None,
    doi: str | None = "unique",
) -> dict:
    value = json.loads((Path(__file__).parent / "fixtures" / "search_entry.json").read_text())
    value["eid"] = f"2-s2.0-{number}"
    value["citedby-count"] = str(citations)
    value["dc:title"] = title or f"Publicação {number}"
    value["prism:doi"] = f"10.0000/test.{number}" if doi == "unique" else doi
    return value


class ScopusNormalizeTests(unittest.TestCase):
    def test_public_contract_excludes_abstract_and_keywords(self) -> None:
        fixture = json.loads((Path(__file__).parent / "fixtures" / "search_entry.json").read_text())
        record = MODULE.normalize_entry(
            fixture,
            "flavio-luiz-c-ribeiro",
            "Flávio Luiz Cardoso Ribeiro",
            {"12345"},
            "2026-08-14T12:00:00Z",
        )
        self.assertNotIn("abstract", record)
        self.assertNotIn("authkeywords", record)
        self.assertNotIn("subject_areas", record["scopus"])
        self.assertEqual(record["authors"][0]["eam_professor_id"], "flavio-luiz-c-ribeiro")
        self.assertEqual(record["scopus"]["citations"], 4)

    def test_invalid_eid_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            MODULE.normalize_entry(
                {"eid": "invalido"}, "pessoa", "Pessoa", {"1"}, "2026-08-14T12:00:00Z"
            )

    def make_tree(
        self,
        root: Path,
        previous_count: int,
        current_count: int,
        *,
        current_citations: int = 4,
        extra_previous_author: bool = False,
    ) -> tuple[Path, Path, Path, Path]:
        site = root / "site"
        previous = root / "previous"
        staging = root / "staging"
        output = root / "output"
        professors = [{
            "id": "professor",
            "nome": "Pessoa Docente",
            "ativo": True,
            "scopus_author_ids": ["12345"],
        }]
        write_json(site / "data" / "pessoal" / "professores.json", {"professores": professors})
        refs = []
        for number in range(1, previous_count + 1):
            publication = MODULE.normalize_entry(
                entry(number), "professor", "Pessoa Docente", {"12345"}, "2026-08-01T00:00:00Z"
            )
            write_json(previous / "publications" / "by_eid" / f"{number}.json", publication)
            refs.append({
                "publication_id": f"2-s2.0-{number}",
                "author_position": 1,
                "is_corresponding_author": False,
            })
        authors = {
            "professor": {
                "metrics": MODULE.author_metrics([], "2026-08-01"),
                "publicacoes": refs,
                "metadata": {"source": "scopus", "updated_at": "2026-08-01T00:00:00Z"},
            }
        }
        if extra_previous_author:
            authors["pessoa-inativa"] = {
                "metrics": MODULE.author_metrics([], "2026-08-01"),
                "publicacoes": [],
                "metadata": {"source": "scopus", "updated_at": "2026-08-01T00:00:00Z"},
            }
        write_json(previous / "autores.json", {"schema_version": 1, "autores": authors})
        write_json(
            staging / "professor.json",
            {
                "professor_id": "professor",
                "scopus_author_ids": ["12345"],
                "authors": [],
                "publications": [entry(number, current_citations) for number in range(1, current_count + 1)],
            },
        )
        return site, previous, staging, output

    def run_main(
        self,
        root: Path,
        site: Path,
        previous: Path,
        staging: Path,
        output: Path,
        *,
        full: bool = True,
    ) -> int:
        argv = [
            "normalize.py",
            "--site-root", str(site),
            "--input", str(staging),
            "--output", str(output),
            "--previous", str(previous),
            "--report", str(root / "report.md"),
        ]
        if full:
            argv.append("--full")
        with patch.object(sys, "argv", argv):
            return MODULE.main()

    def test_citation_only_change_is_written_and_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            site, previous, staging, output = self.make_tree(
                root, previous_count=1, current_count=1, current_citations=9
            )
            self.assertEqual(self.run_main(root, site, previous, staging, output), 0)
            publication = json.loads((output / "publications" / "by_eid" / "1.json").read_text())
            self.assertEqual(publication["scopus"]["citations"], 9)
            report = (root / "report.md").read_text()
            self.assertIn("Publicações: +0 / ~1 / -0", report)

    def test_global_drop_above_five_percent_preserves_last_good_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            site, previous, staging, output = self.make_tree(root, previous_count=20, current_count=18)
            before = (previous / "publications" / "by_eid" / "20.json").read_bytes()
            self.assertEqual(self.run_main(root, site, previous, staging, output), 1)
            self.assertEqual((previous / "publications" / "by_eid" / "20.json").read_bytes(), before)
            self.assertFalse(list(output.rglob("*.json")))

    def test_per_professor_drop_above_twenty_percent_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            site, previous, staging, output = self.make_tree(root, previous_count=10, current_count=7)
            self.assertEqual(self.run_main(root, site, previous, staging, output), 1)
            self.assertFalse(list(output.rglob("*.json")))

    def test_complete_run_removes_generated_author_no_longer_curated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            site, previous, staging, output = self.make_tree(
                root, previous_count=1, current_count=1, extra_previous_author=True
            )
            self.assertEqual(self.run_main(root, site, previous, staging, output), 0)
            authors = json.loads((output / "autores.json").read_text())["autores"]
            self.assertEqual(set(authors), {"professor"})
            self.assertIn("Removida: `pessoa-inativa`", (root / "report.md").read_text())

    def test_partial_run_preserves_people_and_publications_not_processed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            site, previous, staging, output = self.make_tree(root, previous_count=1, current_count=1)
            people = json.loads((site / "data" / "pessoal" / "professores.json").read_text())["professores"]
            people.append({
                "id": "outra-pessoa", "nome": "Outra Pessoa", "ativo": True,
                "scopus_author_ids": ["67890"],
            })
            write_json(site / "data" / "pessoal" / "professores.json", {"professores": people})
            previous_authors = json.loads((previous / "autores.json").read_text())
            previous_authors["autores"]["outra-pessoa"] = {
                "metrics": MODULE.author_metrics([], "2026-08-01"),
                "publicacoes": [],
                "metadata": {"source": "scopus", "updated_at": "2026-08-01T00:00:00Z"},
            }
            write_json(previous / "autores.json", previous_authors)
            self.assertEqual(self.run_main(root, site, previous, staging, output, full=False), 0)
            output_authors = json.loads((output / "autores.json").read_text())["autores"]
            self.assertIn("outra-pessoa", output_authors)

    def test_complete_run_rejects_missing_curated_person(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            site, previous, staging, output = self.make_tree(root, previous_count=1, current_count=1)
            people = json.loads((site / "data" / "pessoal" / "professores.json").read_text())["professores"]
            people.append({
                "id": "ausente", "nome": "Ausente", "ativo": True,
                "scopus_author_ids": ["99999"],
            })
            write_json(site / "data" / "pessoal" / "professores.json", {"professores": people})
            self.assertEqual(self.run_main(root, site, previous, staging, output), 1)

    def test_report_counts_omitted_items_per_category(self) -> None:
        before: dict[str, dict] = {}
        after = {str(index): {"value": index} for index in range(150)}
        report = MODULE.render_report({}, {}, before, after, {}, True)
        self.assertIn("… e mais 50 itens", report)

    def test_complete_run_deduplicates_same_doi_and_remaps_author_reference(self) -> None:
        first = MODULE.normalize_entry(
            entry(20, citations=3, doi="https://doi.org/10.1234/DUPLICATE"),
            "professor", "Pessoa", {"12345"}, "2026-08-14T00:00:00Z",
        )
        second = MODULE.normalize_entry(
            entry(10, citations=8, doi="10.1234/duplicate."),
            "professor", "Pessoa", {"12345"}, "2026-08-14T00:00:00Z",
        )
        publications, aliases = MODULE.deduplicate_publications({"20": first, "10": second})
        self.assertEqual(set(publications), {"10"})
        self.assertEqual(publications["10"]["scopus"]["citations"], 8)
        authors = {"professor": {"publicacoes": [
            {"publication_id": "2-s2.0-20", "author_position": 2, "is_corresponding_author": False},
            {"publication_id": "2-s2.0-10", "author_position": 1, "is_corresponding_author": True},
        ]}}
        MODULE.remap_author_references(authors, publications, aliases)
        self.assertEqual(authors["professor"]["publicacoes"], [{
            "publication_id": "2-s2.0-10",
            "author_position": 1,
            "is_corresponding_author": True,
        }])

    def test_title_rule_applies_only_when_doi_is_absent(self) -> None:
        common = {
            "year": "2026",
            "title": "Título: com pontuação!",
            "journal": {"name": "Revista Árvore"},
            "eid": "2-s2.0-1",
            "doi": None,
        }
        same = {**copy.deepcopy(common), "eid": "2-s2.0-2", "title": "titulo com pontuacao"}
        different_doi = {**copy.deepcopy(common), "eid": "2-s2.0-3", "doi": "10.1/distinct"}
        self.assertEqual(MODULE.duplicate_key(common), MODULE.duplicate_key(same))
        self.assertNotEqual(MODULE.duplicate_key(common), MODULE.duplicate_key(different_doi))


if __name__ == "__main__":
    unittest.main()

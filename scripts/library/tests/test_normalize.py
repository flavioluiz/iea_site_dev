from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "normalize.py"
SPEC = importlib.util.spec_from_file_location("library_normalize", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


class LibraryNormalizeTests(unittest.TestCase):
    def test_tg_course_and_curso_are_semantically_equal(self) -> None:
        common = {
            "num_tg": "7",
            "title": "Título",
            "author": "Pessoa",
            "year": "2026",
            "advisors": ["Docente"],
        }
        self.assertEqual(
            MODULE.comparable({**common, "course": "Engenharia Aeronáutica"}, "tgs"),
            MODULE.comparable({**common, "curso": "Engenharia Aeronáutica"}, "tgs"),
        )

    def test_drop_above_five_percent_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            previous = Path(temporary)
            write_json(
                previous / "manifest.json",
                {"counts": {"teses_dissertacoes": 100, "trabalhos_graduacao": 100}},
            )
            with self.assertRaisesRegex(ValueError, "acima de 5%"):
                MODULE.validate_thresholds(previous, 94, 100)
            MODULE.validate_thresholds(previous, 95, 95)

    def test_no_change_reuses_public_contract_without_publishing_raw_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            previous = root / "previous"
            output = root / "candidate"
            input_dir = root / "input"
            input_dir.mkdir()
            write_json(
                previous / "manifest.json",
                {
                    "counts": {"teses_dissertacoes": 1, "trabalhos_graduacao": 1},
                    "records": 2,
                },
            )
            write_json(previous / "catalogo.json", {"schema_version": 1, "records": []})
            write_json(
                previous / "teses" / "by_id" / "1.json",
                {
                    "num_tese": "1",
                    "title": "Tese",
                    "author": "Pessoa",
                    "year": "2025",
                    "course": "Doutorado",
                    "advisors": [{"name": "Docente", "professor_slug": "docente"}],
                    "co_advisors": [],
                },
            )
            write_json(
                previous / "tgs" / "by_id" / "2.json",
                {
                    "num_tg": "2",
                    "title": "TG",
                    "author": "Pessoa",
                    "year": "2026",
                    "curso": "Engenharia Aeronáutica",
                    "advisors": [{"name": "Docente", "professor_slug": "docente"}],
                    "co_advisors": [],
                },
            )
            output.mkdir()
            (output / "stale.txt").write_text("stale", encoding="utf-8")
            argv = [
                "normalize.py",
                "--input", str(input_dir),
                "--output", str(output),
                "--previous", str(previous),
                "--report", str(root / "report.md"),
            ]
            with patch.object(sys, "argv", argv):
                self.assertEqual(MODULE.main(), 0)
            self.assertFalse((output / "stale.txt").exists())
            self.assertFalse(list(output.glob("*_raw.json")))
            self.assertTrue((output / "catalogo.json").is_file())

    def test_routine_update_adds_new_entries_without_rewriting_existing_records(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            previous = root / "previous"
            output = root / "candidate"
            input_dir = root / "input"
            input_dir.mkdir()
            write_json(previous / "manifest.json", {
                "counts": {
                    "teses_dissertacoes": 1, "trabalhos_graduacao": 1,
                    "teses_dissertacoes_iea": 0, "trabalhos_graduacao_iea": 0,
                },
                "records": 2,
            })
            old_thesis = {
                "num_tese": "1", "type": "tese", "title": "Grafia antiga",
                "author": "Pessoa", "year": "2025", "course": "Doutorado",
                "advisors": [{"name": "Docente externo", "professor_slug": None}],
                "co_advisors": [],
            }
            old_tg = {
                "num_tg": "2", "type": "tg", "title": "TG preservado",
                "author": "Pessoa", "year": "2025", "curso": "Engenharia Aeronáutica",
                "advisors": [{"name": "Docente externo", "professor_slug": None}],
                "co_advisors": [],
            }
            write_json(previous / "teses" / "by_id" / "1.json", old_thesis)
            write_json(previous / "tgs" / "by_id" / "2.json", old_tg)
            write_json(previous / "teses" / "lista.json", [])
            write_json(previous / "teses" / "index.json", [])
            write_json(previous / "teses" / "by_professor.json", {})
            write_json(previous / "teses" / "statistics.json", {
                "total": 0, "mestrado": 0, "doutorado": 0, "by_year": {},
                "generated_at": "2025-01-01T00:00:00Z",
            })
            write_json(previous / "tgs" / "lista.json", [{
                "id": "2", "t": "TG preservado", "a": "Pessoa", "y": "2025",
                "cu": "Engenharia Aeronáutica", "ad": ["Docente externo"], "ap": [], "iea": False,
            }])
            write_json(previous / "tgs" / "index.json", [])
            write_json(previous / "tgs" / "by_professor.json", {})
            write_json(previous / "tgs" / "statistics.json", {
                "total": 1, "by_curso": {"Engenharia Aeronáutica": 1}, "by_year": {"2025": 1},
                "generated_at": "2025-01-01T00:00:00Z",
            })
            old_thesis_bytes = (previous / "teses" / "by_id" / "1.json").read_bytes()
            old_tg_bytes = (previous / "tgs" / "by_id" / "2.json").read_bytes()
            write_json(input_dir / "teses_raw.json", {"teses": [
                {**old_thesis, "title": "Grafia corrigida", "advisors": ["Docente externo"]},
                {
                    "num_tese": "3", "title": "Tese nova", "author": "Nova pessoa", "year": "2026",
                    "course": "Mestrado Acadêmico", "advisors": ["Christopher Shneider Cerqueira"],
                    "co_advisors": [],
                },
            ]})
            write_json(input_dir / "tgs_raw.json", {"tgs": [
                {**old_tg, "title": "TG corrigido na fonte", "advisors": ["Docente externo"]},
            ]})
            report = root / "report.md"
            argv = [
                "normalize.py", "--input", str(input_dir), "--output", str(output),
                "--previous", str(previous), "--report", str(report),
            ]
            with patch.object(sys, "argv", argv):
                self.assertEqual(MODULE.main(), 0)
            self.assertEqual((output / "teses" / "by_id" / "1.json").read_bytes(), old_thesis_bytes)
            self.assertEqual((output / "tgs" / "by_id" / "2.json").read_bytes(), old_tg_bytes)
            self.assertEqual(MODULE.load(output / "teses" / "by_id" / "3.json")["title"], "Tese nova")
            self.assertEqual(MODULE.load(output / "manifest.json")["counts"]["teses_dissertacoes"], 2)
            self.assertEqual(MODULE.load(output / "manifest.json")["counts"]["teses_dissertacoes_iea"], 1)
            self.assertIn("Teses/dissertações: +1 / ~1 / -0", report.read_text(encoding="utf-8"))
            self.assertIn("Alterações de metadados existentes preservadas para revisão separada: 2", report.read_text(encoding="utf-8"))

    def test_refuses_to_write_over_last_good_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            argv = [
                "normalize.py",
                "--input", str(root / "input"),
                "--output", str(root / "published"),
                "--previous", str(root / "published"),
                "--report", str(root / "report.md"),
            ]
            with patch.object(sys, "argv", argv):
                self.assertEqual(MODULE.main(), 2)


if __name__ == "__main__":
    unittest.main()

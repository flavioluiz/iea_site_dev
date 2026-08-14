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

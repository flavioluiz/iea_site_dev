from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "fetch.py"
SPEC = importlib.util.spec_from_file_location("scopus_fetch", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def site_tree(root: Path) -> Path:
    site = root / "site"
    path = site / "data" / "pessoal" / "professores.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"professores": [{
        "id": "professor",
        "nome": "Pessoa",
        "ativo": True,
        "scopus_author_ids": ["12345"],
    }]}), encoding="utf-8")
    return site


class ScopusFetchTests(unittest.TestCase):
    def run_main(self, argv: list[str]) -> int:
        with patch.object(sys, "argv", ["fetch.py", *argv]):
            return MODULE.main()

    def test_dry_run_selects_curated_ids_without_network_or_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            site = site_tree(root)
            output = root / "raw"
            with patch.object(MODULE, "client", side_effect=AssertionError("network called")):
                code = self.run_main([
                    "--site-root", str(site), "--output", str(output), "--dry-run",
                    "--professor", "professor",
                ])
            self.assertEqual(code, 0)
            self.assertFalse(output.exists())

    def test_resume_reuses_complete_staging_unless_force_is_set(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            site = site_tree(root)
            output = root / "raw"
            output.mkdir()
            staged = output / "professor.json"
            staged.write_text('{"existing": true}', encoding="utf-8")
            with (
                patch.object(MODULE, "client", return_value=object()),
                patch.object(MODULE, "fetch_author", side_effect=AssertionError("author fetched")),
                patch.object(MODULE, "fetch_publications", side_effect=AssertionError("publications fetched")),
            ):
                code = self.run_main([
                    "--site-root", str(site), "--output", str(output), "--resume",
                ])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(staged.read_text()), {"existing": True})

    def test_force_overwrites_resumable_staging(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            site = site_tree(root)
            output = root / "raw"
            output.mkdir()
            staged = output / "professor.json"
            staged.write_text('{"existing": true}', encoding="utf-8")
            with (
                patch.object(MODULE, "client", return_value=object()),
                patch.object(MODULE, "fetch_author", return_value={"author-retrieval-response": []}),
                patch.object(MODULE, "fetch_publications", return_value=[]),
            ):
                code = self.run_main([
                    "--site-root", str(site), "--output", str(output), "--resume", "--force",
                ])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(staged.read_text())["professor_id"], "professor")

    def test_unknown_professor_fails_before_network(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            site = site_tree(root)
            with patch.object(MODULE, "client", side_effect=AssertionError("network called")):
                code = self.run_main([
                    "--site-root", str(site), "--output", str(root / "raw"),
                    "--professor", "inexistente",
                ])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()

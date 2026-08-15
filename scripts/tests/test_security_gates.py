from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image


SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SECURITY = load_module("security_check_test", SCRIPTS / "security_check.py")
LINKS = load_module("check_links_test", SCRIPTS / "check_links.py")


class SecurityGateTests(unittest.TestCase):
    def test_decap_update_workflow_never_executes_pull_request_code(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "update-decap-proposals.yml").read_text(encoding="utf-8")
        self.assertIn("pull_request_target:", workflow)
        self.assertNotIn("actions/checkout", workflow)
        self.assertIn('startswith("cms/")', workflow)
        self.assertIn('decap-cms/pending_publish', workflow)
        self.assertIn('pulls/${number}/update-branch', workflow)

    def test_html_disguised_as_jpg_is_rejected_by_content_signature(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "static" / "images" / "pessoal"
            folder.mkdir(parents=True)
            (folder / "foto.jpg").write_bytes(b"<html><script>alert(1)</script></html>")
            problems: list[str] = []
            with patch.object(SECURITY, "ROOT", root):
                SECURITY.scan_images(problems)
            self.assertTrue(any("foto inválida" in problem for problem in problems), problems)

    def test_valid_small_jpeg_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "static" / "images" / "pessoal"
            folder.mkdir(parents=True)
            Image.new("RGB", (120, 120), "white").save(folder / "foto.jpg", format="JPEG")
            problems: list[str] = []
            with patch.object(SECURITY, "ROOT", root):
                SECURITY.scan_images(problems)
            self.assertEqual(problems, [])

    def test_script_in_markdown_and_handler_in_json_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "content").mkdir()
            (root / "data").mkdir()
            (root / "content" / "pagina.md").write_text("<ScRiPt>alert(1)</sCrIpT>", encoding="utf-8")
            (root / "data" / "registro.json").write_text(
                '{"titulo": "<img src=x onerror=alert(1)>"}', encoding="utf-8"
            )
            problems: list[str] = []
            with patch.object(SECURITY, "ROOT", root):
                SECURITY.scan_editorial_content(problems)
            self.assertTrue(any("tag script" in problem for problem in problems), problems)
            self.assertTrue(any("handler HTML" in problem for problem in problems), problems)

    def test_pdf_extension_with_non_pdf_content_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "static" / "documents"
            folder.mkdir(parents=True)
            (folder / "horario.pdf").write_bytes(b"<html>not a pdf</html>")
            problems: list[str] = []
            with patch.object(SECURITY, "ROOT", root):
                SECURITY.scan_documents(problems)
            self.assertTrue(any("assinatura PDF ausente" in problem for problem in problems), problems)

    def test_blank_target_requires_both_rel_defenses(self) -> None:
        unsafe = LINKS.References()
        unsafe.feed('<a href="https://example.org" target="_blank" rel="noopener">x</a>')
        self.assertEqual(unsafe.unsafe_blank_links, ["https://example.org"])
        safe = LINKS.References()
        safe.feed('<a href="https://example.org" target="_blank" rel="noreferrer noopener">x</a>')
        self.assertEqual(safe.unsafe_blank_links, [])


if __name__ == "__main__":
    unittest.main()

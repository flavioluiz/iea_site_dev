from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class CmsRenderContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = (ROOT / "static/admin/config.yml").read_text(encoding="utf-8")

    def test_every_editable_markdown_page_renders_title_and_body(self) -> None:
        pages_block = self.config.split("  - name: paginas", 1)[1].split(
            "  - name: pessoal", 1
        )[0]
        content_files = re.findall(r"^\s+file: (content/\S+)$", pages_block, re.MULTILINE)
        self.assertEqual(20, len(content_files))

        for filename in content_files:
            content_path = Path(filename)
            section = content_path.parent.name
            if content_path.parent == Path("content"):
                template_path = ROOT / "layouts/index.html"
            else:
                custom = ROOT / "layouts" / section / "list.html"
                template_path = custom if custom.exists() else ROOT / "layouts/_default/list.html"

            template = template_path.read_text(encoding="utf-8")
            with self.subTest(entry=filename, template=str(template_path.relative_to(ROOT))):
                self.assertIn(".Title", template)
                self.assertIn(".Content", template)

    def test_page_descriptions_are_used_as_metadata(self) -> None:
        head = (ROOT / "layouts/partials/head.html").read_text(encoding="utf-8")
        self.assertIn(".Description", head)

    def test_editor_never_merges_content_directly(self) -> None:
        collection_blocks = re.findall(
            r"^  - name: (\S+)\n(.*?)(?=^  - name: |\Z)",
            self.config,
            re.MULTILINE | re.DOTALL,
        )
        self.assertEqual(5, len(collection_blocks))
        for name, block in collection_blocks:
            with self.subTest(collection=name):
                self.assertRegex(block, r"(?m)^    publish: false$")

    def test_laboratories_are_not_selected_by_a_manual_allowlist(self) -> None:
        template = (ROOT / "layouts/laboratorios/list.html").read_text(encoding="utf-8")
        self.assertNotIn("$featured", template)
        self.assertIn("range $lab := $labs", template)
        self.assertIn('data-lab-id="{{ $lab.id }}"', template)

    def test_derived_fields_are_not_manual_editor_inputs(self) -> None:
        departments = (ROOT / "layouts/departamentos/list.html").read_text(encoding="utf-8")
        projects = (ROOT / "layouts/projetos/list.html").read_text(encoding="utf-8")

        self.assertIn('where $laboratorios "departamento" $dept.id', departments)
        self.assertNotIn("$dept.laboratorios", departments)
        self.assertNotIn('label: "Ícone técnico"', self.config)
        self.assertNotIn('label: "IDs dos laboratórios"', self.config)
        self.assertNotIn(".Site.Data.areas", projects)
        self.assertIn("$departamentos := .Site.Data.departamentos.departamentos", projects)


if __name__ == "__main__":
    unittest.main()

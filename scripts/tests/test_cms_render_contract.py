from __future__ import annotations

import json
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


class CmsRenderContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = (ROOT / "static/admin/config.yml").read_text(encoding="utf-8")
        cls.collections = {
            item["name"]: item
            for item in yaml.safe_load(cls.config)["collections"]
        }

    def test_site_map_owns_generic_pages_and_navigation(self) -> None:
        site_map = self.collections["paginas"]
        self.assertEqual("data/paginas", site_map["folder"])
        self.assertTrue(site_map["create"])
        self.assertTrue(site_map["delete"])
        parent_field = next(field for field in site_map["fields"] if field["name"] == "parent")
        self.assertEqual("paginas", parent_field["collection"])

        nodes = [json.loads(path.read_text(encoding="utf-8")) for path in (ROOT / "data/paginas").glob("*.json")]
        by_id = {node["id"]: node for node in nodes}
        self.assertGreaterEqual(len(nodes), 30)
        self.assertEqual("pagina_editavel", by_id["sobre"]["tipo"])
        self.assertEqual("divisao", by_id["sobre"]["parent"])
        self.assertEqual("pagina_editavel", by_id["contato"]["tipo"])

        for language in ("pt", "en"):
            adapter = (ROOT / f"content/_content.{language}.gotmpl").read_text(encoding="utf-8")
            self.assertIn('eq .tipo "pagina_editavel"', adapter)
            self.assertIn(f".pagina.conteudo.{language}", adapter)
            self.assertIn("$.AddPage", adapter)

        nav = (ROOT / "layouts/partials/nav.html").read_text(encoding="utf-8")
        self.assertIn(".Site.Data.paginas", nav)
        self.assertNotIn(".Site.Menus.main", nav)
        self.assertIn('where $nodes "parent" "root"', nav)

        map_output = (ROOT / "layouts/index.mapasite.json").read_text(encoding="utf-8")
        hugo_config = (ROOT / "config/_default/config.yaml").read_text(encoding="utf-8")
        self.assertIn('dict "version" 1 "nodes" $nodes', map_output)
        self.assertIn('home: ["HTML", "RSS", "JSON", "MAPASITE"]', hugo_config)

    def test_every_structural_markdown_page_renders_title_and_body(self) -> None:
        content_files = [entry["file"] for entry in self.collections["paginas_estruturais"]["files"]]
        self.assertEqual(16, len(content_files))

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

    def test_external_editors_review_and_maintainers_may_publish(self) -> None:
        self.assertIn("open_authoring: true", self.config)
        self.assertIn("publish_mode: editorial_workflow", self.config)
        self.assertNotIn("publish: false", self.config)

    def test_people_are_individual_filterable_entries(self) -> None:
        people_block = self.config.split("  - name: pessoal", 1)[1].split(
            "  - name: laboratorios", 1
        )[0]
        self.assertIn("folder: data/pessoal/professores", people_block)
        self.assertIn('label: "Somente pessoas ativas"', people_block)
        self.assertIn('{ label: "Departamento", field: departamento }', people_block)
        self.assertIn('{ label: "Categoria", field: categoria }', people_block)
        self.assertIn("public_folder: images/pessoal", people_block)
        self.assertNotIn("file: data/pessoal/professores.json", people_block)

        people = sorted((ROOT / "data/pessoal/professores").glob("*.json"))
        self.assertEqual(90, len(people))

    def test_laboratories_are_individual_filterable_entries(self) -> None:
        laboratories = self.collections["laboratorios"]
        self.assertEqual("data/laboratorios", laboratories["folder"])
        self.assertTrue(laboratories["create"])
        self.assertIn("departamento", [group["field"] for group in laboratories["view_groups"]])
        self.assertIn("tema", [group["field"] for group in laboratories["view_groups"]])
        self.assertNotIn("data/laboratorios.json", self.config)

        laboratory_files = sorted((ROOT / "data/laboratorios").glob("*.json"))
        self.assertEqual(19, len(laboratory_files))
        for path in laboratory_files:
            self.assertEqual(path.stem, json.loads(path.read_text(encoding="utf-8"))["id"])

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

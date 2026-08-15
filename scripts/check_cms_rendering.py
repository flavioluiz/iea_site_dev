#!/usr/bin/env python3
"""Check that structured CMS records are present in Hugo's generated HTML."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from people_data import load_professors
from laboratory_data import load_laboratories


ROOT = Path(__file__).resolve().parents[1]


def load_records(filename: str, key: str) -> list[dict]:
    payload = json.loads((ROOT / "data" / filename).read_text(encoding="utf-8"))
    return payload[key]


def assert_markers(html_path: Path, attribute: str, expected: list[str]) -> int:
    if not html_path.exists():
        raise SystemExit(f"HTML esperado não foi gerado: {html_path}")

    html = html_path.read_text(encoding="utf-8")
    missing = [
        value
        for value in expected
        if f'{attribute}="{value}"' not in html and f"{attribute}={value}" not in html
    ]
    if missing:
        sample = ", ".join(missing[:10])
        raise SystemExit(
            f"{html_path}: {len(missing)} registro(s) do CMS não aparecem no HTML "
            f"({attribute}): {sample}"
        )
    return len(expected)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public", type=Path, default=ROOT / "public")
    args = parser.parse_args()
    public = args.public.resolve()

    departments = [item["id"] for item in load_records("departamentos.json", "departamentos")]
    laboratories = [item["id"] for item in load_laboratories(ROOT)]
    lines = [item["id"] for item in load_records("linhas_pesquisa.json", "linhas")]
    people = [
        item["id"]
        for item in load_professors(ROOT)
        if item["ativo"]
    ]
    projects = [
        item["id"]
        for item in load_records("projetos.json", "projetos")
        if item["status"] == "em_andamento"
    ]
    document_categories = [item["id"] for item in load_records("documentos.json", "categorias")]
    site_nodes = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((ROOT / "data" / "paginas").glob("*.json"))
    ]

    checked = 0
    for lang in ("pt", "en"):
        map_path = public / lang / "mapa-site.json"
        if not map_path.is_file():
            raise SystemExit(f"Mapa visual não foi gerado: {map_path}")
        map_payload = json.loads(map_path.read_text(encoding="utf-8"))
        if map_payload.get("version") != 2:
            raise SystemExit(f"{map_path}: versão inesperada do mapa visual")
        map_ids = {node["id"] for node in map_payload["nodes"]}
        expected_map_ids = {node["id"] for node in site_nodes}
        if map_ids != expected_map_ids:
            raise SystemExit(f"{map_path}: itens diferentes da fonte editorial")
        for node in map_payload["nodes"]:
            if node["tipo"] not in {"pagina_editavel", "pagina_estrutural"}:
                continue
            editor = node.get("edicao", {})
            if node["tipo"] == "pagina_editavel" and not editor:
                continue
            if not editor.get("origem") or not all(editor.get("editor", {}).get(code) for code in ("pt", "en")):
                raise SystemExit(f"{map_path}: página {node['id']} sem origem/editor no mapa")
        checked += len(map_ids)

        home = public / lang / "index.html"
        checked += assert_markers(home, "data-cms-content", ["page-body"])
        menu_items = [
            node["id"]
            for node in site_nodes
            if node["parent"] == "root" and node["visivel"][lang]
        ]
        checked += assert_markers(home, "data-site-page-id", menu_items)
        checked += assert_markers(
            public / lang / "departamentos/index.html", "data-department-id", departments
        )
        checked += assert_markers(
            public / lang / "laboratorios/index.html", "data-lab-id", laboratories
        )
        checked += assert_markers(
            public / lang / "linhas/index.html", "data-research-line-id", lines
        )
        checked += assert_markers(
            public / lang / "pessoal/index.html", "data-person-id", people
        )
        checked += assert_markers(
            public / lang / "projetos/index.html", "data-project-id", projects
        )
        checked += assert_markers(
            public / lang / "documentos/index.html",
            "id",
            [f"document-category-{item}" for item in document_categories],
        )
        for node in site_nodes:
            if node["tipo"] != "pagina_editavel" or not node["pagina"]["publicada"]:
                continue
            page = public / lang / node["pagina"]["slug"] / "index.html"
            if not page.is_file():
                raise SystemExit(f"Página do Mapa do site não foi gerada: {page}")
            html = page.read_text(encoding="utf-8")
            if node["pagina"]["titulo"][lang] not in html:
                raise SystemExit(f"{page}: título do Mapa do site não aparece no HTML")
            checked += 1

    print(f"CMS → HTML: {checked} marcadores conferidos em português e inglês.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

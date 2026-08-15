#!/usr/bin/env python3
"""Check that structured CMS records are present in Hugo's generated HTML."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


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
    laboratories = [item["id"] for item in load_records("laboratorios.json", "laboratorios")]
    lines = [item["id"] for item in load_records("linhas_pesquisa.json", "linhas")]
    people = [
        item["id"]
        for item in load_records("pessoal/professores.json", "professores")
        if item["ativo"]
    ]
    projects = [
        item["id"]
        for item in load_records("projetos.json", "projetos")
        if item["status"] == "em_andamento"
    ]
    document_categories = [item["id"] for item in load_records("documentos.json", "categorias")]

    checked = 0
    for lang in ("pt", "en"):
        home = public / lang / "index.html"
        checked += assert_markers(home, "data-cms-content", ["page-body"])
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

    print(f"CMS → HTML: {checked} marcadores conferidos em português e inglês.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

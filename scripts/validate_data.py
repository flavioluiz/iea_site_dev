#!/usr/bin/env python3
"""Validate editorial data, cross-references, uploads, and bulk changes."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from PIL import Image, UnidentifiedImageError

from people_data import load_professors, load_professors_at_ref
from laboratory_data import load_laboratories, load_laboratories_at_ref


ROOT = Path(__file__).resolve().parents[1]
SAFE_SCHEMES = {"http", "https", "mailto"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_IMAGE_BYTES = 2 * 1024 * 1024
MIN_IMAGE_DIMENSION = 80
MAX_IMAGE_DIMENSION = 4096
MAX_DOCUMENT_BYTES = 10 * 1024 * 1024
EDITORIAL_SCHEMAS = {
    "data/departamentos.json": "schemas/departamentos.schema.json",
    "data/projetos.json": "schemas/projetos.schema.json",
    "data/linhas_pesquisa.json": "schemas/linhas-pesquisa.schema.json",
    "data/documentos.json": "schemas/documentos.schema.json",
}
PROTECTED_SITE_NODE_TYPES = {
    "root": "raiz",
    "home": "pagina_estrutural",
    "divisao": "grupo",
    "departamentos": "pagina_estrutural",
    "pessoal": "pagina_estrutural",
    "pesquisa": "grupo",
    "linhas": "pagina_estrutural",
    "projetos": "pagina_estrutural",
    "publicacoes": "pagina_estrutural",
    "espaco": "pagina_estrutural",
    "laboratorios": "pagina_estrutural",
    "graduacao": "grupo",
    "cursos-grad": "pagina_estrutural",
    "disciplinas": "pagina_estrutural",
    "tgs": "pagina_estrutural",
    "posgraduacao": "grupo",
    "pg-cursos": "pagina_estrutural",
    "teses": "pagina_estrutural",
    "documentos": "pagina_estrutural",
    "pg-cat-stricto": "categoria",
    "pgeam": "link_externo",
    "pgcte": "link_externo",
    "pg-sep-1": "separador",
    "pg-cat-profissional": "categoria",
    "mppee": "link_externo",
    "pg-sep-2": "separador",
    "pg-cat-lato": "categoria",
    "safety": "link_externo",
    "cassa": "pagina_estrutural",
    "ceeaa": "pagina_estrutural",
}
PAGE_EDITOR_ORIGINS = {
    "markdown",
    "markdown_lista",
    "markdown_secao",
    "dados_markdown",
    "template_markdown",
    "importada",
}


class Problems:
    def __init__(self) -> None:
        self.items: list[str] = []

    def add(self, message: str) -> None:
        self.items.append(message)

    def extend(self, messages: Iterable[str]) -> None:
        self.items.extend(messages)

    def finish(self) -> int:
        if self.items:
            print("Validation failed:", file=sys.stderr)
            for item in self.items:
                print(f"- {item}", file=sys.stderr)
            return 1
        print("Data validation passed.")
        return 0


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def parse_all_data(problems: Problems) -> None:
    paths = sorted((ROOT / "data").rglob("*.json")) + sorted((ROOT / "data").rglob("*.yaml"))
    paths += sorted((ROOT / "config").rglob("*.yaml"))
    for path in paths:
        try:
            load_json(path) if path.suffix == ".json" else load_yaml(path)
        except Exception as exc:  # noqa: BLE001 - report parser context uniformly
            problems.add(f"{path.relative_to(ROOT)}: arquivo inválido ({exc})")


def validate_editorial_schemas(problems: Problems) -> None:
    for data_path, schema_path in EDITORIAL_SCHEMAS.items():
        problems.extend(schema_errors(ROOT / data_path, ROOT / schema_path))


def validate_site_map(problems: Problems) -> None:
    folder = ROOT / "data" / "paginas"
    schema = load_json(ROOT / "schemas" / "pagina-site.schema.json")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    by_id: dict[str, dict[str, Any]] = {}
    slugs: dict[str, str] = {}

    for path in sorted(folder.glob("*.json")):
        node = load_json(path)
        for error in sorted(validator.iter_errors(node), key=lambda item: list(item.absolute_path)):
            location = "/".join(str(part) for part in error.absolute_path) or "<raiz>"
            problems.add(f"{path.relative_to(ROOT)}:{location}: {error.message}")
        node_id = node.get("id")
        if not isinstance(node_id, str):
            continue
        if path.name != f"{node_id}.json":
            problems.add(f"{path.relative_to(ROOT)}: o arquivo deve se chamar {node_id}.json")
        if node_id in by_id:
            problems.add(f"Mapa do site: ID duplicado: {node_id}")
        by_id[node_id] = node

        if node.get("tipo") == "pagina_editavel":
            slug = node.get("pagina", {}).get("slug")
            if isinstance(slug, str) and slug:
                if slug in slugs:
                    problems.add(
                        f"Mapa do site: endereço /{slug}/ usado por {slugs[slug]} e {node_id}"
                    )
                slugs[slug] = node_id

    for node_id, expected_type in PROTECTED_SITE_NODE_TYPES.items():
        node = by_id.get(node_id)
        if node is None:
            problems.add(f"Mapa do site: item protegido ausente: {node_id}")
            continue
        if node.get("protegido") is not True:
            problems.add(f"Mapa do site: {node_id} deve permanecer protegido")
        if node.get("tipo") != expected_type:
            problems.add(
                f"Mapa do site: {node_id} deve manter o tipo {expected_type}"
            )

    editor_map = load_yaml(ROOT / "data" / "admin" / "paginas_edicao.yaml")
    if not isinstance(editor_map, dict):
        problems.add("Mapa do site: classificação editorial deve ser um objeto")
        editor_map = {}
    page_node_types = {"pagina_editavel", "pagina_estrutural"}
    for node_id, node in by_id.items():
        if node.get("tipo") not in page_node_types:
            continue
        editor = editor_map.get(node_id)
        if not isinstance(editor, dict):
            problems.add(f"Mapa do site: página {node_id} não possui origem editorial")
            continue
        if editor.get("origem") not in PAGE_EDITOR_ORIGINS:
            problems.add(f"Mapa do site: origem editorial inválida em {node_id}")
        routes = editor.get("editor")
        if not isinstance(routes, dict) or any(
            not isinstance(routes.get(language), str) or not routes[language].startswith("#/edit/")
            for language in ("pt", "en")
        ):
            problems.add(f"Mapa do site: {node_id} deve ter editor PT e EN")
    for node_id, editor in editor_map.items():
        if node_id not in by_id:
            problems.add(f"Mapa do site: classificação editorial aponta para item ausente: {node_id}")
        if isinstance(editor, dict):
            data_route = editor.get("dados_editor")
            if data_route and not re.match(r"^#/(?:edit|collections)/[a-z0-9_/-]+$", data_route):
                problems.add(f"Mapa do site: editor de dados inválido em {node_id}")

    root = by_id.get("root")
    if root and (root.get("parent") != "" or any(root.get("visivel", {}).values())):
        problems.add("Mapa do site: a raiz técnica não pode aparecer no menu nem ter pai")

    for node_id, node in by_id.items():
        node_type = node.get("tipo")
        parent_id = node.get("parent")
        if node_type != "raiz":
            parent = by_id.get(parent_id)
            if parent is None:
                problems.add(f"Mapa do site: {node_id} aponta para seção inexistente: {parent_id}")
            elif parent.get("tipo") not in {"raiz", "grupo"}:
                problems.add(
                    f"Mapa do site: {node_id} só pode ficar no menu principal ou dentro de um grupo"
                )

        visibility = node.get("visivel", {})
        labels = node.get("rotulo", {})
        urls = node.get("url", {})
        for language in ("pt", "en"):
            label = labels.get(language, "")
            url = urls.get(language, "")
            if visibility.get(language) and node_type != "separador" and not label.strip():
                problems.add(f"Mapa do site: {node_id} está visível em {language} sem nome")
            if node_type in {"pagina_estrutural", "grupo"} and url != "#" and not url.startswith("/"):
                problems.add(
                    f"Mapa do site: destino {language} de {node_id} deve começar com / ou ser #"
                )
            if node_type == "link_externo" and urlparse(url).scheme not in {"http", "https"}:
                problems.add(f"Mapa do site: link externo {language} inválido em {node_id}")
            if node_type == "pagina_editavel" and url:
                problems.add(
                    f"Mapa do site: {node_id} é editável; seu endereço vem do campo slug, não de url"
                )
            if node_type in {"categoria", "separador"} and url not in {"", "#"}:
                problems.add(f"Mapa do site: {node_id} é visual e não pode apontar para uma página")

        seen: set[str] = set()
        cursor = node
        while cursor.get("tipo") != "raiz":
            cursor_id = cursor.get("id")
            if cursor_id in seen:
                problems.add(f"Mapa do site: ciclo de seções envolvendo {node_id}")
                break
            seen.add(cursor_id)
            next_node = by_id.get(cursor.get("parent"))
            if next_node is None:
                break
            cursor = next_node


def schema_errors(data_path: Path, schema_path: Path) -> list[str]:
    schema = load_json(schema_path)
    data = load_json(data_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = []
    for error in sorted(validator.iter_errors(data), key=lambda item: list(item.absolute_path)):
        location = "/".join(str(part) for part in error.absolute_path) or "<raiz>"
        errors.append(f"{data_path.relative_to(ROOT)}:{location}: {error.message}")
    return errors


def iter_strings(value: Any, path: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from iter_strings(child, f"{path}/{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_strings(child, f"{path}/{index}")


def valid_orcid(value: str) -> bool:
    match = re.search(r"(?:orcid\.org/)?(\d{4}-\d{4}-\d{4}-\d{3}[\dX])$", value, re.IGNORECASE)
    if not match:
        return False
    compact = match.group(1).replace("-", "").upper()
    total = 0
    for character in compact[:15]:
        total = (total + int(character)) * 2
    remainder = (12 - (total % 11)) % 11
    expected = "X" if remainder == 10 else str(remainder)
    return compact[-1] == expected


def validate_professors(problems: Problems) -> tuple[dict[str, dict[str, Any]], set[str]]:
    canonical_dir = ROOT / "data" / "pessoal" / "professores"
    professors = load_professors(ROOT)
    schema = load_json(ROOT / "schemas" / "professores.schema.json")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    wrapped = {"schema_version": 1, "professores": professors}
    for error in sorted(validator.iter_errors(wrapped), key=lambda item: list(item.absolute_path)):
        location = "/".join(str(part) for part in error.absolute_path) or "<raiz>"
        problems.add(f"data/pessoal/professores/:{location}: {error.message}")
    by_id: dict[str, dict[str, Any]] = {}
    scopus_owners: dict[str, str] = {}
    department_records = load_json(ROOT / "data" / "departamentos.json")["departamentos"]
    departments = {item["id"] for item in department_records}

    for index, professor in enumerate(professors):
        professor_id = professor.get("id", f"<índice-{index}>")
        expected_path = canonical_dir / f"{professor_id}.json"
        if not expected_path.is_file():
            problems.add(f"{professor_id}: o nome do arquivo deve ser {professor_id}.json")
        if professor_id in by_id:
            problems.add(f"ID de pessoa duplicado: {professor_id}")
        by_id[professor_id] = professor
        if professor.get("ativo") and professor.get("departamento") not in departments:
            problems.add(f"{professor_id}: pessoa ativa sem departamento válido")
        if professor.get("ativo") and not professor.get("categoria"):
            problems.add(f"{professor_id}: pessoa ativa sem categoria")

        for scopus_id in professor.get("scopus_author_ids", []):
            previous = scopus_owners.get(scopus_id)
            if previous and previous != professor_id:
                problems.add(f"Scopus Author ID {scopus_id} usado por {previous} e {professor_id}")
            scopus_owners[scopus_id] = professor_id

        orcid = professor.get("links", {}).get("orcid", "")
        if orcid and not valid_orcid(orcid):
            problems.add(f"{professor_id}: ORCID inválido ({orcid})")

        for location, value in iter_strings(professor):
            lowered = value.strip().lower()
            if lowered.startswith(("javascript:", "data:", "vbscript:")):
                problems.add(f"{professor_id}{location}: protocolo de URL proibido")
            if "/links/" in location and value:
                parsed = urlparse(value)
                if parsed.scheme not in SAFE_SCHEMES:
                    problems.add(f"{professor_id}{location}: protocolo não permitido")

        photo = professor.get("foto")
        if photo:
            validate_image(ROOT / "static" / photo.lstrip("/"), professor_id, problems)

    return by_id, departments


def validate_image(path: Path, owner: str, problems: Problems) -> None:
    relative = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    if not path.is_file():
        problems.add(f"{owner}: imagem referenciada não existe: {relative}")
        return
    if path.suffix.lower() not in IMAGE_EXTENSIONS:
        problems.add(f"{relative}: extensão de imagem proibida")
    if path.stat().st_size > MAX_IMAGE_BYTES:
        problems.add(f"{relative}: imagem excede 2 MB")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", path.name):
        problems.add(f"{relative}: nome de imagem deve usar somente minúsculas ASCII, números, ponto, _ e -")
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            if image.format not in IMAGE_FORMATS:
                problems.add(f"{relative}: conteúdo real não é JPEG, PNG ou WebP")
            width, height = image.size
            if min(width, height) < MIN_IMAGE_DIMENSION:
                problems.add(f"{relative}: dimensão mínima é {MIN_IMAGE_DIMENSION}px (atual {width}x{height})")
            if max(width, height) > MAX_IMAGE_DIMENSION:
                problems.add(f"{relative}: dimensão máxima é {MAX_IMAGE_DIMENSION}px (atual {width}x{height})")
    except (UnidentifiedImageError, OSError) as exc:
        problems.add(f"{relative}: assinatura/conteúdo de imagem inválido ({exc})")


def normalized_name(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_value = decomposed.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_value.casefold().split())


def validate_document(path: Path, owner: str, problems: Problems) -> None:
    relative = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    if not path.is_file():
        problems.add(f"{owner}: documento referenciado não existe: {relative}")
        return
    if path.suffix.lower() != ".pdf":
        problems.add(f"{relative}: somente PDF é permitido nesta coleção")
    if path.stat().st_size > MAX_DOCUMENT_BYTES:
        problems.add(f"{relative}: documento excede 10 MB")
    try:
        signature = path.read_bytes()[:5]
    except OSError as exc:
        problems.add(f"{relative}: não foi possível ler o documento ({exc})")
        return
    if signature != b"%PDF-":
        problems.add(f"{relative}: conteúdo real não é PDF")


def validate_cross_references(
    professors: dict[str, dict[str, Any]], departments: set[str], problems: Problems
) -> None:
    aliases_path = ROOT / "data" / "pessoal" / "aliases_biblioteca.json"
    problems.extend(schema_errors(aliases_path, ROOT / "schemas" / "aliases-biblioteca.schema.json"))
    aliases = load_json(aliases_path)["aliases"]
    alias_names: set[str] = set()
    for alias in aliases:
        normalized = " ".join(alias["nome_fonte"].casefold().split())
        if normalized in alias_names:
            problems.add(f"Alias da biblioteca duplicado: {alias['nome_fonte']}")
        alias_names.add(normalized)
        if alias["professor_id"] not in professors:
            problems.add(f"Alias aponta para pessoa inexistente: {alias['professor_id']}")

    generated_path = ROOT / "data" / "generated" / "scopus" / "autores.json"
    problems.extend(schema_errors(generated_path, ROOT / "schemas" / "generated-scopus.schema.json"))
    generated = load_json(generated_path)["autores"]
    unknown = set(generated) - set(professors)
    if unknown:
        problems.add(f"Scopus contém IDs ausentes do cadastro: {', '.join(sorted(unknown))}")
    for professor_id, author in generated.items():
        disallowed_metadata = set(author.get("metadata", {})) - {"link_scopus", "source", "updated_at"}
        if disallowed_metadata:
            problems.add(
                f"Scopus {professor_id}: metadados não aprovados na saída pública: "
                + ", ".join(sorted(disallowed_metadata))
            )

    publications_dir = ROOT / "data" / "generated" / "scopus" / "publications" / "by_eid"
    forbidden_scopus_fields = {"abstract", "authkeywords", "email"}
    publication_schema = load_json(ROOT / "schemas" / "generated-scopus-publication.schema.json")
    publication_validator = Draft202012Validator(publication_schema, format_checker=FormatChecker())
    for publication_path in publications_dir.glob("*.json"):
        publication = load_json(publication_path)
        for error in publication_validator.iter_errors(publication):
            location = "/".join(str(part) for part in error.absolute_path) or "<raiz>"
            problems.add(f"{publication_path.relative_to(ROOT)}:{location}: {error.message}")
        present = forbidden_scopus_fields.intersection(publication)
        if present:
            problems.add(
                f"{publication_path.relative_to(ROOT)}: campos Scopus proibidos na saída pública: "
                + ", ".join(sorted(present))
            )
        if publication.get("scopus", {}).get("subject_areas"):
            problems.add(f"{publication_path.relative_to(ROOT)}: vocabulário controlado Scopus não aprovado")
        if any(author.get("affiliation") for author in publication.get("authors", [])):
            problems.add(f"{publication_path.relative_to(ROOT)}: afiliações brutas Scopus não aprovadas")

    for manifest_path in (
        ROOT / "data" / "generated" / "scopus" / "manifest.json",
        ROOT / "data" / "generated" / "biblioteca" / "manifest.json",
    ):
        problems.extend(schema_errors(manifest_path, ROOT / "schemas" / "generated-manifest.schema.json"))
    library_catalog = ROOT / "data" / "generated" / "biblioteca" / "catalogo.json"
    if library_catalog.exists():
        problems.extend(schema_errors(library_catalog, ROOT / "schemas" / "generated-biblioteca.schema.json"))

    laboratories = load_laboratories(ROOT)
    laboratory_schema = load_json(ROOT / "schemas" / "laboratorios.schema.json")
    laboratory_validator = Draft202012Validator(laboratory_schema, format_checker=FormatChecker())
    wrapped_laboratories = {"schema_version": 1, "laboratorios": laboratories}
    for error in sorted(
        laboratory_validator.iter_errors(wrapped_laboratories),
        key=lambda item: list(item.absolute_path),
    ):
        location = "/".join(str(part) for part in error.absolute_path) or "<raiz>"
        problems.add(f"data/laboratorios/:{location}: {error.message}")
    laboratory_ids: set[str] = set()
    for laboratory in laboratories:
        laboratory_id = laboratory.get("id", "<sem-id>")
        expected_path = ROOT / "data" / "laboratorios" / f"{laboratory_id}.json"
        if not expected_path.is_file():
            problems.add(f"{laboratory_id}: o nome do arquivo deve ser {laboratory_id}.json")
        if laboratory_id in laboratory_ids:
            problems.add(f"Laboratório duplicado: {laboratory_id}")
        laboratory_ids.add(laboratory_id)
        department = laboratory.get("departamento")
        if department and department not in departments:
            problems.add(f"Laboratório {laboratory_id}: departamento inexistente {department}")
        for image in laboratory.get("imagens", []):
            validate_image(ROOT / "static" / image.lstrip("/"), laboratory_id, problems)

    department_records = load_json(ROOT / "data" / "departamentos.json")["departamentos"]
    for department in department_records:
        for laboratory_id in department.get("laboratorios", []):
            if laboratory_id not in laboratory_ids:
                problems.add(f"Departamento {department['id']}: laboratório inexistente {laboratory_id}")

    for collection_path, collection_key in (
        ("data/departamentos.json", "departamentos"),
        ("data/projetos.json", "projetos"),
        ("data/linhas_pesquisa.json", "linhas"),
    ):
        identifiers: set[str] = set()
        for item in load_json(ROOT / collection_path)[collection_key]:
            identifier = item["id"]
            if identifier in identifiers:
                problems.add(f"{collection_path}: ID duplicado: {identifier}")
            identifiers.add(identifier)

    professor_names = {normalized_name(item["nome"]) for item in professors.values()}
    for project in load_json(ROOT / "data" / "projetos.json")["projetos"]:
        department = project.get("departamento")
        if department and department not in departments:
            problems.add(f"Projeto {project['id']}: departamento inexistente {department}")
        for professor_name in project.get("docentes_iea", []):
            if normalized_name(professor_name) not in professor_names:
                problems.add(
                    f"Projeto {project['id']}: pessoa IEA não encontrada no cadastro: {professor_name}"
                )

    categories = load_json(ROOT / "data" / "documentos.json")["categorias"]
    category_ids: set[str] = set()
    for category in categories:
        if category["id"] in category_ids:
            problems.add(f"Categoria de documentos duplicada: {category['id']}")
        category_ids.add(category["id"])
        for document in category["documentos"]:
            if document.get("arquivo"):
                validate_document(ROOT / "static" / document["arquivo"].lstrip("/"), category["id"], problems)


def changed_professor_ids(base_ref: str, current: dict[str, dict[str, Any]], problems: Problems) -> set[str]:
    try:
        base_records = load_professors_at_ref(ROOT, base_ref)
    except json.JSONDecodeError as exc:
        problems.add(f"cadastro base inválido em {base_ref}: {exc}")
        return set()
    if base_records is None:
        # The first canonical-data migration legitimately has no base file.
        # Treat every current record as changed so the bulk-reviewed gate still applies.
        return set(current)
    base = {item["id"]: item for item in base_records}
    return {professor_id for professor_id in set(base) | set(current) if base.get(professor_id) != current.get(professor_id)}


def enforce_bulk_review(
    base_ref: str | None,
    labels: set[str],
    professors: dict[str, dict[str, Any]],
    problems: Problems,
) -> None:
    if not base_ref:
        return
    changed = changed_professor_ids(base_ref, professors, problems)
    print(f"Professores alterados em relação a {base_ref}: {len(changed)}")
    if len(changed) > 10 and "bulk-reviewed" not in labels:
        problems.add(
            f"mudança em massa altera {len(changed)} pessoas; um mantenedor deve aplicar o label bulk-reviewed"
        )


def enforce_laboratory_bulk_review(
    base_ref: str | None,
    labels: set[str],
    current: list[dict[str, Any]],
    problems: Problems,
) -> None:
    if not base_ref:
        return
    base_records = load_laboratories_at_ref(ROOT, base_ref)
    if base_records is None:
        return
    base = {item["id"]: item for item in base_records}
    current_by_id = {item["id"]: item for item in current}
    changed = {
        item_id
        for item_id in set(base) | set(current_by_id)
        if base.get(item_id) != current_by_id.get(item_id)
    }
    print(f"Laboratórios alterados em relação a {base_ref}: {len(changed)}")
    if len(changed) > 5 and "bulk-reviewed" not in labels:
        problems.add(
            f"mudança em massa altera {len(changed)} laboratórios; "
            "um mantenedor deve aplicar o label bulk-reviewed"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ref", help="Git ref used to enforce the bulk-reviewed gate")
    parser.add_argument("--labels", default="", help="Comma-separated pull request labels")
    args = parser.parse_args()

    problems = Problems()
    parse_all_data(problems)
    validate_editorial_schemas(problems)
    validate_site_map(problems)
    professors, departments = validate_professors(problems)
    validate_cross_references(professors, departments, problems)
    labels = {label.strip() for label in args.labels.split(",") if label.strip()}
    enforce_bulk_review(args.base_ref, labels, professors, problems)
    enforce_laboratory_bulk_review(args.base_ref, labels, load_laboratories(ROOT), problems)
    return problems.finish()


if __name__ == "__main__":
    raise SystemExit(main())

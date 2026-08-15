#!/usr/bin/env python3
"""Preview and import collective JSON into the structured editorial collections."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from people_data import load_professors
from laboratory_data import load_laboratories


ROOT = Path(__file__).resolve().parents[1]
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class Collection:
    key: str
    path: str
    schema: str
    individual_files: bool = False


COLLECTIONS = {
    "pessoas": Collection("professores", "data/pessoal/professores", "schemas/professores.schema.json", True),
    "departamentos": Collection("departamentos", "data/departamentos.json", "schemas/departamentos.schema.json"),
    "laboratorios": Collection("laboratorios", "data/laboratorios", "schemas/laboratorios.schema.json", True),
    "projetos": Collection("projetos", "data/projetos.json", "schemas/projetos.schema.json"),
    "linhas": Collection("linhas", "data/linhas_pesquisa.json", "schemas/linhas-pesquisa.schema.json"),
    "documentos": Collection("categorias", "data/documentos.json", "schemas/documentos.schema.json"),
}


def records_from_payload(payload: Any, key: str) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict) and isinstance(payload.get(key), list):
        records = payload[key]
    else:
        raise ValueError(f'use uma lista JSON ou um objeto com a chave "{key}"')
    if not all(isinstance(record, dict) for record in records):
        raise ValueError("cada item do lote deve ser um objeto JSON")
    return records


def normalize_records(kind: str, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for record in records:
        item = dict(record)
        if kind == "pessoas":
            photo = item.get("foto", "")
            if isinstance(photo, str) and photo.startswith("/images/pessoal/"):
                item["foto"] = photo.removeprefix("/")
        normalized.append(item)
    return normalized


def current_payload(collection: Collection) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if collection.individual_files:
        records = load_professors(ROOT) if collection.key == "professores" else load_laboratories(ROOT)
        return {"schema_version": 1}, records
    payload = json.loads((ROOT / collection.path).read_text(encoding="utf-8"))
    return payload, payload[collection.key]


def merged_records(
    current: list[dict[str, Any]], incoming: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    merged = [incoming.get(record["id"], record) for record in current]
    merged.extend(incoming[key] for key in sorted(set(incoming) - {record["id"] for record in current}))
    return merged


def validate_payload(collection: Collection, payload: dict[str, Any]) -> list[str]:
    schema = json.loads((ROOT / collection.schema).read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = []
    for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.absolute_path)):
        location = "/".join(str(part) for part in error.absolute_path) or "<raiz>"
        errors.append(f"{location}: {error.message}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("colecao", choices=sorted(COLLECTIONS), help="tipo de conteúdo do lote")
    parser.add_argument("arquivo", type=Path, help="lista JSON ou objeto com a chave da coleção")
    parser.add_argument("--apply", action="store_true", help="grava os dados; sem esta opção, apenas mostra a prévia")
    parser.add_argument(
        "--update-existing",
        action="store_true",
        help="permite atualizar IDs existentes; sem esta opção, o importador para antes de sobrescrever",
    )
    args = parser.parse_args()
    collection = COLLECTIONS[args.colecao]

    try:
        raw = json.loads(args.arquivo.read_text(encoding="utf-8"))
        records = normalize_records(args.colecao, records_from_payload(raw, collection.key))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Lote inválido: {exc}", file=sys.stderr)
        return 2

    seen: set[str] = set()
    errors = []
    for position, record in enumerate(records, 1):
        identifier = record.get("id")
        if not isinstance(identifier, str) or not ID_PATTERN.fullmatch(identifier):
            errors.append(f"item {position}: ID ausente ou inválido")
            continue
        if identifier in seen:
            errors.append(f"item {position}: ID repetido no lote: {identifier}")
        seen.add(identifier)

    base_payload, current_records = current_payload(collection)
    current = {record["id"]: record for record in current_records}
    incoming = {record["id"]: record for record in records if isinstance(record.get("id"), str)}
    merged = merged_records(current_records, incoming)
    candidate = dict(base_payload)
    candidate[collection.key] = merged
    errors.extend(validate_payload(collection, candidate))
    if errors:
        print("Lote recusado:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    added = sorted(set(incoming) - set(current))
    changed = sorted(key for key in set(incoming) & set(current) if incoming[key] != current[key])
    unchanged = sorted(key for key in set(incoming) & set(current) if incoming[key] == current[key])
    print(f"Lote válido para {args.colecao}: {len(records)} item(ns).")
    print(f"Novos: {len(added)}; atualizados: {len(changed)}; sem mudança: {len(unchanged)}.")
    for label, identifiers in (("NOVO", added), ("ATUALIZA", changed)):
        for identifier in identifiers:
            title = incoming[identifier].get("nome") or incoming[identifier].get("nome_pt") or incoming[identifier].get("titulo_pt") or ""
            print(f"- {label}: {identifier}{f' — {title}' if title else ''}")

    if changed and not args.update_existing:
        print("Nada foi gravado: use --update-existing após conferir as atualizações.", file=sys.stderr)
        return 3
    if not args.apply:
        print("Prévia concluída; nada foi gravado. Use --apply para confirmar.")
        return 0

    if collection.individual_files:
        target = ROOT / collection.path
        target.mkdir(parents=True, exist_ok=True)
        for identifier in added + changed:
            path = target / f"{identifier}.json"
            path.write_text(json.dumps(incoming[identifier], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        path = ROOT / collection.path
        path.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    validation = subprocess.run([sys.executable, "scripts/validate_data.py"], cwd=ROOT, check=False)
    if validation.returncode:
        print("Os dados foram gravados, mas a validação geral falhou; não envie as mudanças para revisão.", file=sys.stderr)
        return validation.returncode
    print("Importação concluída e validada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

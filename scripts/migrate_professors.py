#!/usr/bin/env python3
"""Migrate the legacy staff sources to the canonical editorial data contract.

The command is intentionally deterministic: running it twice against the same
inputs produces byte-for-byte identical JSON and report files.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import unicodedata
from pathlib import Path
from typing import Any

import yaml


DEPARTMENTS = ("iea-a", "iea-b", "iea-c", "iea-e", "iea-p", "iea-s")
LINK_KEYS = (
    "lattes",
    "scopus",
    "orcid",
    "google_scholar",
    "researchgate",
    "web_of_science",
    "site",
)
MIGRATION_DATE = "2026-08-14"
SOURCE_COMMIT = "31afe4a65a07127dd8a33b2c2ce8200762c98f9e"


def canonical_id(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def git_text(root: Path, source_path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{SOURCE_COMMIT}:{source_path}"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"não foi possível ler {source_path} no commit {SOURCE_COMMIT}")
    return result.stdout


def git_json(root: Path, source_path: str) -> dict[str, Any]:
    return json.loads(git_text(root, source_path))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    path.write_text(rendered, encoding="utf-8")


def load_members(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    members: list[dict[str, Any]] = []
    reports: list[str] = []
    by_slug: dict[str, list[dict[str, Any]]] = {}

    for department in DEPARTMENTS:
        source_path = f"data/pessoal/{department}.yaml"
        data = yaml.safe_load(git_text(root, source_path))
        for position, item in enumerate(data.get("membros", [])):
            member = dict(item)
            member["departamento"] = department
            member["_position"] = position
            source_slug = member.get("perfil") or member.get("slug")
            if not source_slug:
                reports.append(f"Registro sem slug em `{source_path}`: {member.get('nome', '<sem nome>')}")
                continue
            slug = canonical_id(str(source_slug))
            if slug != source_slug:
                reports.append(f"Slug `{source_slug}` normalizado para `{slug}`.")
            member["id"] = slug
            by_slug.setdefault(slug, []).append(member)

    for slug, candidates in by_slug.items():
        if len(candidates) == 1:
            members.append(candidates[0])
            continue

        # Prefer the record that explicitly links the matching detailed profile.
        linked = [candidate for candidate in candidates if candidate.get("perfil") == slug]
        selected = linked[0] if len(linked) == 1 else candidates[0]
        places = ", ".join(candidate["departamento"] for candidate in candidates)
        reports.append(
            f"Duplicidade `{slug}` em {places}; mantido `{selected['departamento']}` "
            "(registro com vínculo explícito ao perfil)."
        )
        members.append(selected)

    department_rank = {value: index for index, value in enumerate(DEPARTMENTS)}
    members.sort(key=lambda item: (department_rank[item["departamento"]], item["_position"]))
    return members, reports


def normalized_links(profile: dict[str, Any]) -> dict[str, str]:
    source = profile.get("links") or {}
    return {key: source.get(key) or "" for key in LINK_KEYS}


def canonical_record(
    root: Path,
    member: dict[str, Any] | None,
    profile: dict[str, Any] | None,
) -> dict[str, Any]:
    profile = profile or {}
    active = member is not None
    professor_id = (member or {}).get("id") or profile["id"]
    raw_photo = profile.get("foto") or ""
    photo_file = root / "static" / "images" / "pessoal" / Path(raw_photo).name
    photo = f"/images/pessoal/{photo_file.name}" if raw_photo and photo_file.is_file() else ""
    scopus_author_id = (profile.get("scopus_ids") or {}).get("author_id")

    cargos: list[str] = []
    if member and member.get("cargo_divisao"):
        cargos.append(str(member["cargo_divisao"]))

    source_path = (
        f"Cadastro departamental anterior, migrado do commit {SOURCE_COMMIT}"
        if member
        else f"Perfil legado inativo, migrado do commit {SOURCE_COMMIT}"
    )

    return {
        "id": professor_id,
        "nome": (member or {}).get("nome") or profile.get("nome") or professor_id,
        "nome_destaque": profile.get("nome_destaque") or "",
        "ativo": active,
        "departamento": (member or {}).get("departamento") or "",
        "categoria": (member or {}).get("categoria") or "",
        "posto": (member or {}).get("posto") or "",
        "cargos": cargos,
        "chefe_departamento": bool((member or {}).get("chefe_departamento", False)),
        "foto": photo,
        "email": profile.get("email") or "",
        "links": normalized_links(profile),
        "scopus_author_ids": [str(scopus_author_id)] if scopus_author_id else [],
        "linhas_pesquisa": profile.get("linhas_pesquisa") or {"pt": [], "en": []},
        "resumo": profile.get("resumo") or {"pt": "", "en": ""},
        "formacao_academica": profile.get("formacao_academica") or [],
        "premios_titulos": profile.get("premios_titulos") or [],
        "idiomas": profile.get("idiomas") or [],
        "bolsista_cnpq": profile.get("bolsista_cnpq") or "",
        "fonte": source_path,
        "verificado_em": MIGRATION_DATE,
    }


def generated_author(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "metrics": profile.get("metrics") or {},
        "publicacoes": profile.get("publicacoes") or [],
        "metadata": profile.get("scopus_metadata") or {},
    }


def render_report(
    active_records: list[dict[str, Any]],
    inactive_records: list[dict[str, Any]],
    members: list[dict[str, Any]],
    profiles: dict[str, dict[str, Any]],
    notices: list[str],
) -> str:
    without_profile = [item for item in members if item["id"] not in profiles]
    missing_photos = [item for item in active_records if not item["foto"]]
    lines = [
        "# Relatório de migração do cadastro de pessoal",
        "",
        f"Gerado deterministicamente em referência à migração de {MIGRATION_DATE}.",
        "",
        "## Resumo",
        "",
        f"- Registros ativos: {len(active_records)}",
        f"- Perfis legados preservados como inativos: {len(inactive_records)}",
        f"- Ativos sem perfil detalhado anterior: {len(without_profile)}",
        f"- Ativos sem foto disponível: {len(missing_photos)}",
        "",
        "## Divergências resolvidas automaticamente",
        "",
    ]
    lines.extend(f"- {notice}" for notice in notices)
    if not notices:
        lines.append("- Nenhuma.")

    lines.extend(["", "## Ativos sem perfil detalhado anterior", ""])
    lines.extend(
        f"- `{item['id']}` — {item['nome']} ({item['departamento']})" for item in without_profile
    )
    if not without_profile:
        lines.append("- Nenhum.")

    lines.extend(["", "## Perfis legados marcados como inativos", ""])
    lines.extend(f"- `{item['id']}` — {item['nome']}" for item in inactive_records)
    if not inactive_records:
        lines.append("- Nenhum.")

    lines.extend(["", "## Ativos sem foto", ""])
    lines.extend(f"- `{item['id']}` — {item['nome']}" for item in missing_photos)
    if not missing_photos:
        lines.append("- Nenhum.")
    lines.append("")
    return "\n".join(lines)


def migrate(root: Path) -> None:
    members, notices = load_members(root)
    listing = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", SOURCE_COMMIT, "--", "data/pessoal/profiles"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    profile_paths = sorted(path for path in listing.stdout.splitlines() if path.endswith(".json"))
    profiles = {Path(path).stem: git_json(root, path) for path in profile_paths}

    active_records = [canonical_record(root, member, profiles.get(member["id"])) for member in members]
    active_ids = {record["id"] for record in active_records}
    inactive_records = [
        canonical_record(root, None, profile)
        for professor_id, profile in sorted(profiles.items())
        if professor_id not in active_ids
    ]

    canonical = {
        "schema_version": 1,
        "professores": active_records + inactive_records,
    }
    generated = {
        "schema_version": 1,
        "autores": {
            professor_id: generated_author(profile)
            for professor_id, profile in sorted(profiles.items())
        },
    }
    update_dates = [
        profile.get("metrics", {}).get("ultima_atualizacao")
        for profile in profiles.values()
        if profile.get("metrics", {}).get("ultima_atualizacao")
    ]
    manifest = {
        "source": "scopus",
        "generated_at": f"{max(update_dates)}T00:00:00Z" if update_dates else None,
        "status": "migrated",
        "records": len(generated["autores"]),
        "pipeline_version": "legacy-migration-v1",
        "last_complete_run": f"{max(update_dates)}T00:00:00Z" if update_dates else None,
    }

    write_json(root / "data" / "pessoal" / "professores.json", canonical)
    write_json(root / "data" / "generated" / "scopus" / "autores.json", generated)
    write_json(root / "data" / "generated" / "scopus" / "manifest.json", manifest)
    report = render_report(active_records, inactive_records, members, profiles, notices)
    report_path = root / "docs" / "content-management" / "migration-report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root (defaults to the parent of scripts/).",
    )
    args = parser.parse_args()
    migrate(args.root.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

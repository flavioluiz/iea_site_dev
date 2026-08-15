#!/usr/bin/env python3
"""Create a human-readable semantic diff for editorial review."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from people_data import load_professors, load_professors_at_ref
from laboratory_data import load_laboratories, load_laboratories_at_ref


ROOT = Path(__file__).resolve().parents[1]


def current_data() -> list[dict[str, Any]]:
    return load_professors(ROOT)


def data_at_ref(ref: str) -> list[dict[str, Any]] | None:
    return load_professors_at_ref(ROOT, ref)


def indexed(data: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in data}


def changed_fields(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    return sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key))


def changed_generated_files(base_ref: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", base_ref, "--", "data/generated"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return sorted(path for path in result.stdout.splitlines() if path)


def laboratory_diff(base_ref: str) -> tuple[list[str], list[str], list[str]]:
    base_records = load_laboratories_at_ref(ROOT, base_ref) or []
    before = indexed(base_records)
    after = indexed(load_laboratories(ROOT))
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(key for key in set(before) & set(after) if before[key] != after[key])
    return added, removed, changed


def render(base_ref: str) -> str:
    base_data = data_at_ref(base_ref)
    before = indexed(base_data) if base_data else {}
    after = indexed(current_data())
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(key for key in set(before) & set(after) if before[key] != after[key])
    deactivated = sorted(
        key for key in changed if before[key].get("ativo") and not after[key].get("ativo")
    )
    labs_added, labs_removed, labs_changed = laboratory_diff(base_ref)

    lines = [
        "# Relatório semântico de conteúdo",
        "",
        f"Base comparada: `{base_ref}`.",
        "" if base_data else "O cadastro canônico ainda não existia na base; esta é a migração inicial.",
        "",
        "## Resumo",
        "",
        f"- Pessoas adicionadas: {len(added)}",
        f"- Pessoas removidas do cadastro: {len(removed)}",
        f"- Pessoas alteradas: {len(changed)}",
        f"- Pessoas desativadas: {len(deactivated)}",
        f"- Laboratórios adicionados: {len(labs_added)}",
        f"- Laboratórios removidos: {len(labs_removed)}",
        f"- Laboratórios alterados: {len(labs_changed)}",
        "",
        "## Adicionadas",
        "",
    ]
    lines.extend(f"- `{key}` — {after[key]['nome']}" for key in added)
    if not added:
        lines.append("- Nenhuma.")
    lines.extend(["", "## Removidas do cadastro", ""])
    lines.extend(f"- `{key}` — {before[key]['nome']}" for key in removed)
    if not removed:
        lines.append("- Nenhuma.")
    lines.extend(["", "## Alteradas", ""])
    for key in changed:
        fields = ", ".join(f"`{field}`" for field in changed_fields(before[key], after[key]))
        lines.append(f"- `{key}` — {after[key]['nome']}: {fields}")
    if not changed:
        lines.append("- Nenhuma.")

    lines.extend(["", "## Laboratórios", ""])
    for label, identifiers in (
        ("Adicionado", labs_added),
        ("Removido", labs_removed),
        ("Alterado", labs_changed),
    ):
        lines.extend(f"- {label}: `{identifier}`" for identifier in identifiers)
    if not (labs_added or labs_removed or labs_changed):
        lines.append("- Nenhuma alteração semântica.")

    generated = json.loads(
        (ROOT / "data" / "generated" / "scopus" / "autores.json").read_text(encoding="utf-8")
    )["autores"]
    references = sum(len(item.get("publicacoes", [])) for item in generated.values())
    library_manifest = json.loads(
        (ROOT / "data" / "generated" / "biblioteca" / "manifest.json").read_text(encoding="utf-8")
    )
    generated_changes = changed_generated_files(base_ref)
    lines.extend(
        [
            "",
            "## Dados automáticos atuais",
            "",
            f"- Autores Scopus: {len(generated)}",
            f"- Referências autor–publicação: {references}",
            f"- Registros da Biblioteca: {library_manifest['records']}",
            f"- Arquivos derivados alterados neste PR: {len(generated_changes)}",
            "",
            "## Arquivos derivados alterados",
            "",
        ]
    )
    lines.extend(f"- `{path}`" for path in generated_changes[:30])
    if len(generated_changes) > 30:
        lines.append(f"- … e mais {len(generated_changes) - 30} arquivos; confira o artefato/diff do pipeline.")
    if not generated_changes:
        lines.append("- Nenhum.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    text = render(args.base_ref)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

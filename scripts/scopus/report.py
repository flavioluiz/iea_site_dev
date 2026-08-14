#!/usr/bin/env python3
"""Render the auditable semantic report for a normalized Scopus candidate."""

from __future__ import annotations

import copy
from typing import Any


TIMESTAMP_KEYS = {"generated_at", "last_complete_run", "last_updated", "updated_at", "ultima_atualizacao"}


def semantic(value: Any) -> Any:
    value = copy.deepcopy(value)
    if isinstance(value, dict):
        for key in tuple(value):
            if key in TIMESTAMP_KEYS:
                value.pop(key)
            else:
                value[key] = semantic(value[key])
    elif isinstance(value, list):
        value = [semantic(item) for item in value]
    return value


def changed_keys(before: dict[str, Any], after: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(key for key in set(before) & set(after) if semantic(before[key]) != semantic(after[key]))
    return added, removed, changed


def render_report(
    previous_authors: dict[str, Any],
    candidate_authors: dict[str, Any],
    previous_publications: dict[str, Any],
    candidate_publications: dict[str, Any],
    curated_ids: dict[str, list[str]],
    full_run: bool,
    previous_curated_ids: dict[str, list[str]] | None = None,
) -> str:
    publication_added, publication_removed, publication_changed = changed_keys(
        previous_publications, candidate_publications
    )
    author_added, author_removed, author_changed = changed_keys(previous_authors, candidate_authors)
    lines = [
        "# Atualização Scopus",
        "",
        f"- Modo: {'conjunto completo' if full_run else 'parcial'}",
        f"- Pessoas processadas: {len(curated_ids)}",
        f"- Autores: +{len(author_added)} / ~{len(author_changed)} / -{len(author_removed)}",
        f"- Publicações: {len(previous_publications)} → {len(candidate_publications)}",
        f"- Publicações: +{len(publication_added)} / ~{len(publication_changed)} / -{len(publication_removed)}",
        "- Abstracts, e-mails, afiliações e vocabulário controlado publicados: 0",
        "",
        "## Mudanças em IDs Scopus curados",
        "",
    ]
    if previous_curated_ids is None:
        lines.append("- Baseline de IDs ainda não disponível; confira a lista completa abaixo.")
    else:
        id_added, id_removed, id_changed = changed_keys(previous_curated_ids, curated_ids)
        lines.extend(f"- Pessoa adicionada ao acompanhamento: `{identifier}`" for identifier in id_added)
        lines.extend(f"- IDs alterados: `{identifier}`" for identifier in id_changed)
        lines.extend(f"- Pessoa removida do acompanhamento: `{identifier}`" for identifier in id_removed)
        if not any((id_added, id_changed, id_removed)):
            lines.append("- Nenhuma mudança nos IDs curados.")
    lines.extend([
        "",
        "## IDs Scopus curados usados",
        "",
    ])
    lines.extend(
        f"- `{professor_id}`: {', '.join(author_ids)}"
        for professor_id, author_ids in sorted(curated_ids.items())
    )
    lines.extend(["", "## Pessoas alteradas", ""])
    lines.extend(f"- Adicionada: `{identifier}`" for identifier in author_added)
    lines.extend(f"- Alterada: `{identifier}`" for identifier in author_changed)
    lines.extend(f"- Removida: `{identifier}`" for identifier in author_removed)
    if not any((author_added, author_changed, author_removed)):
        lines.append("- Nenhuma.")
    lines.extend(["", "## Publicações adicionadas, alteradas e removidas", ""])
    lines.extend(f"- Adicionada: `{identifier}`" for identifier in publication_added[:100])
    lines.extend(f"- Alterada: `{identifier}`" for identifier in publication_changed[:100])
    lines.extend(f"- Removida: `{identifier}`" for identifier in publication_removed[:100])
    remaining = sum(
        max(0, len(items) - 100)
        for items in (publication_added, publication_changed, publication_removed)
    )
    if remaining > 0:
        lines.append(f"- … e mais {remaining} itens no diff do PR.")
    if not any((publication_added, publication_changed, publication_removed)):
        lines.append("- Nenhuma mudança substantiva.")
    lines.append("")
    return "\n".join(lines)

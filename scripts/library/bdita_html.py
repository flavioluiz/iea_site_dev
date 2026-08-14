"""Small, fixture-testable parser for the legacy BDITA HTML catalogue."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()


def stable_id(href: str, query_key: str) -> str:
    values = parse_qs(urlparse(href).query).get(query_key, [])
    return clean(values[0]) if values else ""


def parse_list(html: str, base_url: str, kind: str, course: str = "") -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if table is None:
        raise ValueError("BDITA list no longer contains the expected table")
    records: list[dict[str, Any]] = []
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 5:
            continue
        title_link = cells[1].find("a")
        if title_link is None:
            continue
        href = title_link.get("href", "")
        query_key = "num_tese" if kind == "teses" else "num_tg"
        identifier = stable_id(href, query_key)
        if not identifier:
            continue
        author_link = cells[2].find("a")
        record = {
            query_key: identifier,
            "title": clean(title_link.get_text(" ", strip=True)),
            "author": clean((author_link or cells[2]).get_text(" ", strip=True)),
            "detail_url": urljoin(base_url, href),
        }
        if kind == "teses":
            if len(cells) < 6:
                continue
            record.update(
                program=clean(cells[3].get_text(" ", strip=True)),
                year=clean(cells[4].get_text(" ", strip=True)),
                course=clean(cells[5].get_text(" ", strip=True)).replace("Acadęmico", "Acadêmico"),
            )
            pdf_cell = cells[6] if len(cells) > 6 else None
        else:
            record.update(
                course=course or clean(cells[3].get_text(" ", strip=True)),
                curso=course or clean(cells[3].get_text(" ", strip=True)),
                year=clean(cells[4].get_text(" ", strip=True)),
            )
            pdf_cell = cells[5] if len(cells) > 5 else None
        pdf_link = pdf_cell.find("a") if pdf_cell else None
        record["pdf_url"] = urljoin(base_url, pdf_link.get("href", "")) if pdf_link else ""
        records.append(record)
    if not records:
        raise ValueError("BDITA list parsed zero records")
    return records


LABELS = {
    "título": "title", "titulo": "title", "autor": "author", "programa": "program",
    "área de concentração": "area", "area de concentracao": "area", "orientador": "advisors",
    "orientadores": "advisors", "co-orientador": "co_advisors", "coorientador": "co_advisors",
    "co-orientadores": "co_advisors", "coorientadores": "co_advisors",
    "ano de publicação": "year", "ano de publicacao": "year", "curso": "course",
    "assunto": "subjects", "assuntos": "subjects", "resumo": "abstract",
    "data de defesa": "defense_date", "texto na íntegra": "fulltext", "texto na integra": "fulltext",
}


def parse_detail(html: str, base_url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if table is None:
        raise ValueError("BDITA detail no longer contains the expected table")
    fields: dict[str, Any] = {}
    current_label = ""
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        raw_label = clean(cells[0].get_text(" ", strip=True)).rstrip(":").lower()
        if raw_label and raw_label != "t":
            current_label = raw_label
        key = LABELS.get(current_label)
        if key is None and "orientador" in current_label:
            key = "co_advisors" if current_label.startswith("co") else "advisors"
        if key is None:
            continue
        value = clean(cells[1].get_text(" ", strip=True))
        if key == "fulltext":
            link = cells[1].find("a")
            fields["fulltext_url"] = urljoin(base_url, link.get("href", "")) if link else ""
        elif key in {"advisors", "co_advisors", "subjects"}:
            if value:
                fields.setdefault(key, []).append(value)
        elif key not in fields:
            fields[key] = value
    return fields

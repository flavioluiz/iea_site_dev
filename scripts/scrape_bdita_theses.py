#!/usr/bin/env python3
"""
Scrape BDITA theses/dissertations list and detail pages into a JSON database.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


BASE_URL = "http://www.bdita.bibl.ita.br/tesesdigitais/"
DEFAULT_LIST_URL = (
    "http://www.bdita.bibl.ita.br/tesesdigitais/"
    "resultado_titulos_programas.php?ano_inicio=1984&ano_fim=2025"
    "&tipo_tese=Todos&programa=Engenharia%20Aeron%E1utica%20e%20Mec%E2nica"
    "&area_concen=&total_teses_prog=3128"
)


def clean_text(value: str) -> str:
    text = value.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_label(value: str) -> str:
    text = clean_text(value)
    text = text.rstrip(":").strip()
    return text


def normalize_label(value: str) -> Optional[str]:
    text = clean_label(value).lower()
    mapping = {
        "título": "title",
        "titulo": "title",
        "autor": "author",
        "programa": "program",
        "área de concentração": "area_concentration",
        "area de concentracao": "area_concentration",
        "orientador": "advisors",
        "orientadores": "advisors",
        "co-orientador": "co_advisors",
        "co-orientadores": "co_advisors",
        "coorientador": "co_advisors",
        "coorientadores": "co_advisors",
        "ano de publicação": "year",
        "ano de publicacao": "year",
        "curso": "course",
        "assunto": "subjects",
        "assuntos": "subjects",
        "resumo": "abstract",
        "data de defesa": "defense_date",
        "texto na íntegra": "fulltext",
        "texto na integra": "fulltext",
    }
    if text in mapping:
        return mapping[text]
    if "orientador" in text:
        if text.startswith("co") or "co-" in text:
            return "co_advisors"
        return "advisors"
    if text.startswith("assunto"):
        return "subjects"
    return None


def fetch_url(
    session: requests.Session,
    url: str,
    cache_path: Optional[Path] = None,
    force: bool = False,
) -> str:
    if cache_path and cache_path.exists() and not force:
        return cache_path.read_text(encoding="utf-8")

    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding
    text = resp.text

    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(text, encoding="utf-8")
    return text


def parse_list_page(html: str, base_url: str) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return []

    rows: List[Dict[str, str]] = []
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 6:
            continue

        title_link = tds[1].find("a")
        if not title_link:
            continue

        detail_href = title_link.get("href", "").strip()
        detail_url = urljoin(base_url, detail_href)
        parsed = urlparse(detail_href)
        num_tese = parse_qs(parsed.query).get("num_tese", [None])[0]
        if not num_tese and "num_tese=" in detail_href:
            num_tese = detail_href.split("num_tese=", 1)[-1]

        author_link = tds[2].find("a")
        pdf_link = tds[6].find("a") if len(tds) > 6 else None
        pdf_href = pdf_link.get("href", "").strip() if pdf_link else ""

        rows.append(
            {
                "num_tese": num_tese or "",
                "title": clean_text(title_link.get_text()),
                "author": clean_text(
                    author_link.get_text() if author_link else tds[2].get_text()
                ),
                "program": clean_text(tds[3].get_text()),
                "year": clean_text(tds[4].get_text()),
                "course": clean_text(tds[5].get_text()),
                "detail_url": detail_url,
                "pdf_url": urljoin(base_url, pdf_href) if pdf_href else "",
            }
        )

    return rows


def add_value(target: Dict[str, Any], key: str, value: Any, always_list: bool) -> None:
    if always_list:
        target.setdefault(key, []).append(value)
        return

    if key not in target:
        target[key] = value
        return

    existing = target[key]
    if isinstance(existing, list):
        existing.append(value)
    else:
        target[key] = [existing, value]


def parse_detail_page(html: str, base_url: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return {"fields": {}, "fields_raw": {}}

    fields: Dict[str, Any] = {}
    fields_raw: Dict[str, List[Any]] = {}
    current_label: Optional[str] = None

    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 2:
            continue

        label_raw = clean_label(tds[0].get_text(" ", strip=True))
        value_text = clean_text(tds[1].get_text(" ", strip=True))
        label = label_raw or None

        if not label or label.lower() == "t":
            label = current_label
        if not label:
            continue

        current_label = label
        fields_raw.setdefault(label, []).append(value_text)

        normalized = normalize_label(label)
        if normalized == "fulltext":
            link = tds[1].find("a")
            href = link.get("href", "").strip() if link else ""
            fulltext_url = urljoin(base_url, href) if href else ""
            add_value(fields, "fulltext_url", fulltext_url, always_list=False)
            continue

        if normalized:
            multi = normalized in {"subjects", "advisors", "co_advisors"}
            add_value(fields, normalized, value_text, always_list=multi)

    return {"fields": fields, "fields_raw": fields_raw}


def merge_list_fields(entry: Dict[str, Any], list_row: Dict[str, str]) -> None:
    fields = entry.setdefault("fields", {})
    if not fields.get("title") and list_row.get("title"):
        fields["title"] = list_row["title"]
    if not fields.get("author") and list_row.get("author"):
        fields["author"] = list_row["author"]
    if not fields.get("program") and list_row.get("program"):
        fields["program"] = list_row["program"]
    if not fields.get("year") and list_row.get("year"):
        fields["year"] = list_row["year"]
    if not fields.get("course") and list_row.get("course"):
        fields["course"] = list_row["course"]


def load_existing(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape BDITA theses into JSON.")
    parser.add_argument("--list-url", default=DEFAULT_LIST_URL)
    parser.add_argument(
        "--out-file",
        default="data/tesesdigitais_eam.json",
        help="JSON output file path.",
    )
    parser.add_argument(
        "--cache-dir",
        default="data/tesesdigitais_cache",
        help="Optional cache directory for HTML pages.",
    )
    parser.add_argument("--sleep", type=float, default=0.4)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--include-courses",
        default="Mestrado Acadêmico,Doutorado",
        help="Comma-separated list of course names to include.",
    )
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument("--resume", action="store_true", default=True)
    parser.add_argument("--no-resume", action="store_true", help="Re-scrape all theses from scratch.")

    args = parser.parse_args()

    out_path = Path(args.out_file)
    cache_dir = Path(args.cache_dir) if args.cache_dir else None
    include_courses = [c.strip() for c in args.include_courses.split(",") if c.strip()]
    limit = args.limit if args.limit and args.limit > 0 else None

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
    )

    list_cache = cache_dir / "list.html" if cache_dir else None
    list_html = fetch_url(
        session, args.list_url, cache_path=list_cache, force=args.force_refresh
    )
    list_rows = parse_list_page(list_html, BASE_URL)
    if include_courses:
        list_rows = [r for r in list_rows if r.get("course") in include_courses]
    if limit:
        list_rows = list_rows[:limit]

    existing = load_existing(out_path) if args.resume and not args.no_resume else {}
    existing_items = {
        item.get("num_tese")
        for item in existing.get("theses", [])
        if item.get("num_tese")
    }

    if existing_items:
        new_count = sum(1 for r in list_rows if r.get("num_tese") not in existing_items)
        print(f"Existing: {len(existing_items)}, new to fetch: {new_count}, total on site: {len(list_rows)}")

    results: List[Dict[str, Any]] = []
    if args.resume and not args.no_resume and existing.get("theses"):
        results.extend(existing["theses"])

    for idx, row in enumerate(list_rows, 1):
        num_tese = row.get("num_tese")
        if args.resume and not args.no_resume and num_tese in existing_items:
            continue

        detail_cache = (
            cache_dir / f"detail_{num_tese}.html" if cache_dir and num_tese else None
        )
        detail_html = fetch_url(
            session,
            row["detail_url"],
            cache_path=detail_cache,
            force=args.force_refresh,
        )
        detail_data = parse_detail_page(detail_html, BASE_URL)

        entry = {
            "num_tese": num_tese,
            "detail_url": row["detail_url"],
            "pdf_url": row.get("pdf_url", ""),
            "list_entry": row,
            **detail_data,
        }
        merge_list_fields(entry, row)
        results.append(entry)

        if idx < len(list_rows):
            time.sleep(args.sleep)

    output = {
        "metadata": {
            "source_list_url": args.list_url,
            "generated_at": datetime.now().isoformat(),
            "total_listed": len(list_rows),
            "total_saved": len(results),
            "filters": {
                "include_courses": include_courses,
                "limit": limit,
                "resume": args.resume,
            },
        },
        "theses": results,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(results)} records to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

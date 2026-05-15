#!/usr/bin/env python3
"""
Scrape teses e dissertações do BDITA orientadas por professores da IEA/ITA.

Baixa todas as teses do programa PG-EAM (Mestrado Acadêmico + Doutorado)
e filtra aquelas cujo orientador ou co-orientador é um professor atual da IEA.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE_URL = "http://www.bdita.bibl.ita.br/tesesdigitais/"
LIST_URL = (
    "http://www.bdita.bibl.ita.br/tesesdigitais/"
    "resultado_titulos_programas.php?ano_inicio=1984&ano_fim=2025"
    "&tipo_tese=Todos&programa=Engenharia%20Aeron%E1utica%20e%20Mec%E2nica"
    "&area_concen=&total_teses_prog=3128"
)
INCLUDE_COURSES = {"Mestrado Acadêmico", "Doutorado"}

BASE = Path(__file__).parent.parent
OUT_FILE = BASE / "data" / "bdita_teses_raw.json"
CACHE_DIR = BASE / "data" / "bdita_teses_cache"


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("\xa0", " ")).strip()


def normalize_label(label: str) -> Optional[str]:
    t = clean(label).rstrip(":").lower()
    mapping = {
        "título": "title", "titulo": "title",
        "autor": "author",
        "programa": "program",
        "área de concentração": "area", "area de concentracao": "area",
        "orientador": "advisors", "orientadores": "advisors",
        "co-orientador": "co_advisors", "co-orientadores": "co_advisors",
        "coorientador": "co_advisors", "coorientadores": "co_advisors",
        "ano de publicação": "year", "ano de publicacao": "year",
        "curso": "course",
        "assunto": "subjects", "assuntos": "subjects",
        "resumo": "abstract",
        "data de defesa": "defense_date",
        "texto na íntegra": "fulltext", "texto na integra": "fulltext",
    }
    if t in mapping:
        return mapping[t]
    if "orientador" in t:
        return "co_advisors" if t.startswith("co") or "co-" in t else "advisors"
    if t.startswith("assunto"):
        return "subjects"
    return None


def fetch(session: requests.Session, url: str, cache: Optional[Path] = None) -> str:
    if cache and cache.exists():
        return cache.read_text(encoding="utf-8")
    r = session.get(url, timeout=30)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(r.text, encoding="utf-8")
    return r.text


def parse_list(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return []
    rows = []
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 6:
            continue
        link = tds[1].find("a")
        if not link:
            continue
        href = link.get("href", "").strip()
        qs = parse_qs(urlparse(href).query)
        num = qs.get("num_tese", [""])[0] or href.split("num_tese=")[-1]
        author_link = tds[2].find("a")
        course = clean(tds[5].get_text())
        if course not in INCLUDE_COURSES:
            continue
        pdf_link = tds[6].find("a") if len(tds) > 6 else None
        rows.append({
            "num_tese": num,
            "title": clean(link.get_text()),
            "author": clean(author_link.get_text() if author_link else tds[2].get_text()),
            "program": clean(tds[3].get_text()),
            "year": clean(tds[4].get_text()),
            "course": course,
            "detail_url": urljoin(BASE_URL, href),
            "pdf_url": urljoin(BASE_URL, pdf_link.get("href", "")) if pdf_link else "",
        })
    return rows


def parse_detail(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return {}
    fields: Dict[str, Any] = {}
    cur_label = None
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 2:
            continue
        raw_label = clean(tds[0].get_text(" ", strip=True)).rstrip(":")
        value = clean(tds[1].get_text(" ", strip=True))
        if not raw_label or raw_label.lower() == "t":
            raw_label = cur_label
        if not raw_label:
            continue
        cur_label = raw_label
        key = normalize_label(raw_label)
        if not key:
            continue
        if key == "fulltext":
            a = tds[1].find("a")
            fields["fulltext_url"] = urljoin(BASE_URL, a.get("href", "")) if a else ""
            continue
        if key in ("advisors", "co_advisors", "subjects"):
            fields.setdefault(key, [])
            if value:
                fields[key].append(value)
        else:
            if key not in fields:
                fields[key] = value
    return fields


def load_existing() -> Dict[str, Any]:
    if OUT_FILE.exists():
        return json.loads(OUT_FILE.read_text(encoding="utf-8"))
    return {}


def main():
    session = requests.Session()
    session.headers["User-Agent"] = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    print("Baixando lista de teses...")
    list_html = fetch(session, LIST_URL, CACHE_DIR / "list.html")
    rows = parse_list(list_html)
    print(f"Total na lista (Mestrado + Doutorado): {len(rows)}")

    existing = load_existing()
    done = {t["num_tese"] for t in existing.get("teses", [])}
    results: List[Dict] = list(existing.get("teses", []))

    new_rows = [r for r in rows if r["num_tese"] not in done]
    print(f"Já baixadas: {len(done)} | Novas: {len(new_rows)}")

    for i, row in enumerate(new_rows, 1):
        num = row["num_tese"]
        cache = CACHE_DIR / f"tese_{num}.html"
        print(f"  [{i}/{len(new_rows)}] {num}: {row['title'][:60]}")
        detail_html = fetch(session, row["detail_url"], cache)
        fields = parse_detail(detail_html)
        # merge list fields as fallback
        for k in ("title", "author", "year", "course", "program"):
            if k not in fields and row.get(k):
                fields[k] = row[k]
        results.append({
            "num_tese": num,
            "detail_url": row["detail_url"],
            "pdf_url": row.get("pdf_url", ""),
            **fields,
        })
        time.sleep(0.4)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps({
        "metadata": {
            "source": LIST_URL,
            "generated_at": datetime.now().isoformat(),
            "total": len(results),
        },
        "teses": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo: {OUT_FILE} ({len(results)} teses)")


if __name__ == "__main__":
    main()

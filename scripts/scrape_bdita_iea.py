#!/usr/bin/env python3
"""
Scrape teses/dissertações e trabalhos de graduação do BDITA para o site AER/IEA.

Teses e dissertações: programa PG-EAM (Mestrado Acadêmico + Doutorado).
TGs: cursos de Engenharia Aeronáutica e Engenharia Aeroespacial (todos os anos).

Saída:
  data/bdita/teses_raw.json   — teses/dissertações
  data/bdita/tgs_raw.json     — trabalhos de graduação
  data/bdita/cache/           — cache HTML das páginas
"""

from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# ── URLs ──────────────────────────────────────────────────────────────────────

TESES_BASE_URL = "http://www.bdita.bibl.ita.br/tesesdigitais/"
TGS_BASE_URL = "http://www.bdita.bibl.ita.br/TGsDigitais/"

TESES_LIST_URL = (
    "http://www.bdita.bibl.ita.br/tesesdigitais/"
    "resultado_titulos_programas.php?ano_inicio=1984&ano_fim=2025"
    "&tipo_tese=Todos&programa=Engenharia%20Aeron%E1utica%20e%20Mec%E2nica"
    "&area_concen=&total_teses_prog=3128"
)

TGS_URLS = {
    "Engenharia Aeroespacial": (
        "http://www.bdita.bibl.ita.br/TGsDigitais/"
        "resultado_titulos_cursos.php?ano_inicio=1952&ano_fim=2025"
        "&curso=Engenharia%20Aeroespacial&total_TGs_curso=173"
    ),
    "Engenharia Aeronáutica": (
        "http://www.bdita.bibl.ita.br/TGsDigitais/"
        "resultado_titulos_cursos.php?ano_inicio=1952&ano_fim=2025"
        "&curso=Engenharia%20Aeron%E1utica&total_TGs_curso=741"
    ),
}

INCLUDE_COURSES = {"Mestrado Acadêmico", "Mestrado Acadęmico", "Doutorado"}

BASE = Path(__file__).parent.parent
OUT_TESES = BASE / "data" / "bdita" / "teses_raw.json"
OUT_TGS = BASE / "data" / "bdita" / "tgs_raw.json"
# Cache fora de data/ para não confundir o Hugo (que tenta parsear tudo em data/)
CACHE_DIR = Path("/tmp/bdita_cache")


# ── helpers ───────────────────────────────────────────────────────────────────

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


def fetch(session: requests.Session, url: str, cache: Optional[Path] = None,
          force: bool = False) -> str:
    if cache and cache.exists() and not force:
        return cache.read_text(encoding="utf-8")
    r = session.get(url, timeout=30)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(r.text, encoding="utf-8")
    return r.text


def parse_detail(html: str, base_url: str) -> Dict[str, Any]:
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
            fields["fulltext_url"] = urljoin(base_url, a.get("href", "")) if a else ""
            continue
        if key in ("advisors", "co_advisors", "subjects"):
            fields.setdefault(key, [])
            if value:
                fields[key].append(value)
        else:
            if key not in fields:
                fields[key] = value
    return fields


# ── teses/dissertações ────────────────────────────────────────────────────────

def parse_teses_list(html: str) -> List[Dict]:
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
            "course": course.replace("Acadęmico", "Acadêmico"),
            "detail_url": urljoin(TESES_BASE_URL, href),
            "pdf_url": urljoin(TESES_BASE_URL, pdf_link.get("href", "")) if pdf_link else "",
        })
    return rows


def scrape_teses(session: requests.Session, force: bool = False) -> List[Dict]:
    print("=== Teses e Dissertações (PG-EAM) ===")
    list_html = fetch(session, TESES_LIST_URL, CACHE_DIR / "teses_list.html", force)
    rows = parse_teses_list(list_html)
    print(f"Na lista (Mestrado + Doutorado): {len(rows)}")

    existing = {}
    if OUT_TESES.exists():
        d = json.loads(OUT_TESES.read_text(encoding="utf-8"))
        existing = {t["num_tese"]: t for t in d.get("teses", [])}

    results = list(existing.values())
    new_rows = [r for r in rows if r["num_tese"] not in existing]
    print(f"Já baixadas: {len(existing)} | Novas: {len(new_rows)}")

    for i, row in enumerate(new_rows, 1):
        num = row["num_tese"]
        cache = CACHE_DIR / f"tese_{num}.html"
        print(f"  [{i}/{len(new_rows)}] {num}: {row['title'][:60]}")
        detail_html = fetch(session, row["detail_url"], cache, force)
        fields = parse_detail(detail_html, TESES_BASE_URL)
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

    OUT_TESES.parent.mkdir(parents=True, exist_ok=True)
    OUT_TESES.write_text(json.dumps({
        "metadata": {
            "source": TESES_LIST_URL,
            "generated_at": datetime.now().isoformat(),
            "total": len(results),
        },
        "teses": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Salvo: {OUT_TESES} ({len(results)} teses)\n")
    return results


# ── trabalhos de graduação ─────────────────────────────────────────────────────

def parse_tgs_list(html: str, curso: str) -> List[Dict]:
    # Columns: [#, título(link), autor, curso, ano, PDF]
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return []
    rows = []
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 5:
            continue
        link = tds[1].find("a")
        if not link:
            continue
        href = link.get("href", "").strip()
        qs = parse_qs(urlparse(href).query)
        num = qs.get("num_tg", [""])[0] or href.split("num_tg=")[-1]
        author_link = tds[2].find("a")
        pdf_link = tds[5].find("a") if len(tds) > 5 else None
        rows.append({
            "num_tg": num,
            "title": clean(link.get_text()),
            "author": clean(author_link.get_text() if author_link else tds[2].get_text()),
            "year": clean(tds[4].get_text()),
            "curso": curso,
            "detail_url": urljoin(TGS_BASE_URL, href),
            "pdf_url": urljoin(TGS_BASE_URL, pdf_link.get("href", "")) if pdf_link else "",
        })
    return rows


def scrape_tgs(session: requests.Session, force: bool = False) -> List[Dict]:
    print("=== Trabalhos de Graduação ===")

    existing = {}
    if OUT_TGS.exists():
        d = json.loads(OUT_TGS.read_text(encoding="utf-8"))
        existing = {t["num_tg"]: t for t in d.get("tgs", [])}

    results = list(existing.values())
    all_new = []

    for curso, url in TGS_URLS.items():
        slug = curso.lower().replace(" ", "_").replace(".", "")
        list_html = fetch(session, url, CACHE_DIR / f"tgs_list_{slug}.html", force)
        rows = parse_tgs_list(list_html, curso)
        new_rows = [r for r in rows if r["num_tg"] not in existing]
        print(f"{curso}: {len(rows)} total | novas: {len(new_rows)}")
        all_new.extend(new_rows)

    print(f"Total novas: {len(all_new)}")

    for i, row in enumerate(all_new, 1):
        num = row["num_tg"]
        cache = CACHE_DIR / f"tg_{num}.html"
        print(f"  [{i}/{len(all_new)}] {num}: {row['title'][:60]}")
        detail_html = fetch(session, row["detail_url"], cache, force)
        fields = parse_detail(detail_html, TGS_BASE_URL)
        for k in ("title", "author", "year"):
            if k not in fields and row.get(k):
                fields[k] = row[k]
        if "course" not in fields:
            fields["course"] = row["curso"]
        results.append({
            "num_tg": num,
            "curso": row["curso"],
            "detail_url": row["detail_url"],
            "pdf_url": row.get("pdf_url", ""),
            **fields,
        })
        time.sleep(0.4)

    OUT_TGS.parent.mkdir(parents=True, exist_ok=True)
    OUT_TGS.write_text(json.dumps({
        "metadata": {
            "sources": list(TGS_URLS.values()),
            "generated_at": datetime.now().isoformat(),
            "total": len(results),
        },
        "tgs": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Salvo: {OUT_TGS} ({len(results)} TGs)\n")
    return results


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--teses-only", action="store_true")
    parser.add_argument("--tgs-only", action="store_true")
    parser.add_argument("--force", action="store_true", help="Ignorar cache HTML")
    args = parser.parse_args()

    session = requests.Session()
    session.headers["User-Agent"] = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    if not args.tgs_only:
        scrape_teses(session, force=args.force)
    if not args.teses_only:
        scrape_tgs(session, force=args.force)


if __name__ == "__main__":
    main()

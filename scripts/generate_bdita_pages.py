#!/usr/bin/env python3
"""
Gera dados e páginas Hugo para teses/dissertações e TGs do BDITA.

Lê:
  data/bdita/teses_raw.json  — saída de scrape_bdita_iea.py
  data/bdita/tgs_raw.json    — idem

Gera:
  data/bdita/teses/index.json          — índice leve (busca)
  data/bdita/teses/by_id/<num>.json    — ficha completa por tese
  data/bdita/teses/by_professor.json   — teses por prof. da divisão
  data/bdita/teses/manual_matches.json — sobrescritas manuais de matching
  data/bdita/tgs/index.json
  data/bdita/tgs/by_id/<num>.json
  data/bdita/tgs/by_professor.json     — apenas TGs de prof. atuais
  content/teses/<num>/index.pt.md
  content/tgs/<num>/index.pt.md

Matching de orientadores:
  - Automático por similaridade de nome (lógica do pgeam_dev).
  - Para teses: orientador principal + co-orientadores.
  - Para TGs: campo "orientador" (se presente) é mapeado.
  - Sobrescritas manuais em data/bdita/teses/manual_matches.json
    e data/bdita/tgs/manual_matches.json.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
BDITA_DIR = DATA_DIR / "bdita"
PROFILES_DIR = DATA_DIR / "pessoal" / "profiles"
IEA_SLUGS_FILE = DATA_DIR / "pessoal" / "iea_profiles.json"

# ── name matching ─────────────────────────────────────────────────────────────

COMMON_LAST = {
    "silva", "santos", "oliveira", "souza", "rodrigues", "ferreira", "alves",
    "pereira", "lima", "gomes", "costa", "ribeiro", "martins", "carvalho",
    "almeida", "lopes", "soares", "fernandes", "vieira", "barbosa", "rocha",
    "dias", "nascimento", "andrade", "moreira", "nunes", "marques", "machado",
    "mendes", "freitas", "cardoso", "ramos", "goncalves", "santana", "teixeira",
    "neto", "junior", "filho", "sobrinho",
}
COMMON_FIRST = {
    "jose", "joao", "maria", "antonio", "pedro", "rodrigo", "carlos",
    "paulo", "luis", "luiz", "marcos", "marcelo", "andre", "rafael",
    "fernando", "roberto", "sergio", "gilberto", "amauri",
}
PREPOSITIONS = {"de", "da", "do", "dos", "das", "e"}


def normalize(name: str) -> str:
    n = unicodedata.normalize("NFKD", name)
    n = "".join(c for c in n if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", n.lower().strip())


def name_parts(name: str) -> dict:
    parts = normalize(name).split()
    return {
        "first": parts[0] if parts else "",
        "last": parts[-1] if parts else "",
        "second_to_last": parts[-2] if len(parts) > 1 else "",
        "all": set(parts),
        "full": " ".join(parts),
    }


def name_score(adv_parts: dict, prof_data: dict) -> float:
    pp = prof_data["parts"]
    if adv_parts["full"] == pp["full"]:
        return 1.0
    pn = prof_data["normalized"]
    if adv_parts["full"] in pn or pn in adv_parts["full"]:
        common = adv_parts["all"] & pp["all"]
        if common - COMMON_LAST - PREPOSITIONS - COMMON_FIRST:
            return 0.95
    if adv_parts["first"] != pp["first"]:
        return 0.0
    if adv_parts["last"] == pp["last"]:
        if adv_parts["last"] not in COMMON_LAST | COMMON_FIRST:
            return 0.9
        common = adv_parts["all"] & pp["all"]
        if common - COMMON_LAST - PREPOSITIONS - COMMON_FIRST:
            return 0.85
    if (adv_parts["second_to_last"]
            and adv_parts["second_to_last"] == pp["last"]
            and adv_parts["second_to_last"] not in COMMON_LAST | COMMON_FIRST):
        return 0.85
    destaque = prof_data.get("destaque", "")
    if destaque and destaque not in COMMON_FIRST | COMMON_LAST:
        dparts = set(destaque.split())
        adv_dist = adv_parts["all"] - PREPOSITIONS - COMMON_LAST - COMMON_FIRST
        if dparts & adv_dist:
            return 0.85
    common = adv_parts["all"] & pp["all"]
    if len(common - COMMON_LAST - PREPOSITIONS - COMMON_FIRST) >= 2:
        return 0.8
    return 0.0


def auto_match(advisor_name: str, prof_index: dict, threshold: float = 0.7):
    if not advisor_name:
        return None, 0.0
    ap = name_parts(advisor_name)
    best_id, best_score = None, 0.0
    for pid, pd in prof_index.items():
        s = name_score(ap, pd)
        if s > best_score:
            best_score, best_id = s, pid
    return (best_id, best_score) if best_score >= threshold else (None, 0.0)


# ── load professors (IEA only) ────────────────────────────────────────────────

def load_iea_professors():
    slugs = json.loads(IEA_SLUGS_FILE.read_text())["slugs"]
    professors = {}
    prof_index = {}
    for slug in slugs:
        f = PROFILES_DIR / f"{slug}.json"
        if not f.exists():
            continue
        prof = json.loads(f.read_text())
        pid = prof.get("slug") or slug
        professors[pid] = prof
        nome = prof.get("nome", "")
        if nome:
            prof_index[pid] = {
                "normalized": normalize(nome),
                "parts": name_parts(nome),
                "destaque": normalize(prof.get("nome_destaque", "")),
            }
    return professors, prof_index


# ── matching helpers ──────────────────────────────────────────────────────────

def build_advisor_mapping(records: list, adv_fields: list,
                          prof_index: dict, manual: dict) -> dict:
    """Return {advisor_name: prof_slug_or_None}."""
    all_names: set = set()
    for rec in records:
        for field in adv_fields:
            for name in (rec.get(field) or []):
                if name:
                    all_names.add(name)

    mapping = {}
    for name in all_names:
        if name in manual:
            mapping[name] = manual[name]
        else:
            pid, _ = auto_match(name, prof_index)
            mapping[name] = pid
    return mapping


# ── generate teses pages ──────────────────────────────────────────────────────

def generate_teses(professors: dict, prof_index: dict):
    raw_file = BDITA_DIR / "teses_raw.json"
    if not raw_file.exists():
        print(f"AVISO: {raw_file} não existe. Execute scrape_bdita_iea.py primeiro.")
        return

    data = json.loads(raw_file.read_text())
    teses = data.get("teses", [])
    print(f"Teses carregadas: {len(teses)}")

    manual_file = BDITA_DIR / "teses" / "manual_matches.json"
    manual = json.loads(manual_file.read_text()) if manual_file.exists() else {}

    mapping = build_advisor_mapping(
        teses, ["advisors", "co_advisors"], prof_index, manual
    )
    matched = sum(1 for v in mapping.values() if v)
    print(f"  Orientadores: {len(mapping)} únicos, {matched} mapeados a prof. da divisão")

    out_dir = BDITA_DIR / "teses"
    by_id_dir = out_dir / "by_id"
    out_dir.mkdir(parents=True, exist_ok=True)
    by_id_dir.mkdir(exist_ok=True)

    content_dir = BASE_DIR / "content" / "teses"
    content_dir.mkdir(parents=True, exist_ok=True)

    index_entries = []
    by_professor: dict = defaultdict(lambda: {
        "as_advisor": [], "as_coadvisor": [],
        "mestrado_count": 0, "doutorado_count": 0,
    })
    stats = {
        "total": 0, "mestrado": 0, "doutorado": 0,
        "by_year": defaultdict(int),
        "generated_at": datetime.now().isoformat(),
    }

    for tese in teses:
        num = tese.get("num_tese", "")
        if not num:
            continue

        advisors_raw = tese.get("advisors") or []
        co_advisors_raw = tese.get("co_advisors") or []

        advisors_out = [
            {"name": n, "professor_slug": mapping.get(n)}
            for n in advisors_raw
        ]
        co_advisors_out = [
            {"name": n, "professor_slug": mapping.get(n)}
            for n in co_advisors_raw
        ]

        course = tese.get("course", "")
        is_mestrado = "Mestrado" in course
        year = tese.get("year", "")

        record = {
            "num_tese": num,
            "type": "tese",
            "title": tese.get("title", ""),
            "author": tese.get("author", ""),
            "year": year,
            "course": course,
            "area": tese.get("area", ""),
            "program": tese.get("program", ""),
            "advisors": advisors_out,
            "co_advisors": co_advisors_out,
            "abstract": tese.get("abstract", ""),
            "subjects": tese.get("subjects", []),
            "defense_date": tese.get("defense_date", ""),
            "detail_url": tese.get("detail_url", ""),
            "pdf_url": tese.get("pdf_url", "") or tese.get("fulltext_url", ""),
        }
        (by_id_dir / f"{num}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        iea_slugs = [a["professor_slug"] for a in advisors_out + co_advisors_out if a["professor_slug"]]
        if iea_slugs:  # só inclui no índice se há orientador da divisão
            index_entries.append({
                "id": num,
                "t": record["title"][:200],
                "a": record["author"],
                "y": year,
                "c": "M" if is_mestrado else "D",
                "ad": [a["name"] for a in advisors_out][:3],
                "ap": iea_slugs[:3],
            })

        for j, adv in enumerate(advisors_raw):
            pid = mapping.get(adv)
            if pid:
                if j == 0:
                    by_professor[pid]["as_advisor"].append(num)
                    by_professor[pid]["mestrado_count" if is_mestrado else "doutorado_count"] += 1
                else:
                    by_professor[pid]["as_coadvisor"].append(num)
        for adv in co_advisors_raw:
            pid = mapping.get(adv)
            if pid:
                by_professor[pid]["as_coadvisor"].append(num)

        if iea_slugs:
            stats["total"] += 1
            stats["mestrado" if is_mestrado else "doutorado"] += 1
            stats["by_year"][year] += 1

        # content markdown
        t_dir = content_dir / num
        t_dir.mkdir(exist_ok=True)
        title_esc = record["title"].replace("\\", "\\\\").replace('"', '\\"')
        md = f'---\ntitle: "{title_esc}"\ntype: "teses"\nlayout: "single"\ntese_id: "{num}"\n---\n'
        (t_dir / "index.pt.md").write_text(md, encoding="utf-8")
        (t_dir / "index.en.md").write_text(md, encoding="utf-8")

    (out_dir / "lista.json").write_text(
        json.dumps(index_entries, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    stats["by_year"] = dict(stats["by_year"])
    (out_dir / "statistics.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "by_professor.json").write_text(
        json.dumps(dict(by_professor), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "manual_matches.json").write_text(
        json.dumps(manual, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"  Teses: {stats['total']} ({stats['mestrado']} M + {stats['doutorado']} D)")
    print(f"  Índice: {out_dir / 'index.json'}")
    print(f"  by_professor: {len(by_professor)} professores com orientações\n")


# ── generate TGs pages ────────────────────────────────────────────────────────

def generate_tgs(professors: dict, prof_index: dict):
    raw_file = BDITA_DIR / "tgs_raw.json"
    if not raw_file.exists():
        print(f"AVISO: {raw_file} não existe. Execute scrape_bdita_iea.py primeiro.")
        return

    data = json.loads(raw_file.read_text())
    tgs = data.get("tgs", [])
    print(f"TGs carregados: {len(tgs)}")

    manual_file = BDITA_DIR / "tgs" / "manual_matches.json"
    manual = json.loads(manual_file.read_text()) if manual_file.exists() else {}

    mapping = build_advisor_mapping(
        tgs, ["advisors", "co_advisors"], prof_index, manual
    )
    matched = sum(1 for v in mapping.values() if v)
    print(f"  Orientadores: {len(mapping)} únicos, {matched} mapeados a prof. da divisão")

    out_dir = BDITA_DIR / "tgs"
    by_id_dir = out_dir / "by_id"
    out_dir.mkdir(parents=True, exist_ok=True)
    by_id_dir.mkdir(exist_ok=True)

    content_dir = BASE_DIR / "content" / "tgs"
    content_dir.mkdir(parents=True, exist_ok=True)

    index_entries = []
    by_professor: dict = defaultdict(lambda: {"as_advisor": [], "as_coadvisor": []})
    stats = {
        "total": 0, "by_curso": defaultdict(int),
        "by_year": defaultdict(int),
        "generated_at": datetime.now().isoformat(),
    }

    for tg in tgs:
        num = tg.get("num_tg", "")
        if not num:
            continue

        advisors_raw = tg.get("advisors") or []
        co_advisors_raw = tg.get("co_advisors") or []

        advisors_out = [
            {"name": n, "professor_slug": mapping.get(n)}
            for n in advisors_raw
        ]
        co_advisors_out = [
            {"name": n, "professor_slug": mapping.get(n)}
            for n in co_advisors_raw
        ]

        curso = tg.get("curso", tg.get("course", ""))
        year = tg.get("year", "")

        record = {
            "num_tg": num,
            "type": "tg",
            "title": tg.get("title", ""),
            "author": tg.get("author", ""),
            "year": year,
            "curso": curso,
            "advisors": advisors_out,
            "co_advisors": co_advisors_out,
            "abstract": tg.get("abstract", ""),
            "subjects": tg.get("subjects", []),
            "detail_url": tg.get("detail_url", ""),
            "pdf_url": tg.get("pdf_url", "") or tg.get("fulltext_url", ""),
        }
        (by_id_dir / f"{num}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        has_iea_advisor = any(a["professor_slug"] for a in advisors_out + co_advisors_out)
        index_entries.append({
            "id": num,
            "t": record["title"][:200],
            "a": record["author"],
            "y": year,
            "cu": curso,
            "ad": [a["name"] for a in advisors_out][:2],
            "ap": [a["professor_slug"] for a in advisors_out if a["professor_slug"]][:2],
            "iea": has_iea_advisor,
        })

        for j, adv in enumerate(advisors_raw):
            pid = mapping.get(adv)
            if pid:
                if j == 0:
                    by_professor[pid]["as_advisor"].append(num)
                else:
                    by_professor[pid]["as_coadvisor"].append(num)
        for adv in co_advisors_raw:
            pid = mapping.get(adv)
            if pid:
                by_professor[pid]["as_coadvisor"].append(num)

        stats["total"] += 1
        stats["by_curso"][curso] += 1
        stats["by_year"][year] += 1

        # content markdown (apenas para TGs com orientador da divisão)
        if has_iea_advisor:
            t_dir = content_dir / num
            t_dir.mkdir(exist_ok=True)
            title_esc = record["title"].replace("\\", "\\\\").replace('"', '\\"')
            md = f'---\ntitle: "{title_esc}"\ntype: "tgs"\nlayout: "single"\ntg_id: "{num}"\n---\n'
            (t_dir / "index.pt.md").write_text(md, encoding="utf-8")
            (t_dir / "index.en.md").write_text(md, encoding="utf-8")

    (out_dir / "lista.json").write_text(
        json.dumps(index_entries, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    stats["by_curso"] = dict(stats["by_curso"])
    stats["by_year"] = dict(stats["by_year"])
    (out_dir / "statistics.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "by_professor.json").write_text(
        json.dumps(dict(by_professor), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "manual_matches.json").write_text(
        json.dumps(manual, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    iea_count = sum(1 for e in index_entries if e["iea"])
    print(f"  TGs: {stats['total']} total, {iea_count} com orientador da divisão")
    print(f"  by_professor: {len(by_professor)} professores com TGs\n")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--teses-only", action="store_true")
    parser.add_argument("--tgs-only", action="store_true")
    args = parser.parse_args()

    print("Carregando professores da IEA...")
    professors, prof_index = load_iea_professors()
    print(f"  {len(professors)} professores carregados\n")

    if not args.tgs_only:
        print("--- Gerando páginas de teses ---")
        generate_teses(professors, prof_index)

    if not args.teses_only:
        print("--- Gerando páginas de TGs ---")
        generate_tgs(professors, prof_index)

    print("Concluído.")


if __name__ == "__main__":
    main()

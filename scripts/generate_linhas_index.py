#!/usr/bin/env python3
"""
Gera data/linhas/index.json com publicações e docentes por linha de pesquisa.

Matching (qualquer dos critérios):
  1. keyword exato em authkeywords
  2. termo de título em title/abstract (apenas linhas com title_terms definido)
  3. subject_area (Scopus code) — APENAS se a linha tem poucos keywords E a pub
     não tem nenhum keyword preenchido (fallback para pubs sem keywords)
"""

import json
import yaml
from pathlib import Path

BASE = Path(__file__).parent.parent
LINHAS_YAML = BASE / "data" / "linhas_pesquisa.yaml"
PROFILES_DIR = BASE / "data" / "pessoal" / "profiles"
PUBS_DIR = BASE / "data" / "publications" / "by_eid"
IEA_SLUGS_FILE = BASE / "data" / "pessoal" / "iea_profiles.json"
OUT_DIR = BASE / "data" / "linhas"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Termos de busca em título/abstract por linha (para linhas com poucos keywords)
TITLE_TERMS = {
    "hipersonico-reentrada": [
        "hypersonic", "reentry", "re-entry", "reentrada",
        "thermal protection system", "ablat", "scramjet", "ramjet",
        "aerothermodynamic", "high enthalpy", "high-enthalpy",
        "shock wave boundary layer", "shock/boundary layer",
        "hypersonic boundary layer", "hypersonic flow",
        "reentry vehicle", "heat shield",
    ],
    "satelites": [
        "nanosatellite", "cubesat", "smallsat", "nanossat",
        "spacecraft attitude", "onboard computer",
        "eps subsystem", "adcs", "tt&c",
        "space mission simulator", "remote sensing satellite",
    ],
    "propulsao-foguetes": [
        "rocket motor", "rocket engine", "hybrid rocket", "solid rocket",
        "liquid rocket", "foguete", "propelente", "thrust chamber",
        "paraffin fuel", "htpb", "solid propellant", "hybrid propulsion",
        "launch vehicle propulsion", "turbopump", "lox-ethanol",
        "sounding rocket", "hydrazine thruster",
    ],
    "propulsao-aeronautica": [
        "turbofan engine performance", "gas turbine engine", "bypass ratio turbofan",
        "blade element method", "distributed propulsion", "propeller-wing interaction",
        "sustainable aviation fuel", "biojet fuel", "biojet production",
        "jet a-1", "aviation kerosene", "gas generator atomizer",
        "high bypass ratio turbofan",
    ],
    "propulsao-eletrica": [
        "electric aircraft", "hybrid-electric aircraft", "fuel cell aircraft",
        "fuel cell powered airplane", "fuel cell in a small aircraft",
        "liquid hydrogen tanks as energy carriers",
        "electric-fan propulsor", "urban air mobility", "aerial mobility of the future",
        "evtol", "optimal climb performance of electric",
        "electrification of aircraft", "aircraft propulsion electrification",
        "exergy assessment comparison of conventional and hybrid-electric",
        "exergoeconomic comparative analysis between conventional and hybrid electric",
        "regional aircraft with boundary layer ingestion",
        "regional aircraft with fuselage boundary layer ingestion",
    ],
    "mecanica-orbital": [
        "lunar mission", "three-body problem", "earth-moon", "garatéa", "garatéa-l",
        "orbital transfer", "ballistic capture", "weak stability boundary",
        "libration point", "halo orbit", "swing-by", "flyby",
        "asteroid orbit", "orbital resonance",
    ],
}


def load_iea_eid_map():
    iea_slugs = json.loads(IEA_SLUGS_FILE.read_text())["slugs"]
    eid_map = {}
    for slug in iea_slugs:
        prof_file = PROFILES_DIR / f"{slug}.json"
        if not prof_file.exists():
            continue
        prof = json.loads(prof_file.read_text())
        for pub_ref in prof.get("publicacoes") or []:
            pid = pub_ref.get("publication_id", "")
            eid_num = pid.split("-")[-1]
            if eid_num not in eid_map:
                eid_map[eid_num] = {"publication_id": pid, "professors": []}
            if slug not in eid_map[eid_num]["professors"]:
                eid_map[eid_num]["professors"].append(slug)
    return eid_map


def load_pub(eid_num):
    f = PUBS_DIR / f"{eid_num}.json"
    return json.loads(f.read_text()) if f.exists() else None


def match_pub(pub, linha_id, kw_set, area_set):
    authkws = [k.strip() for k in (pub.get("authkeywords") or [])]

    # 1. Keyword match
    if any(k in kw_set for k in authkws):
        return True

    # 2. Title/abstract term match
    terms = TITLE_TERMS.get(linha_id, [])
    if terms:
        text = " ".join([
            pub.get("title", "") or "",
            pub.get("abstract", "") or "",
        ]).lower()
        if any(t in text for t in terms):
            return True

    # 3. Subject area fallback (only for pubs with NO authkeywords)
    if not authkws and area_set:
        pub_areas = {sa.get("code", "") for sa in (pub.get("scopus", {}).get("subject_areas") or [])}
        if pub_areas & area_set:
            return True

    return False


def main():
    linhas_data = yaml.safe_load(LINHAS_YAML.read_text())["linhas"]
    eid_map = load_iea_eid_map()

    print(f"IEA publications: {len(eid_map)}\n")

    index = {}

    for linha_id, linha in linhas_data.items():
        kw_set = set(linha.get("keywords") or [])
        area_set = set(linha.get("subject_areas") or [])

        matched_pubs = []
        matched_profs = set()

        for eid_num, info in eid_map.items():
            pub = load_pub(eid_num)
            if not pub:
                continue
            if match_pub(pub, linha_id, kw_set, area_set):
                matched_pubs.append({
                    "publication_id": info["publication_id"],
                    "eid": eid_num,
                    "year": pub.get("year"),
                    "title": pub.get("title", ""),
                })
                for prof in info["professors"]:
                    matched_profs.add(prof)

        matched_pubs.sort(key=lambda x: x.get("year") or "0000", reverse=True)

        index[linha_id] = {
            "id": linha_id,
            "total_publicacoes": len(matched_pubs),
            "total_docentes": len(matched_profs),
            "docentes": sorted(matched_profs),
            "publicacoes": matched_pubs,
        }

        print(f"  {linha_id}: {len(matched_pubs):3d} pubs, {len(matched_profs):2d} docentes")

    out_file = OUT_DIR / "index.json"
    out_file.write_text(json.dumps(index, ensure_ascii=False, indent=2))
    print(f"\nSalvo: {out_file}")


if __name__ == "__main__":
    main()

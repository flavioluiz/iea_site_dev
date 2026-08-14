#!/usr/bin/env python3
"""
Associa TGs às linhas de pesquisa por matching de palavras-chave.

Matching (qualquer critério):
  1. keyword da linha em subjects do TG (case-insensitive)
  2. termo de título em title + abstract do TG (case-insensitive, substring)

Saída: data/linhas/tgs.json  {linha_id: [{num_tg, title, author, year, curso, advisor_slug?}]}
"""

from __future__ import annotations
import json
import re
import unicodedata
import yaml
from pathlib import Path

BASE = Path(__file__).parent.parent
TGS_FILE  = BASE / "data" / "bdita" / "tgs_raw.json"
TGS_LISTA = BASE / "data" / "bdita" / "tgs" / "lista.json"
LINHAS_YAML = BASE / "data" / "linhas_pesquisa.yaml"
OUT_FILE = BASE / "data" / "linhas" / "tgs.json"

# Termos de busca em título/abstract por linha (complementam os keywords do yaml)
# Termos buscados APENAS no título (mais precisos que abstract)
TITLE_TERMS: dict[str, list[str]] = {
    "aerodinamica-e-aeroacustica": [
        "aeroacoustic", "aeroacústic", "airfoil", "perfil alar", "aerofoil",
        "boundary layer separation", "separação de camada limite",
        "wind tunnel", "túnel de vento", "túnel aerodinâmico",
        "vortex shedding", "desprendimento de vórtice",
        "drag reduction", "redução de arrasto",
        "lift-to-drag", "coeficiente de sustentação",
        "wake interaction", "interação de esteira",
        "jet noise", "ruído de jato",
    ],
    "estabilidade-escoamentos": [
        "flow stability", "hydrodynamic stability",
        "laminar-turbulent transition", "transicao laminar", "transição laminar",
        "tollmien-schlichting", "kelvin-helmholtz",
        "boundary layer instability", "instabilidade de camada limite",
        "instabilidade da camada limite", "transition to turbulence",
        "estabilidade de fluxo", "instabilidade de kelvin",
        "camada limite laminar", "receptividade",
        "transicao a turbulencia", "transição à turbulência",
        "rayleigh-benard", "rayleigh criterion",
        "orr-sommerfeld", "absolute instability", "convective instability",
        "boundary layer transition", "transicao de camada limite",
        "turbulent boundary layer", "camada limite turbulenta",
        "streaky structures", "streamwise streak",
    ],
    "aeroelasticidade": [
        "aeroelastic", "aeroelástic", "flutter", "buffet",
        "gust response", "resposta a rajada", "dynamic stall",
        "limit cycle oscillation", "oscilação de ciclo limite",
        "wing vibration", "vibração de asa",
    ],
    "mecanica-voo-controle": [
        "flight mechanics", "mecânica do voo",
        "flight control", "controle de voo",
        "flight dynamics", "dinâmica de voo",
        "handling qualities", "qualidades de voo",
        "stability and control", "estabilidade e controle",
        "autopilot", "piloto automático",
        "flight simulation", "simulação de voo",
        "aircraft performance", "desempenho de aeronave",
        "aircraft navigation", "navegação de aeronave",
    ],
    "solidos-e-materiais": [
        "composite material", "material compósito", "fiber reinforced",
        "fibra de carbono", "carbon fiber", "glass fiber", "fibra de vidro",
        "fatigue analysis", "análise de fadiga", "fracture mechanics",
        "mecânica da fratura", "additive manufacturing", "manufatura aditiva",
        "3d printing", "impressão 3d", "metal alloy", "liga metálica",
        "titanium alloy", "liga de titânio", "aluminum alloy", "liga de alumínio",
        "creep analysis", "análise de fluência", "damage tolerance",
        "tolerância a dano", "corrosion", "corrosão",
        # portuguese subject terms common in BDITA
        "material composto", "materiais compostos", "materiais compositos",
        "fadiga", "fratura", "fluencia", "dano estrutural",
        "ensaio mecanico", "propriedades mecanicas", "resistencia mecanica",
        "tratamento termico", "tratamento superficial", "implantacao ionica",
        "liga de aluminio", "liga de titanio", "liga metalica",
        "fibra de carbono", "fibra de vidro", "resina epox",
        "laminado", "painel sandwich", "material ceramico",
        "manufatura aditiva", "impressao 3d", "sinterizacao",
        "tensao residual", "concentracao de tensao",
    ],
    "estruturas-aeroespaciais": [
        "aircraft structure", "estrutura de aeronave",
        "structural analysis", "análise estrutural",
        "fuselage", "fuselagem", "wing structure", "estrutura de asa",
        "buckling", "flambagem", "airframe", "structural test",
        "ensaio estrutural", "static test", "ensaio estático",
        "spar", "longarina", "rib structure",
    ],
    "metodos-numericos": [
        "computational fluid dynamics", "cfd simulation",
        "finite element method", "método dos elementos finitos",
        "finite volume method", "método dos volumes finitos",
        "numerical simulation", "simulação numérica",
        "numerical method", "método numérico",
        "high-order method", "método de alta ordem",
        "unstructured mesh", "malha não estruturada",
    ],
    "propulsao-foguetes": [
        "rocket motor", "motor foguete", "rocket engine", "motor-foguete",
        "solid propellant", "propelente sólido",
        "liquid propellant", "propelente líquido",
        "hybrid rocket", "foguete híbrido",
        "sounding rocket", "foguete de sondagem",
        "combustion chamber", "câmara de combustão",
        "nozzle design", "projeto de bocal",
        "thrust vector", "vetor de empuxo",
        "scramjet", "ramjet",
    ],
    "propulsao-aeronautica": [
        "turbofan", "turbojet", "turboprop", "turboshaft",
        "gas turbine engine", "motor turbina a gás",
        "jet engine", "motor a jato",
        "propeller design", "projeto de hélice",
        "compressor blade", "pá de compressor",
        "turbine blade", "pá de turbina",
        "engine performance", "desempenho de motor",
        "combustor design", "projeto de câmara de combustão",
    ],
    "propulsao-eletrica": [
        "electric propulsion", "propulsão elétrica",
        "electric aircraft", "aeronave elétrica",
        "hybrid-electric", "híbrido elétrico",
        "fuel cell", "célula combustível",
        "evtol", "urban air mobility", "mobilidade aérea urbana",
        "electric motor aircraft", "all-electric aircraft",
    ],
    "hipersonico-reentrada": [
        "hypersonic", "hipersônic", "hipersonico",
        "reentry", "reentrada",
        "thermal protection", "proteção térmica",
        "ablat", "scramjet",
        "aerothermodynamic", "aerotermodinâmic",
        "high enthalpy", "alta entalpia",
        "shock tunnel", "túnel de choque",
        "heat shield", "escudo térmico",
        "mach 5", "mach 6", "mach 7", "mach 8", "mach 9", "mach 10",
        "shock wave boundary layer",
    ],
    "mecanica-orbital": [
        "orbital mechanics", "mecânica orbital",
        "orbital transfer", "transferência orbital",
        "orbital maneuver", "manobra orbital",
        "astrodynamics", "astrodinâmica",
        "three-body problem", "problema de três corpos",
        "lagrange point", "ponto de lagrange",
        "trajectory optimization", "otimização de trajetória",
        "interplanetary", "interplanetário",
        "lunar mission", "missão lunar",
        "swing-by", "flyby",
    ],
    "satelites": [
        "cubesat", "nanosatellite", "nanossatélite", "smallsat",
        "microsatellite", "microssatélite",
        "attitude control", "controle de atitude",
        "attitude determination", "determinação de atitude",
        "onboard computer", "computador de bordo",
        "eps subsystem", "subsistema de potência",
        "satellite thermal control", "controle térmico de satélite",
        "satellite communication", "comunicação por satélite",
        "remote sensing satellite", "satélite de sensoriamento remoto",
        "space mission", "missão espacial",
    ],
    "projeto-aeroespacial": [
        "conceptual design of aircraft", "projeto conceitual de aeronave",
        "preliminary design of aircraft", "projeto preliminar de aeronave",
        "aircraft design", "projeto de aeronave",
        "systems engineering", "engenharia de sistemas",
        "multidisciplinary design optimization", "projeto multidisciplinar",
        "trade study", "estudo de compromisso",
        "mission requirements", "requisitos de missão",
        "payload design", "projeto de carga útil",
        "concurrent engineering", "engenharia concorrente",
        "design space exploration",
    ],
    "veiculo-lancador": [
        "veículo lançador", "veiculo lancador", "launch vehicle",
        "foguete lançador", "foguete lancador",
        "separação de estágios", "separacao de estagios", "stage separation",
        "trajetória de lançamento", "trajetoria de lancamento",
        "guiagem de foguete", "rocket guidance",
        "nanolançador", "nanolauncador", "nano-launcher",
        "VLS", "VLM",
        "estagiamento", "staging optimization",
        "veículo de lançamento", "veiculo de lancamento",
    ],
    "operacoes-sistemas-espaciais": [
        "range safety", "segurança de lançamento", "seguranca de lancamento",
        "probabilidade de impacto", "impact probability",
        "operações de lançamento", "operacoes de lancamento", "launch operations",
        "centro de lançamento", "centro de lancamento",
        "alcântara", "alcantara",
        "vigilância espacial", "vigilancia espacial", "space surveillance",
        "rastreio espacial", "space tracking", "rastreamento de satélite",
        "controle de missão", "controle de missao", "mission control",
        "detritos espaciais", "space debris",
        "operações espaciais", "operacoes espaciais", "space operations",
        "ciclo de vida espacial", "space system lifecycle",
        "centro espacial ita",
    ],
}


def normalize(s: str) -> str:
    n = unicodedata.normalize("NFKD", s)
    return "".join(c for c in n if not unicodedata.combining(c)).lower()


# Terms that, if found in subjects, should NOT match the given linha
# (prevents generic subjects like "estabilidade de fluxo" from matching unrelated TGs)
EXCLUDE_SUBJECTS: dict[str, list[str]] = {
    "estabilidade-escoamentos": [
        "reentrada", "reentry", "foguete", "propelente", "satellite", "satelite",
        "rayleigh-ritz", "flambagem", "buckling", "materiais compositos",
        "composite laminate", "delamina", "temperatura de chama", "combustao",
    ],
    "aerodinamica-e-aeroacustica": ["hipersonico", "mach 5", "mach 6", "mach 7", "mach 8", "mach 9"],
    "solidos-e-materiais": ["propelente solido", "solid propellant", "rocket propellant"],
}


def match_tg(tg: dict, linha_id: str, kw_set: set[str], title_terms: list[str]) -> bool:
    subjects_text = normalize(" | ".join(tg.get("subjects") or []))
    title = normalize(tg.get("title", "") or "")
    haystack = title + " | " + subjects_text

    # exclusion guard
    for excl in EXCLUDE_SUBJECTS.get(linha_id, []):
        if normalize(excl) in haystack:
            return False

    # 1. yaml keyword against subjects (substring)
    for kw in kw_set:
        if normalize(kw) in subjects_text:
            return True

    # 2. title_terms against title OR subjects
    if title_terms:
        if any(normalize(t) in haystack for t in title_terms):
            return True

    return False


def main():
    linhas_data = yaml.safe_load(LINHAS_YAML.read_text())["linhas"]
    tgs = json.loads(TGS_FILE.read_text())["tgs"]

    # load advisor slug map from lista.json (num_tg -> first ap slug)
    advisor_map: dict[str, str] = {}
    if TGS_LISTA.exists():
        for entry in json.loads(TGS_LISTA.read_text()):
            if entry.get("ap"):
                advisor_map[entry["id"]] = entry["ap"][0]

    print(f"TGs: {len(tgs)}  |  linhas: {len(linhas_data)}\n")

    result: dict[str, list] = {}

    for linha_id, linha in linhas_data.items():
        kw_set = set(linha.get("keywords") or [])
        title_terms = TITLE_TERMS.get(linha_id, [])

        matched = []
        for tg in tgs:
            if match_tg(tg, linha_id, kw_set, title_terms):
                matched.append({
                    "num_tg": tg["num_tg"],
                    "title": tg.get("title", ""),
                    "author": tg.get("author", ""),
                    "year": tg.get("year", ""),
                    "curso": tg.get("curso", tg.get("course", "")),
                    "advisor_slug": advisor_map.get(tg["num_tg"]),
                    "advisors": tg.get("advisors") or [],
                })

        matched.sort(key=lambda x: x.get("year") or "0000", reverse=True)
        result[linha_id] = matched
        print(f"  {linha_id}: {len(matched)} TGs")

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo: {OUT_FILE}")


if __name__ == "__main__":
    main()

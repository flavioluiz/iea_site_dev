#!/usr/bin/env python3
"""
Associa teses/dissertações orientadas por prof. da IEA às linhas de pesquisa.

Usa os mesmos critérios de generate_tgs_linhas.py:
  1. keyword da linha nos subjects da tese (substring, case-insensitive)
  2. termo de título em title + subjects

Saída: data/linhas/teses.json
  {linha_id: [{num_tese, title, author, year, course, advisors, advisor_slug}]}
"""

from __future__ import annotations
import json
import unicodedata
import yaml
from pathlib import Path

BASE        = Path(__file__).parent.parent
TESES_RAW   = BASE / "data" / "bdita" / "teses_raw.json"
TESES_LISTA = BASE / "data" / "bdita" / "teses" / "lista.json"
LINHAS_YAML = BASE / "data" / "linhas_pesquisa.yaml"
OUT_FILE    = BASE / "data" / "linhas" / "teses.json"

# reutiliza os mesmos title_terms do script de TGs
TITLE_TERMS: dict[str, list[str]] = {
    "aerodinamica-e-aeroacustica": [
        "aeroacoustic", "aeroacústic", "airfoil", "perfil alar", "aerofoil",
        "boundary layer separation", "wind tunnel", "túnel de vento",
        "vortex shedding", "drag reduction", "wake interaction",
        "jet noise", "ruído de jato", "trailing edge noise",
        "leading edge noise", "duct acoustics", "wavepacket",
        "turbulent jet", "subsonic jet", "supersonic jet",
    ],
    "estabilidade-escoamentos": [
        "flow stability", "hydrodynamic stability",
        "laminar-turbulent transition", "transicao laminar", "transição laminar",
        "tollmien-schlichting", "kelvin-helmholtz",
        "boundary layer instability", "instabilidade de camada limite",
        "instabilidade da camada limite", "transition to turbulence",
        "estabilidade de fluxo", "instabilidade de kelvin",
        "transicao a turbulencia", "transição à turbulência",
        "receptivity", "receptividade",
        "couette flow", "poiseuille flow",
        "rayleigh-benard", "rayleigh criterion", "rayleigh number",
        "orr-sommerfeld", "absolute instability", "convective instability",
        "instabilidade absoluta", "instabilidade convectiva",
        "boundary layer transition", "transicao de camada limite",
        "turbulent boundary layer", "camada limite turbulenta",
        "streaky structures", "streamwise streak",
        "free-stream turbulence",
    ],
    "aeroelasticidade": [
        "aeroelastic", "aeroelástic", "flutter", "buffet",
        "gust response", "resposta a rajada", "dynamic stall",
        "limit cycle oscillation", "oscilação de ciclo limite",
        "wing vibration", "vibração de asa",
        "panel flutter", "galloping", "vortex induced vibration",
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
        "trajectory optimization", "otimização de trajetória de voo",
        "unmanned aerial", "veículo aéreo não tripulado", "uav",
    ],
    "solidos-e-materiais": [
        "composite material", "material compósito", "fiber reinforced",
        "fibra de carbono", "carbon fiber", "glass fiber",
        "fatigue analysis", "análise de fadiga", "fracture mechanics",
        "mecânica da fratura", "additive manufacturing", "manufatura aditiva",
        "damage tolerance", "tolerância a dano", "corrosion", "corrosão",
        "material composto", "materiais compostos", "materiais compositos",
        "fadiga", "fratura", "fluencia", "dano estrutural",
        "propriedades mecanicas", "resistencia mecanica",
        "tratamento termico", "liga de aluminio", "liga de titanio",
        "laminado", "material ceramico", "tensao residual",
        "delamination", "delaminação", "crack propagation", "propagação de trinca",
    ],
    "estruturas-aeroespaciais": [
        "aircraft structure", "estrutura de aeronave",
        "structural analysis", "análise estrutural",
        "fuselage", "fuselagem", "wing structure", "estrutura de asa",
        "buckling", "flambagem", "airframe", "structural test",
        "ensaio estrutural", "static test", "ensaio estático",
        "spar", "longarina", "structural optimization",
        "otimização estrutural", "topology optimization",
    ],
    "metodos-numericos": [
        "computational fluid dynamics", "cfd simulation",
        "finite element method", "método dos elementos finitos",
        "finite volume method", "método dos volumes finitos",
        "numerical simulation", "simulação numérica",
        "numerical method", "método numérico",
        "high-order method", "método de alta ordem",
        "unstructured mesh", "malha não estruturada",
        "large eddy simulation", "les", "direct numerical simulation", "dns",
        "reynolds-averaged", "rans", "spectral method",
        "parabolized stability", "resolvent analysis",
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
        "scramjet", "ramjet", "rocket propulsion",
    ],
    "propulsao-aeronautica": [
        "turbofan", "turbojet", "turboprop", "turboshaft",
        "gas turbine engine", "motor turbina a gás",
        "jet engine", "motor a jato",
        "propeller design", "projeto de hélice",
        "compressor blade", "pá de compressor",
        "turbine blade", "pá de turbina",
        "engine performance", "desempenho de motor",
        "combustor design", "bypass ratio",
        "sustainable aviation fuel", "combustível de aviação sustentável",
    ],
    "propulsao-eletrica": [
        "electric propulsion", "propulsão elétrica",
        "electric aircraft", "aeronave elétrica",
        "hybrid-electric", "híbrido elétrico",
        "fuel cell", "célula combustível",
        "evtol", "urban air mobility", "mobilidade aérea urbana",
        "electric motor aircraft", "all-electric aircraft",
        "battery-powered aircraft",
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
        "shock wave boundary layer",
        "mach 5", "mach 6", "mach 7", "mach 8", "mach 9", "mach 10",
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
        "swing-by", "flyby", "ballistic capture",
    ],
    "satelites": [
        "cubesat", "nanosatellite", "nanossatélite", "smallsat",
        "microsatellite", "microssatélite",
        "attitude control", "controle de atitude",
        "attitude determination", "determinação de atitude",
        "onboard computer", "computador de bordo",
        "satellite thermal control", "controle térmico de satélite",
        "satellite communication", "comunicação por satélite",
        "remote sensing satellite", "satélite de sensoriamento remoto",
        "space mission", "missão espacial",
        "spacecraft design",
    ],
    "projeto-aeroespacial": [
        "conceptual design of aircraft", "projeto conceitual de aeronave",
        "preliminary design of aircraft", "projeto preliminar de aeronave",
        "aircraft design", "projeto de aeronave",
        "systems engineering", "engenharia de sistemas",
        "multidisciplinary design optimization",
        "trade study", "estudo de compromisso",
        "mission requirements", "requisitos de missão",
        "concurrent engineering", "design space exploration",
    ],
    "veiculo-lancador": [
        "veículo lançador", "veiculo lancador", "launch vehicle",
        "foguete lançador", "foguete lancador",
        "separação de estágios", "separacao de estagios", "stage separation",
        "trajetória de lançamento", "trajetoria de lancamento",
        "guiagem de foguete", "rocket guidance",
        "nanolançador", "nanolauncador", "nano-launcher",
        "VLS", "VLM",
        "estagiamento", "stagiamento", "staging optimization",
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
        "TT&C", "telemetria espacial",
        "controle de missão", "controle de missao", "mission control",
        "detritos espaciais", "space debris",
        "operações espaciais", "operacoes espaciais", "space operations",
        "ciclo de vida espacial", "space system lifecycle",
        "centro espacial ita", "CEI-ITA",
    ],
}

EXCLUDE_SUBJECTS: dict[str, list[str]] = {
    "estabilidade-escoamentos": [
        "reentrada", "reentry", "foguete", "propelente", "satellite", "satelite",
        "rayleigh-ritz", "flambagem", "buckling", "materiais compositos",
        "composite laminate", "delamina", "temperatura de chama", "combustao",
        "corpos flexiveis", "dinâmica de voo",
    ],
    "aerodinamica-e-aeroacustica": ["hipersonico", "mach 5", "mach 6", "mach 7", "mach 8", "mach 9"],
    "solidos-e-materiais": ["propelente solido", "solid propellant", "rocket propellant"],
}


def normalize(s: str) -> str:
    n = unicodedata.normalize("NFKD", s)
    return "".join(c for c in n if not unicodedata.combining(c)).lower()


def match_tese(tese: dict, linha_id: str, kw_set: set[str], title_terms: list[str]) -> bool:
    subjects_text = normalize(" | ".join(tese.get("subjects") or []))
    title         = normalize(tese.get("title", "") or "")
    haystack      = title + " | " + subjects_text

    for excl in EXCLUDE_SUBJECTS.get(linha_id, []):
        if normalize(excl) in haystack:
            return False

    for kw in kw_set:
        if normalize(kw) in subjects_text:
            return True

    if title_terms:
        if any(normalize(t) in haystack for t in title_terms):
            return True

    return False


def main():
    linhas_data = yaml.safe_load(LINHAS_YAML.read_text())["linhas"]

    # load all teses
    all_teses = json.loads(TESES_RAW.read_text())["teses"]

    # build set of IEA-supervised tese IDs + their advisor slug from lista.json
    lista = json.loads(TESES_LISTA.read_text())
    iea_map: dict[str, dict] = {}   # num_tese -> {advisor_slug, ap}
    for entry in lista:
        iea_map[entry["id"]] = {
            "advisor_slug": entry.get("ap", [None])[0],
            "advisors_display": entry.get("ad", []),
            "course_code": entry.get("c", ""),
        }

    # filter to IEA-supervised only
    iea_teses = [t for t in all_teses if t["num_tese"] in iea_map]
    print(f"Teses IEA: {len(iea_teses)} (de {len(all_teses)} total)  |  linhas: {len(linhas_data)}\n")

    result: dict[str, list] = {}

    for linha_id, linha in linhas_data.items():
        kw_set      = set(linha.get("keywords") or [])
        title_terms = TITLE_TERMS.get(linha_id, [])

        matched = []
        for tese in iea_teses:
            if match_tese(tese, linha_id, kw_set, title_terms):
                info = iea_map[tese["num_tese"]]
                matched.append({
                    "num_tese":     tese["num_tese"],
                    "title":        tese.get("title", ""),
                    "author":       tese.get("author", ""),
                    "year":         tese.get("year", ""),
                    "course":       tese.get("course", ""),
                    "course_code":  info["course_code"],
                    "advisor_slug": info["advisor_slug"],
                    "advisors":     tese.get("advisors") or [],
                })

        matched.sort(key=lambda x: x.get("year") or "0000", reverse=True)
        result[linha_id] = matched
        print(f"  {linha_id}: {len(matched)} teses")

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo: {OUT_FILE}")


if __name__ == "__main__":
    main()

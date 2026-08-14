"""
Extrai projetos de pesquisa do relatório Sucupira/CAPES (PDF).

Cada publicação no relatório tem um bloco "Contexto":
    Projeto de Pesquisa: <título — pode ocupar múltiplas linhas>

E uma tabela "Autores" com nome e categoria (Docente / Discente / ...).

Este script:
 1. Varre o PDF página a página (pdfplumber)
 2. Agrupa blocos de texto por registro de produção (delimitado por "Produção:")
 3. Dentro de cada bloco, extrai o projeto e os autores/docentes
 4. Agrega por título de projeto — unindo todos os Docentes associados
 5. Cruza Docentes com a lista IEA usando matching estrito (sem falsos positivos)

Saída: scripts/data/projetos_eam_raw.json
"""

import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import pdfplumber

PDF_PATH = Path("/Users/flavioribeiro/Documents/eam_docs/relatorio_dados_enviados_coleta_full.pdf")
OUT_JSON = Path("scripts/data/projetos_eam_raw.json")

# ---------------------------------------------------------------------------
# Docentes IEA
# ---------------------------------------------------------------------------
DOCENTES_IEA = [
    "Paulo Afonso de Oliveira Soviero",
    "André Valdetaro Gomes Cavalieri",
    "Tiago Barbosa de Araujo",
    "Vinicius Malatesta",
    "Vitor Gabriel Kleine",
    "André Fernando de Castro da Silva",
    "Filipe Ramos do Amaral",
    "Rodrigo Costa Moura",
    "Valéria Serrano Faillace Oliveira Leite",
    "Flávio Luiz Cardoso Ribeiro",
    "Maísa de Oliveira Terra",
    "Mauricio Andrés Varela Morales",
    "Antonio Bernardo Guimarães Neto",
    "Luiz Arthur Gagg Filho",
    "Guilherme Soares e Silva",
    "Cláudia Regina de Andrade",
    "Cristiane Aparecida Martins",
    "Pedro Teixeira Lacava",
    "Leonardo Henrique Gouvêa",
    "Flávio Luiz de Silva Bussamra",
    "Airton Nabarrete",
    "Maurício Vicente Donadon",
    "Mariano Andrés Arbelo",
    "Rafael Marques Lins",
    "Mauricio Pazini Brandão",
    "Adson Agrico de Paula",
    "Christopher Shneider Cerqueira",
    "Ronaldo Vieira Cruz",
    "Roberto Gil Annes da Silva",
    "Ney Rafael Sêcco",
    "Willer Gomes dos Santos",
    "Luis Eduardo Vergueiro Loures da Costa",
]

# Preposições / artigos a ignorar no matching
STOP = {"de", "da", "do", "dos", "das", "e", "a", "o", "em", "no", "na"}


def norm(s: str) -> str:
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower().strip()


def tokens_significativos(nome: str) -> list[str]:
    """Retorna tokens sem acentos e sem stop words."""
    return [t for t in norm(nome).split() if t not in STOP and len(t) > 1]


# Pré-computa tokens para cada docente IEA
IEA_TOKENS: list[tuple[str, list[str]]] = [
    (d, tokens_significativos(d)) for d in DOCENTES_IEA
]


def match_docente_iea(nome_raw: str) -> str | None:
    """
    Retorna o nome canônico do docente IEA se o nome_raw corresponder.

    Critérios (mais para menos restritivo):
    1. Match exato após normalização
    2. Todos os tokens significativos do docente presentes no nome dado
    3. ≥ 3 tokens significativos em comum (evita falsos positivos com
       sobrenomes comuns como "Silva", "Santos", "André")
    4. Nomes curtos (≤ 2 tokens significativos): ambos presentes
    """
    n = norm(nome_raw)
    # Filtra stop words do nome dado também (mesma lógica dos docentes)
    n_tokens = set(tokens_significativos(nome_raw))

    for canon, ctokens in IEA_TOKENS:
        if not ctokens:
            continue

        # 1. Exato
        if n == norm(canon):
            return canon

        common = set(ctokens) & n_tokens

        # 2. Todos os tokens do docente presentes no nome dado
        if len(common) == len(ctokens):
            return canon

        # 3. ≥ 3 tokens em comum (nomes com 3+ tokens significativos)
        if len(ctokens) >= 3 and len(common) >= 3:
            return canon

        # 4. Nome curto (≤ 2 tokens): ambos presentes
        if len(ctokens) <= 2 and len(common) == len(ctokens):
            return canon

    return None


# ---------------------------------------------------------------------------
# Extração e parsing do PDF
# ---------------------------------------------------------------------------

# Padrões de campo
RE_PRODUCAO  = re.compile(r"Produ[cç][aã]o:\s*(.+)", re.IGNORECASE)
RE_PROJETO   = re.compile(r"Projeto de Pesquisa:\s*(.*)", re.IGNORECASE)
RE_LINHA     = re.compile(r"Linha de Pesquisa:\s*(.*)", re.IGNORECASE)
RE_AREA      = re.compile(r"[Áa]rea de Concentra[cç][aã]o:\s*(.*)", re.IGNORECASE)

# Marcadores que indicam fim de um campo multilinhas
RE_FIELD_END = re.compile(
    r"^(Tipo:|Subtipo:|Natureza:|Autor|Detalhamento|Contexto|"
    r"Institui[cç][aã]o|Programa:|Ano da|A Produ|[Éé] um dos|Produ[cç][aã]o:|"
    r"Linha de Pesquisa:|[Áa]rea de Concentra[cç][aã]o:|\d{2}/\d{2}/\d{4})",
    re.IGNORECASE
)

# Linha de autor: "N NOME COMPLETO Categoria"
# pdfplumber normaliza espaços em tabelas → apenas 1 espaço entre colunas
RE_AUTOR = re.compile(
    r"^(\d+)\s+"
    r"(.+?)\s+"
    r"(Docente|Egresso|P[oó]s-?Doc|Discente|Participante Externo|Sem categoria)"
    r"\s*$"
)


def extract_full_text(pdf_path: Path) -> str:
    """Extrai texto completo do PDF (todas as páginas concatenadas)."""
    parts = []
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        batch = 50
        for start in range(0, total, batch):
            end = min(start + batch, total)
            for i in range(start, end):
                text = pdf.pages[i].extract_text() or ""
                parts.append(text)
            print(f"  Páginas {start+1}–{end} / {total}")
    return "\n".join(parts)


def parse_text(full_text: str) -> list[dict]:
    """
    Divide o texto em blocos de produção e extrai campos relevantes.
    Retorna lista de registros com: titulo_producao, projeto, linha, area,
    docentes_raw (lista de nomes com categoria Docente).
    """
    records: list[dict] = []
    current: dict | None = None

    # Estado do campo multilinhas sendo lido
    ml_field: str | None = None   # "projeto" | "linha" | "area"
    ml_buffer: list[str] = []

    def flush_multiline():
        nonlocal ml_field, ml_buffer
        if ml_field and current and ml_buffer:
            val = " ".join(ml_buffer).strip()
            # Remove artefatos de paginação (número de página sozinho)
            val = re.sub(r"\s+\d+\s*$", "", val).strip()
            if val and val != "-":
                current[ml_field] = val
        ml_field = None
        ml_buffer = []

    lines = full_text.splitlines()

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        # --- Nova produção ------------------------------------------------
        m = RE_PRODUCAO.match(line)
        if m:
            flush_multiline()
            if current:
                records.append(current)
            current = {
                "titulo_producao": m.group(1).strip(),
                "projeto": "",
                "linha": "",
                "area": "",
                "docentes_raw": [],
            }
            continue

        if current is None:
            continue

        # --- Fim de campo multilinhas se encontrarmos marcador de campo ---
        if ml_field and RE_FIELD_END.match(line):
            flush_multiline()

        # --- Projeto de Pesquisa ------------------------------------------
        m = RE_PROJETO.match(line)
        if m:
            flush_multiline()
            val = m.group(1).strip()
            if val and val != "-":
                current["projeto"] = val
                # Pode continuar na próxima linha
                ml_field = "projeto"
                ml_buffer = [val]
            else:
                ml_field = "projeto"
                ml_buffer = []
            continue

        # --- Linha de Pesquisa -------------------------------------------
        m = RE_LINHA.match(line)
        if m:
            flush_multiline()
            val = m.group(1).strip()
            current["linha"] = val
            ml_field = "linha"
            ml_buffer = [val] if val else []
            continue

        # --- Área de Concentração ----------------------------------------
        m = RE_AREA.match(line)
        if m:
            flush_multiline()
            val = m.group(1).strip()
            current["area"] = val
            ml_field = "area"
            ml_buffer = [val] if val else []
            continue

        # --- Continuação de campo multilinhas ----------------------------
        if ml_field:
            # Linha de continuação válida: não começa por campo conhecido,
            # não é linha de autor, não é número de página sozinho
            if not RE_FIELD_END.match(line) and not RE_AUTOR.match(line):
                if not re.match(r"^\d+\s*$", line):  # número de página
                    ml_buffer.append(line)
                    continue
            else:
                flush_multiline()

        # --- Linha de autor ----------------------------------------------
        m = RE_AUTOR.match(line)
        if m:
            nome = m.group(2).strip()
            cat  = m.group(3).strip()
            if cat == "Docente":
                current["docentes_raw"].append(nome)

    flush_multiline()
    if current:
        records.append(current)

    return records


def aggregate_projects(records: list[dict]) -> list[dict]:
    """
    Agrega registros por título de projeto.
    Para cada projeto: coleta docentes IEA, docentes externos, produções.
    """
    proj: dict[str, dict] = {}

    for r in records:
        titulo = r["projeto"].strip()
        if not titulo or titulo == "-":
            continue

        if titulo not in proj:
            proj[titulo] = {
                "titulo": titulo,
                "linha": r["linha"],
                "area": r["area"],
                "financiador": "",
                "periodo": "",
                "descricao": "",
                "docentes": [],          # todos os docentes associados
                "participantes_iea": [], # apenas IEA
                "producoes": [],
            }

        p = proj[titulo]

        # Atualiza linha/área se ainda vazio
        if not p["linha"] and r["linha"]:
            p["linha"] = r["linha"]
        if not p["area"] and r["area"]:
            p["area"] = r["area"]

        # Docentes do registro
        for nome_raw in r["docentes_raw"]:
            if nome_raw not in p["docentes"]:
                p["docentes"].append(nome_raw)
            iea = match_docente_iea(nome_raw)
            if iea and iea not in p["participantes_iea"]:
                p["participantes_iea"].append(iea)

        # Produção
        prod = r["titulo_producao"]
        if prod and prod not in p["producoes"]:
            p["producoes"].append(prod)

    return list(proj.values())


def main():
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    print(f"PDF: {PDF_PATH}")
    print("Extraindo texto...")
    full_text = extract_full_text(PDF_PATH)

    print("Parseando registros...")
    records = parse_text(full_text)
    print(f"  Produções encontradas: {len(records)}")

    projetos = aggregate_projects(records)
    com_iea = [p for p in projetos if p["participantes_iea"]]
    sem_iea  = [p for p in projetos if not p["participantes_iea"]]

    print(f"  Projetos únicos: {len(projetos)}")
    print(f"  Com docentes IEA: {len(com_iea)}")
    print(f"  Sem docentes IEA: {len(sem_iea)}")

    data = {
        "total": len(projetos),
        "total_com_iea": len(com_iea),
        "projetos": projetos,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nSalvo: {OUT_JSON}")

    # Relatório detalhado
    print("\n=== PROJETOS COM DOCENTES IEA ===\n")
    for p in sorted(com_iea, key=lambda x: x["titulo"]):
        print(f"Título : {p['titulo']}")
        print(f"Linha  : {p['linha']}")
        print(f"Área   : {p['area']}")
        print(f"Docentes IEA: {', '.join(p['participantes_iea'])}")
        print(f"Todos docentes: {', '.join(p['docentes'])}")
        print(f"Produções ({len(p['producoes'])}): {'; '.join(p['producoes'][:3])}{'...' if len(p['producoes']) > 3 else ''}")
        print()

    # Contagem por docente
    contagem: dict[str, int] = {}
    for p in com_iea:
        for d in p["participantes_iea"]:
            contagem[d] = contagem.get(d, 0) + 1
    print("=== CONTAGEM POR DOCENTE IEA ===")
    for d, n in sorted(contagem.items(), key=lambda x: -x[1]):
        print(f"  {n:2d}  {d}")


if __name__ == "__main__":
    main()

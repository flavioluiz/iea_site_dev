"""
Extração de projetos de pesquisa do relatório EAM (PDF).

Entrada:  /Users/flavioribeiro/Documents/eam_docs/relatorio_dados_enviados_coleta_full.pdf
Saída:    scripts/data/projetos_eam_raw.json   — todos os projetos extraídos
          scripts/data/projetos_iea.json        — apenas projetos com docentes da IEA
          scripts/data/projetos_iea.yaml        — versão YAML pronta para data/projetos.yaml

Uso:
    python3 scripts/extract_projetos_pdf.py
"""

import json
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Docentes IEA — para cruzamento de participantes
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

# Índice de sobrenomes para matching rápido
SOBRENOMES_IEA = {
    nome.split()[-1].lower(): nome for nome in DOCENTES_IEA
}


def normaliza(texto: str) -> str:
    import unicodedata
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode().lower()


def encontra_docentes_iea(participantes: list[str]) -> list[str]:
    """Cruza lista de participantes com docentes IEA."""
    encontrados = []
    for part in participantes:
        part_norm = normaliza(part)
        for docente in DOCENTES_IEA:
            # Match por sobrenome + pelo menos um nome do meio/primeiro
            partes_doc = [normaliza(p) for p in docente.split()]
            if all(p in part_norm for p in partes_doc[-1:]) and any(
                p in part_norm for p in partes_doc[:-1]
            ):
                encontrados.append(docente)
                break
            # Match direto
            if normaliza(docente) in part_norm or part_norm in normaliza(docente):
                if docente not in encontrados:
                    encontrados.append(docente)
                break
    return encontrados


def gera_slug(titulo: str) -> str:
    import unicodedata, re
    slug = unicodedata.normalize("NFD", titulo).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9\s-]", "", slug).strip().lower()
    slug = re.sub(r"\s+", "-", slug)
    return slug[:60]


def projetos_para_yaml(projetos: list[dict]) -> str:
    """Gera YAML compatível com data/projetos.yaml do Hugo."""
    linhas = ["projetos:"]
    for p in projetos:
        slug = gera_slug(p["titulo"])
        linhas.append(f"  {slug}:")
        linhas.append(f'    id: "{slug}"')
        linhas.append(f'    titulo_pt: "{p["titulo"]}"')
        linhas.append(f'    titulo_en: ""')
        # Departamento do primeiro docente IEA
        linhas.append(f'    departamento: ""')
        linhas.append(f'    financiador: "{p.get("financiador", "")}"')
        linhas.append(f'    valor: ""')
        linhas.append(f'    periodo: "{p.get("periodo", "")}"')
        linhas.append(f'    status: "em_andamento"')
        linhas.append(f'    tema: ""')
        # Docentes IEA (deduplicated)
        docentes_uniq = list(dict.fromkeys(p.get("participantes_iea", [])))
        if docentes_uniq:
            linhas.append(f'    docentes_iea:')
            for d in docentes_uniq:
                linhas.append(f'      - "{d}"')
        # Todos os docentes associados
        if p.get("docentes"):
            linhas.append(f'    docentes:')
            for d in p["docentes"]:
                linhas.append(f'      - "{d}"')
        descricao = p.get("descricao", "").replace('"', "'").replace("\n", " ")
        linhas.append(f'    descricao_pt: "{descricao}"')
        linhas.append(f'    descricao_en: ""')
        linhas.append("")
    return "\n".join(linhas)


def main():
    pdf_path = Path("/Users/flavioribeiro/Documents/eam_docs/relatorio_dados_enviados_coleta_full.pdf")
    raw_json = Path("scripts/data/projetos_eam_raw.json")
    iea_json = Path("scripts/data/projetos_iea.json")
    iea_yaml = Path("scripts/data/projetos_iea.yaml")

    if not raw_json.exists():
        print("ERRO: scripts/data/projetos_eam_raw.json não encontrado.")
        print("Execute primeiro o agente de extração ou rode manualmente com Claude.")
        return

    with open(raw_json) as f:
        data = json.load(f)

    projetos = data.get("projetos", [])
    print(f"Total extraído: {len(projetos)} projetos")

    # Usa participantes_iea já preenchidos pelo extrator (extrair_projetos_pdf.py)
    # Filtra apenas projetos com docentes IEA confirmados
    com_iea = [p for p in projetos if p.get("participantes_iea")]

    print(f"Com participação IEA: {len(com_iea)} projetos")

    # Salva JSON filtrado
    with open(iea_json, "w") as f:
        json.dump({"projetos": com_iea, "total": len(com_iea)}, f, ensure_ascii=False, indent=2)
    print(f"Salvo: {iea_json}")

    # Salva YAML para Hugo
    yaml_content = projetos_para_yaml(com_iea)
    with open(iea_yaml, "w") as f:
        f.write(yaml_content)
    print(f"Salvo: {iea_yaml}")

    # Resumo por docente IEA
    print("\n--- Projetos por docente IEA ---")
    contagem = {}
    for p in com_iea:
        for d in p["participantes_iea"]:
            contagem[d] = contagem.get(d, 0) + 1
    for docente, n in sorted(contagem.items(), key=lambda x: -x[1]):
        print(f"  {n:2d}  {docente}")


if __name__ == "__main__":
    main()

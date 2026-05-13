import pybliometrics

# inicialização programática (não precisa nem de arquivo de config)
pybliometrics.init(
    keys=["e8917d664a72244e7ed90ce9e5ecc082"],       # lista, pode ter mais de uma
    inst_tokens=[None],              # ou ["SEU_INST_TOKEN"] se tiver
)

import json
from pybliometrics.scopus import AuthorRetrieval, AbstractRetrieval

def get_author_data(scopus_author_id: str) -> tuple[AuthorRetrieval, dict]:
    # ENHANCED: mais metadados disponíveis
    au = AuthorRetrieval(scopus_author_id, view="ENHANCED")

    # Afiliações atuais
    afiliacoes_atuais = []
    if au.affiliation_current:
        for aff in au.affiliation_current:
            afiliacoes_atuais.append({
                "id": getattr(aff, "id", None),
                "nome": getattr(aff, "afdispname", None),
                "cidade": getattr(aff, "city", None),
                "pais": getattr(aff, "country", None),
            })

    # Afiliações históricas
    afiliacoes_historicas = []
    if au.affiliation_history:
        for aff in au.affiliation_history:
            afiliacoes_historicas.append({
                "id": getattr(aff, "id", None),
                "nome": getattr(aff, "afdispname", None),
                "cidade": getattr(aff, "city", None),
                "pais": getattr(aff, "country", None),
            })

    # Áreas de classificação
    classificacoes = []
    if au.classificationgroup:
        for sg_id, n_docs in au.classificationgroup:
            classificacoes.append({
                "subject_group_id": sg_id,
                "num_documentos": n_docs,
            })

    dados_autor = {
        # Identificação
        "author_id": au.identifier,
        "eid": au.eid,
        "nome_indexado": au.indexed_name,
        "nome": au.given_name,
        "sobrenome": au.surname,
        "orcid": au.orcid,

        # IDs alternativos
        "alias": au.alias,
        "historical_identifier": au.historical_identifier,

        # Métricas
        "h_index": au.h_index,
        "total_documentos": au.document_count,
        "total_citacoes": au.citation_count,
        "cited_by_count": au.cited_by_count,
        "intervalo_publicacao": au.publication_range,

        # Coautores / links
        "coauthor_count": au.coauthor_count,
        "coauthor_link": au.coauthor_link,
        "link_scopus": au.scopus_author_link,
        "self_link": au.self_link,

        # Datas / assuntos
        "data_criacao_registro": au.date_created,
        "classificacao_assuntos": classificacoes,

        # Afiliações
        "afiliacoes_atuais": afiliacoes_atuais,
        "afiliacoes_historicas": afiliacoes_historicas,
    }

    return au, dados_autor


def get_publications_data(au: AuthorRetrieval,
                          fetch_abstract: bool = True) -> list[dict]:
    """
    Retorna uma lista de dicionários, um por publicação.
    Se fetch_abstract=True, usa AbstractRetrieval para pegar resumo, keywords etc.
    """
    docs = au.get_documents() or []
    pubs = []

    for d in docs:
        cover_date = getattr(d, "coverDate", None)
        ano = cover_date.split("-")[0] if cover_date else None

        pub = {
            # Identificação básica
            "eid": getattr(d, "eid", None),
            "doi": getattr(d, "doi", None),
            "pii": getattr(d, "pii", None),
            "pubmed_id": getattr(d, "pubmed_id", None),

            # Metadados centrais
            "title": getattr(d, "title", None),
            "subtype": getattr(d, "subtype", None),
            "subtype_description": getattr(d, "subtypeDescription", None),
            "year": ano,
            "date": cover_date,
            "display_date": getattr(d, "coverDisplayDate", None),
            "journal": getattr(d, "publicationName", None),
            "aggregation_type": getattr(d, "aggregationType", None),

            # Autores / afiliação
            "author_count": getattr(d, "author_count", None),
            "author_names": getattr(d, "author_names", None),
            "author_ids": getattr(d, "author_ids", None),
            "author_afids": getattr(d, "author_afids", None),
            "affilname": getattr(d, "affilname", None),
            "affiliation_city": getattr(d, "affiliation_city", None),
            "affiliation_country": getattr(d, "affiliation_country", None),

            # Fonte (journal / proceedings)
            "issn": getattr(d, "issn", None),
            "eissn": getattr(d, "eIssn", None),
            "source_id": getattr(d, "source_id", None),

            # Volume / páginas
            "volume": getattr(d, "volume", None),
            "issue": getattr(d, "issueIdentifier", None),
            "article_number": getattr(d, "article_number", None),
            "page_range": getattr(d, "pageRange", None),

            # Citações
            "cited_by": getattr(d, "citedby_count", None),
        }

        # Enriquecer com AbstractRetrieval (resumo, keywords, etc.)
        if fetch_abstract and pub["eid"]:
            try:
                ab = AbstractRetrieval(pub["eid"], view="FULL")
                # Palavras-chave (authkeywords pode ser lista ou None)
                keywords = ab.authkeywords
                # Áreas de assunto (lista de namedtuples) → lista de dicts simples
                subject_areas = []
                if ab.subject_areas:
                    for sa in ab.subject_areas:
                        # a estrutura típica é algo como (area_code, abbrev, description)
                        subject_areas.append({
                            "code": getattr(sa, "area", getattr(sa, "code", None)),
                            "abbrev": getattr(sa, "abbreviation", None),
                            "name": getattr(sa, "description", None),
                        })

                refs = ab.references or []

                pub.update({
                    "abstract": ab.abstract,
                    "authkeywords": keywords,
                    "subject_areas": subject_areas,
                    "references_count": len(refs),
                    "scopus_link": ab.scopus_link,
                })
            except Exception as e:
                # Em caso de erro na AbstractRetrieval, só registra a mensagem
                pub["abstract_error"] = str(e)

        pubs.append(pub)

    return pubs


def export_author_and_pubs_to_json(author_id: str,
                                   filename: str | None = None,
                                   fetch_abstract: bool = True) -> str:
    au, dados_autor = get_author_data(author_id)
    publications = get_publications_data(au, fetch_abstract=fetch_abstract)

    data = {
        "author": dados_autor,
        "publications": publications,
    }

    if filename is None:
        filename = f"scopus_author_{author_id}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return filename


if __name__ == "__main__":
    # Coloque aqui o Scopus Author ID desejado
    author_id = "46461159000"
    output_file = export_author_and_pubs_to_json(author_id)
    print(f"Arquivo gerado: {output_file}")
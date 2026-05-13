import pybliometrics

# inicialização programática (não precisa nem de arquivo de config)
pybliometrics.init(
    keys=["e8917d664a72244e7ed90ce9e5ecc082"],       # lista, pode ter mais de uma
    inst_tokens=[None],              # ou ["SEU_INST_TOKEN"] se tiver
)
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pybliometrics.scopus import AuthorSearch
import json
import unicodedata
from typing import List, Dict, Any

AFFILIATION_VARIANTS = [
    "Instituto Tecnologico de Aeronautica",
    "Instituto Tecnológico de Aeronáutica",
]

# Nome “normalizado” que queremos encontrar
ITA_NORM = "instituto tecnologico de aeronautica"


def normalize(s: str | None) -> str:
    if not s:
        return ""
    # remove acentos e joga pra minúsculo
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s.lower().strip()


def is_current_ita_affiliation(entry: Dict[str, Any]) -> tuple[bool, Dict[str, Any] | None]:
    """
    Verifica se alguma 'affiliation-current' do entry é o ITA.
    Retorna (True, afil_ita_dict) se encontrar; caso contrário (False, None).

    'affiliation-current' pode ser dict ou lista de dicts.
    """
    aff_cur = entry.get("affiliation-current")
    if not aff_cur:
        return False, None

    # pode vir como dict único ou como lista
    if isinstance(aff_cur, dict):
        aff_list = [aff_cur]
    elif isinstance(aff_cur, list):
        aff_list = aff_cur
    else:
        return False, None

    for aff in aff_list:
        nome = aff.get("affiliation-name")
        if normalize(nome).find(ITA_NORM) != -1:
            return True, aff

    return False, None


def extract_subject_areas(entry: Dict[str, Any]):
    sa = entry.get("subject-area")
    if not sa:
        return None

    areas: list[str] = []

    if isinstance(sa, str):
        return [sa]

    if isinstance(sa, dict):
        areas.append(sa.get("$") or sa.get("@abbrev") or str(sa))
        return areas

    if isinstance(sa, list):
        for x in sa:
            if isinstance(x, dict):
                areas.append(x.get("$") or x.get("@abbrev") or str(x))
            else:
                areas.append(str(x))
        return areas or None

    return [str(sa)]


def find_authors_by_affiliations(
    affiliation_names: List[str] = AFFILIATION_VARIANTS,
    refresh: bool | int = False,
) -> List[Dict[str, Any]]:
    authors_by_id: Dict[int, Dict[str, Any]] = {}

    for aff in affiliation_names:
        query = f'AFFIL("{aff}")'
        print(f"Rodando AuthorSearch com query: {query}")
        s = AuthorSearch(query, refresh=refresh)

        for entry in (s._json or []):
            # filtra pelo ITA na AFILIAÇÃO ATUAL
            ok, aff_ita = is_current_ita_affiliation(entry)
            if not ok:
                continue

            raw_id = entry.get("dc:identifier")
            if not raw_id:
                continue
            try:
                author_id = int(str(raw_id).split(":")[-1])
            except ValueError:
                continue

            pref = entry.get("preferred-name", {}) or {}
            orcid = entry.get("orcid")
            subject_areas = extract_subject_areas(entry)

            record = {
                "author_id": author_id,
                "orcid": orcid,
                "indexed_name": pref.get("indexed-name"),
                "surname": pref.get("surname"),
                "given_name": pref.get("given-name"),
                "initials": pref.get("initials"),

                "affiliation_id": aff_ita.get("affiliation-id") if aff_ita else None,
                "affiliation_name": aff_ita.get("affiliation-name") if aff_ita else None,
                "affiliation_city": aff_ita.get("affiliation-city") if aff_ita else None,
                "affiliation_country": aff_ita.get("affiliation-country") if aff_ita else None,

                "document_count": entry.get("document-count"),
                "subject_areas": subject_areas,
            }

            if author_id in authors_by_id:
                existing = authors_by_id[author_id]
                if not existing.get("orcid") and orcid:
                    existing["orcid"] = orcid
                if subject_areas:
                    sa_ant = set(existing.get("subject_areas") or [])
                    sa_nov = set(subject_areas)
                    existing["subject_areas"] = sorted(sa_ant.union(sa_nov))
            else:
                authors_by_id[author_id] = record

    return list(authors_by_id.values())


def main():
    autores = find_authors_by_affiliations(refresh=False)

    autores_com_orcid = [a for a in autores if a.get("orcid")]

    print(f"Total de autores (afiliação atual ITA): {len(autores)}")
    print(f"Total com ORCID: {len(autores_com_orcid)}")

    with open("ita_authors_orcid.json", "w", encoding="utf-8") as f:
        json.dump(autores_com_orcid, f, indent=2, ensure_ascii=False)

    with open("ita_authors_all.json", "w", encoding="utf-8") as f:
        json.dump(autores, f, indent=2, ensure_ascii=False)

    print("Arquivos gravados: ita_authors_orcid.json e ita_authors_all.json")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Normalize private Scopus staging into the restricted public data contract."""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shutil
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from report import render_report, semantic


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PREVIOUS = ROOT / "data" / "generated" / "scopus"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def first(value: Any) -> dict[str, Any]:
    if isinstance(value, list):
        return value[0] if value else {}
    return value if isinstance(value, dict) else {}


def author_metrics(payloads: list[dict[str, Any]], generated_date: str) -> dict[str, Any]:
    responses = []
    for payload in payloads:
        responses.extend(payload.get("author-retrieval-response", []))
    h_index = max((int(item.get("h-index", 0) or 0) for item in responses), default=0)
    cores = [item.get("coredata", {}) for item in responses]
    return {
        "h_index": h_index,
        "citacoes": sum(int(item.get("citation-count", 0) or 0) for item in cores),
        "cited_by_count": sum(int(item.get("cited-by-count", 0) or 0) for item in cores),
        "artigos": sum(int(item.get("document-count", 0) or 0) for item in cores),
        "coauthor_count": max((int(item.get("coauthor-count", 0) or 0) for item in responses), default=0),
        "publication_range": [], "ultima_atualizacao": generated_date, "data_source": "scopus",
    }


def normalize_authors(entry: dict[str, Any], professor_id: str, professor_name: str, author_ids: set[str]) -> list[dict[str, Any]]:
    raw_authors = entry.get("author") or []
    if not isinstance(raw_authors, list):
        raw_authors = [raw_authors]
    result = []
    for raw in raw_authors:
        scopus_id = str(raw.get("authid") or "") or None
        is_professor = bool(scopus_id and scopus_id in author_ids)
        result.append({
            "name": raw.get("authname") or raw.get("surname") or "",
            "scopus_id": scopus_id, "affiliation": None,
            "is_eam_professor": is_professor, "eam_professor_id": professor_id if is_professor else None,
        })
    if not result:
        result.append({"name": professor_name, "scopus_id": next(iter(author_ids), None), "affiliation": None, "is_eam_professor": True, "eam_professor_id": professor_id})
    return result


def normalize_entry(entry: dict[str, Any], professor_id: str, professor_name: str, author_ids: set[str], timestamp: str) -> dict[str, Any]:
    eid = entry.get("eid", "")
    if not eid.startswith("2-s2.0-"):
        raise ValueError(f"EID inválido: {eid!r}")
    date = entry.get("prism:coverDate") or ""
    authors = normalize_authors(entry, professor_id, professor_name, author_ids)
    coauthors = sorted({item["eam_professor_id"] for item in authors if item["eam_professor_id"]})
    return {
        "publication_id": eid, "eid": eid, "doi": entry.get("prism:doi") or None,
        "pii": None, "pubmed_id": None, "title": entry.get("dc:title") or "Sem título",
        "year": date[:4], "date": date, "type": "article", "subtype": entry.get("subtype") or "",
        "journal": {"name": entry.get("prism:publicationName") or None, "issn": None, "eissn": None, "volume": None, "issue": None, "pages": None, "article_number": None},
        "authors": authors, "eam_coauthors": coauthors,
        "scopus": {"citations": int(entry.get("citedby-count", 0) or 0), "references_count": None, "scopus_link": entry.get("prism:url") or None},
        "metadata": {"source": "scopus", "last_updated": timestamp, "data_quality_score": 70},
    }


def merge_publication(existing: dict[str, Any] | None, candidate: dict[str, Any]) -> dict[str, Any]:
    if not existing:
        return candidate
    merged = copy.deepcopy(existing)
    for key in ("publication_id", "eid", "doi", "title", "year", "date", "type", "subtype"):
        merged[key] = candidate[key]
    journal = merged.setdefault("journal", {})
    for key, value in candidate.get("journal", {}).items():
        if value not in (None, ""):
            journal[key] = value
    for key, value in candidate["scopus"].items():
        if value is not None:
            merged["scopus"][key] = value
    merged["metadata"].update(candidate["metadata"])
    authors: dict[tuple[str | None, str], dict[str, Any]] = {}
    for author in merged.get("authors", []) + candidate.get("authors", []):
        key = (author.get("scopus_id"), author.get("name", ""))
        previous = authors.get(key, {})
        authors[key] = {**previous, **author}
        if previous.get("eam_professor_id") and not author.get("eam_professor_id"):
            authors[key]["is_eam_professor"] = True
            authors[key]["eam_professor_id"] = previous["eam_professor_id"]
    merged["authors"] = list(authors.values())
    merged["eam_coauthors"] = sorted(
        {
            author["eam_professor_id"]
            for author in merged["authors"]
            if author.get("eam_professor_id")
        }
    )
    return merged


def normalized_text(value: Any) -> str:
    decomposed = unicodedata.normalize("NFKD", str(value or ""))
    ascii_value = decomposed.encode("ascii", "ignore").decode("ascii").casefold()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", ascii_value).split())


def normalized_doi(value: Any) -> str:
    doi = str(value or "").strip().casefold()
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi)
    return doi.rstrip(". ")


def duplicate_key(publication: dict[str, Any]) -> tuple[str, ...]:
    """Return the conservative cross-EID identity documented in the runbook."""
    doi = normalized_doi(publication.get("doi"))
    if doi:
        return ("doi", doi)
    title = normalized_text(publication.get("title"))
    year = str(publication.get("year") or "")
    journal = normalized_text(publication.get("journal", {}).get("name"))
    if title and year and journal:
        return ("title-year-journal", title, year, journal)
    return ("eid", str(publication.get("eid") or ""))


def merge_duplicate_publication(
    primary: dict[str, Any], duplicate: dict[str, Any]
) -> dict[str, Any]:
    """Merge authors/metrics while retaining the deterministic primary EID."""
    identity = {key: primary.get(key) for key in ("publication_id", "eid")}
    preferred = {
        key: primary.get(key)
        for key in ("doi", "pii", "pubmed_id", "title", "year", "date", "type", "subtype")
    }
    primary_journal = copy.deepcopy(primary.get("journal", {}))
    primary_link = primary.get("scopus", {}).get("scopus_link")
    primary_citations = int(primary.get("scopus", {}).get("citations", 0) or 0)
    duplicate_citations = int(duplicate.get("scopus", {}).get("citations", 0) or 0)
    merged = merge_publication(primary, duplicate)
    merged.update(identity)
    for key, value in preferred.items():
        if value not in (None, ""):
            merged[key] = value
    merged["journal"] = {
        key: primary_journal.get(key) or merged.get("journal", {}).get(key)
        for key in set(primary_journal) | set(merged.get("journal", {}))
    }
    merged["scopus"]["citations"] = max(primary_citations, duplicate_citations)
    merged["scopus"]["scopus_link"] = primary_link or merged["scopus"].get("scopus_link")
    return merged


def deduplicate_publications(
    publications: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    """Deduplicate a complete result by EID, DOI, then exact title/year/journal."""
    output: dict[str, dict[str, Any]] = {}
    canonical_by_key: dict[tuple[str, ...], str] = {}
    aliases: dict[str, str] = {}
    for numeric, publication in sorted(publications.items()):
        key = duplicate_key(publication)
        canonical = canonical_by_key.get(key)
        if canonical is None:
            canonical_by_key[key] = numeric
            output[numeric] = publication
            aliases[numeric] = numeric
            continue
        output[canonical] = merge_duplicate_publication(output[canonical], publication)
        aliases[numeric] = canonical
    return output, aliases


def remap_author_references(
    authors: dict[str, dict[str, Any]],
    publications: dict[str, dict[str, Any]],
    aliases: dict[str, str],
) -> None:
    for author in authors.values():
        references: dict[str, dict[str, Any]] = {}
        for reference in author.get("publicacoes", []):
            numeric = str(reference.get("publication_id", "")).split("-")[-1]
            canonical = aliases.get(numeric, numeric)
            publication = publications.get(canonical)
            if not publication:
                continue
            eid = publication["eid"]
            candidate = {**reference, "publication_id": eid}
            previous = references.get(eid)
            if previous:
                candidate["author_position"] = min(
                    int(previous.get("author_position", 1) or 1),
                    int(candidate.get("author_position", 1) or 1),
                )
                candidate["is_corresponding_author"] = bool(
                    previous.get("is_corresponding_author")
                    or candidate.get("is_corresponding_author")
                )
            references[eid] = candidate
        author["publicacoes"] = [references[eid] for eid in sorted(references)]


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--previous", type=Path, default=DEFAULT_PREVIOUS)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--site-root", type=Path, default=ROOT)
    parser.add_argument("--full", action="store_true", help="Require all curated active author IDs")
    parser.add_argument("--dry-run", action="store_true", help="Document that output stays in staging; promotion is always external")
    args = parser.parse_args()
    ROOT = args.site_root.resolve()
    if args.output.resolve() == args.previous.resolve():
        print("Scopus output must be a disposable staging directory, not the published tree.", file=sys.stderr)
        return 2
    if args.output.exists():
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True)
    staged_files = sorted(args.input.glob("*.json"))
    if not staged_files:
        print("No complete Scopus staging files found.", file=sys.stderr)
        return 1
    professors = {item["id"]: item for item in load(ROOT / "data" / "pessoal" / "professores.json")["professores"] if item["ativo"] and item["scopus_author_ids"]}
    staged = {load(path)["professor_id"]: load(path) for path in staged_files}
    unknown = set(staged) - set(professors)
    missing = set(professors) - set(staged)
    if unknown or (args.full and missing):
        print(f"Incomplete/unknown Scopus staging; missing={sorted(missing)}, unknown={sorted(unknown)}", file=sys.stderr)
        return 1
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    generated_date = timestamp[:10]
    previous_authors = load(args.previous / "autores.json")["autores"]
    # A complete run is authoritative for generated Scopus data. A partial run
    # may update only the requested people and must preserve everybody else.
    authors = {} if args.full else copy.deepcopy(previous_authors)
    previous_publications = {
        path.stem: load(path) for path in (args.previous / "publications" / "by_eid").glob("*.json")
    }
    previous_manifest_path = args.previous / "manifest.json"
    previous_manifest = load(previous_manifest_path) if previous_manifest_path.exists() else {}
    previous_all_curated_ids = previous_manifest.get("curated_ids")
    if not isinstance(previous_all_curated_ids, dict):
        previous_all_curated_ids = None
    publications = {} if args.full else copy.deepcopy(previous_publications)
    curated_ids = {
        professor_id: list(professors[professor_id]["scopus_author_ids"])
        for professor_id in sorted(staged)
    }
    if args.full:
        all_curated_ids = {
            professor_id: list(professors[professor_id]["scopus_author_ids"])
            for professor_id in sorted(professors)
        }
        previous_report_ids = previous_all_curated_ids
    else:
        all_curated_ids = copy.deepcopy(previous_all_curated_ids or {
            professor_id: list(professors[professor_id]["scopus_author_ids"])
            for professor_id in sorted(professors)
        })
        all_curated_ids.update(curated_ids)
        previous_report_ids = (
            {
                professor_id: previous_all_curated_ids[professor_id]
                for professor_id in sorted(staged)
                if professor_id in previous_all_curated_ids
            }
            if previous_all_curated_ids is not None
            else None
        )
    for professor_id, raw in sorted(staged.items()):
        professor = professors[professor_id]
        author_ids = set(professor["scopus_author_ids"])
        refs = []
        for entry in raw.get("publications", []):
            publication = normalize_entry(entry, professor_id, professor["nome"], author_ids, timestamp)
            numeric = publication["eid"].split("-")[-1]
            existing = publications.get(numeric) or previous_publications.get(numeric)
            publications[numeric] = merge_publication(existing, publication)
            positions = [index + 1 for index, author in enumerate(publication["authors"]) if author["eam_professor_id"] == professor_id]
            refs.append({"publication_id": publication["eid"], "author_position": positions[0] if positions else 1, "is_corresponding_author": False})
        old_count = len(previous_authors.get(professor_id, {}).get("publicacoes", []))
        if old_count and len(refs) < old_count * 0.8:
            print(f"Drop above 20% for {professor_id}; last good output preserved.", file=sys.stderr)
            return 1
        authors[professor_id] = {"metrics": author_metrics(raw.get("authors", []), generated_date), "publicacoes": sorted(refs, key=lambda item: item["publication_id"]), "metadata": {"source": "scopus", "updated_at": timestamp}}
    old_total = len(previous_publications)
    collected_total = len(publications)
    if args.full and old_total and collected_total < old_total * 0.95:
        print("Global Scopus drop above 5%; last good output preserved.", file=sys.stderr)
        return 1
    if args.full:
        publications, aliases = deduplicate_publications(publications)
        remap_author_references(authors, publications, aliases)
    candidate_authors = {"schema_version": 1, "autores": dict(sorted(authors.items()))}
    previous_author_data = {"schema_version": 1, "autores": previous_authors}
    report = render_report(
        previous_authors,
        candidate_authors["autores"],
        previous_publications,
        publications,
        curated_ids,
        args.full,
        previous_report_ids,
    )
    semantic_same = (
        semantic(candidate_authors) == semantic(previous_author_data)
        and semantic(publications) == semantic(previous_publications)
        and previous_all_curated_ids == all_curated_ids
    )
    if semantic_same:
        shutil.copytree(args.previous, args.output, dirs_exist_ok=True)
        args.report.write_text(report, encoding="utf-8")
        print("No substantive Scopus changes.")
        return 0
    write(args.output / "autores.json", candidate_authors)
    for numeric, publication in sorted(publications.items()):
        write(args.output / "publications" / "by_eid" / f"{numeric}.json", publication)
    index = {publication["eid"]: {"title": publication["title"], "year": publication["year"], "type": publication["type"], "eam_coauthors": publication["eam_coauthors"], "citations": publication["scopus"]["citations"]} for publication in publications.values()}
    write(args.output / "publications" / "index.json", {"metadata": {"total_publications": len(publications), "last_updated": timestamp, "version": "1.0"}, "publications": dict(sorted(index.items()))})
    write(args.output / "manifest.json", {"source": "scopus", "generated_at": timestamp, "status": "ok", "records": len(authors), "pipeline_version": os.environ.get("GITHUB_SHA", "local"), "last_complete_run": timestamp, "curated_ids": all_curated_ids})
    args.report.write_text(report, encoding="utf-8")
    print(f"Normalized {len(publications)} public Scopus records; zero abstracts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

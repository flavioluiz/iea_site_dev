#!/usr/bin/env python3
"""Fetch the minimal approved Scopus fields into private staging files."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ModuleNotFoundError:  # --dry-run intentionally works without network dependencies
    requests = None  # type: ignore[assignment]

REQUEST_ERROR = requests.RequestException if requests is not None else RuntimeError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scopus_env import scopus_headers  # noqa: E402
from people_data import load_professors  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
API = "https://api.elsevier.com/content"
SEARCH_FIELDS = ",".join((
    "eid", "dc:title", "prism:coverDate", "prism:doi", "prism:publicationName",
    "subtype", "citedby-count", "prism:url", "dc:creator", "author",
))


def client() -> requests.Session:
    if requests is None:
        raise RuntimeError("install scripts/requirements-scopus.txt before fetching")
    retry = Retry(total=4, connect=4, read=4, backoff_factor=1.5, status_forcelist=(429, 500, 502, 503, 504))
    value = requests.Session()
    value.headers.update(scopus_headers())
    value.mount("https://", HTTPAdapter(max_retries=retry))
    return value


def get_json(value: requests.Session, url: str, params: dict[str, Any]) -> dict[str, Any]:
    response = value.get(url, params=params, timeout=(10, 60))
    response.raise_for_status()
    remaining = response.headers.get("X-RateLimit-Remaining")
    if remaining is not None:
        print(f"Scopus quota remaining: {remaining}")
    return response.json()


def fetch_author(value: requests.Session, author_id: str) -> dict[str, Any]:
    return get_json(value, f"{API}/author/author_id/{author_id}", {"view": "ENHANCED"})


def fetch_publications(value: requests.Session, author_ids: list[str]) -> list[dict[str, Any]]:
    query = " OR ".join(f"AU-ID({author_id})" for author_id in author_ids)
    start = 0
    entries: dict[str, dict[str, Any]] = {}
    while True:
        payload = get_json(
            value,
            f"{API}/search/scopus",
            {"query": query, "view": "COMPLETE", "field": SEARCH_FIELDS, "count": 25, "start": start},
        )
        search = payload.get("search-results", {})
        batch = search.get("entry", [])
        for entry in batch:
            eid = entry.get("eid")
            if eid:
                entries[eid] = entry
        start += len(batch)
        total = int(search.get("opensearch:totalResults", 0) or 0)
        if not batch or start >= total:
            break
        time.sleep(0.2)
    return [entries[eid] for eid in sorted(entries)]


def selected_professors(requested: list[str], site_root: Path = ROOT) -> list[dict[str, Any]]:
    records = load_professors(site_root)
    selected = [item for item in records if item["ativo"] and item["scopus_author_ids"]]
    if requested:
        known = {item["id"] for item in selected}
        unknown = set(requested) - known
        if unknown:
            raise ValueError(f"pessoa sem ID Scopus ativo: {', '.join(sorted(unknown))}")
        selected = [item for item in selected if item["id"] in requested]
    return selected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--site-root", type=Path, default=ROOT)
    parser.add_argument("--professor", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        professors = selected_professors(args.professor, args.site_root)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    if not professors:
        print("No active professor has a curated Scopus ID.", file=sys.stderr)
        return 1
    print(f"Selected {len(professors)} professor records; abstracts are disabled.")
    if args.dry_run:
        for professor in professors:
            print(f"- {professor['id']}: {', '.join(professor['scopus_author_ids'])}")
        return 0
    args.output.mkdir(parents=True, exist_ok=True)
    try:
        value = client()
        for position, professor in enumerate(professors, 1):
            output = args.output / f"{professor['id']}.json"
            if args.resume and output.exists() and not args.force:
                print(f"[{position}/{len(professors)}] resume {professor['id']}")
                continue
            print(f"[{position}/{len(professors)}] fetch {professor['id']}")
            authors = [fetch_author(value, author_id) for author_id in professor["scopus_author_ids"]]
            publications = fetch_publications(value, professor["scopus_author_ids"])
            payload = {
                "professor_id": professor["id"], "scopus_author_ids": professor["scopus_author_ids"],
                "collected_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "authors": authors, "publications": publications,
            }
            output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (REQUEST_ERROR, RuntimeError, ValueError, KeyError) as exc:
        print(f"Scopus fetch aborted; published data remains unchanged: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

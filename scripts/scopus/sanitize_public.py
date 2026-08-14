#!/usr/bin/env python3
"""Remove Scopus fields that are not approved for the public repository."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PUBLICATIONS = ROOT / "data" / "generated" / "scopus" / "publications" / "by_eid"
FORBIDDEN_TOP_LEVEL = {"abstract", "authkeywords", "email"}
FORBIDDEN_SCOPUS_FIELDS = {"subject_areas"}


def sanitize(value: dict) -> bool:
    changed = False
    for key in FORBIDDEN_TOP_LEVEL:
        if key in value:
            del value[key]
            changed = True
    scopus = value.get("scopus")
    if isinstance(scopus, dict):
        for key in FORBIDDEN_SCOPUS_FIELDS:
            if key in scopus:
                del scopus[key]
                changed = True
    for author in value.get("authors", []):
        if author.get("affiliation") is not None:
            author["affiliation"] = None
            changed = True
    return changed


def main() -> int:
    changed = 0
    for path in sorted(PUBLICATIONS.glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        if sanitize(value):
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            changed += 1
    authors_path = ROOT / "data" / "generated" / "scopus" / "autores.json"
    authors_data = json.loads(authors_path.read_text(encoding="utf-8"))
    authors_changed = False
    for author in authors_data["autores"].values():
        metadata = author.get("metadata", {})
        if set(metadata) - {"link_scopus"}:
            author["metadata"] = {"link_scopus": metadata.get("link_scopus", "")}
            authors_changed = True
    if authors_changed:
        authors_path.write_text(json.dumps(authors_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Sanitized {changed} public Scopus records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

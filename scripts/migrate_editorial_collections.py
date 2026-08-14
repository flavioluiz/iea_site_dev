#!/usr/bin/env python3
"""One-time deterministic migration from keyed YAML maps to CMS-friendly JSON lists."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = "31afe4a65a07127dd8a33b2c2ce8200762c98f9e"
COLLECTIONS = (
    ("departamentos", "departamentos"),
    ("laboratorios", "laboratorios"),
    ("projetos", "projetos"),
    ("linhas_pesquisa", "linhas"),
)


def main() -> int:
    for stem, key in COLLECTIONS:
        source_path = f"data/{stem}.yaml"
        source = subprocess.run(
            ["git", "show", f"{SOURCE_COMMIT}:{source_path}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        data = yaml.safe_load(source)
        records = []
        for record_id, value in data[key].items():
            record = dict(value)
            record["id"] = record_id
            records.append(record)
        target = ROOT / "data" / f"{stem}.json"
        target.write_text(
            json.dumps({"schema_version": 1, key: records}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

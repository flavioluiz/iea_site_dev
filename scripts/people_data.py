#!/usr/bin/env python3
"""Shared readers for the one-file-per-person editorial data."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def load_professors(site_root: Path) -> list[dict[str, Any]]:
    folder = site_root / "data" / "pessoal" / "professores"
    if folder.is_dir():
        return [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(folder.glob("*.json"))
        ]
    legacy = site_root / "data" / "pessoal" / "professores.json"
    return json.loads(legacy.read_text(encoding="utf-8"))["professores"]


def load_professors_at_ref(site_root: Path, ref: str) -> list[dict[str, Any]] | None:
    """Read either the current directory layout or the legacy aggregate at a git ref."""
    tree = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", ref, "--", "data/pessoal/professores"],
        cwd=site_root,
        capture_output=True,
        text=True,
        check=False,
    )
    paths = sorted(
        path
        for path in tree.stdout.splitlines()
        if path.startswith("data/pessoal/professores/") and path.endswith(".json")
    )
    if paths:
        records = []
        for path in paths:
            result = subprocess.run(
                ["git", "show", f"{ref}:{path}"],
                cwd=site_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                return None
            records.append(json.loads(result.stdout))
        return records

    legacy = subprocess.run(
        ["git", "show", f"{ref}:data/pessoal/professores.json"],
        cwd=site_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if legacy.returncode != 0:
        return None
    return json.loads(legacy.stdout)["professores"]

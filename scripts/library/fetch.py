#!/usr/bin/env python3
"""Fetch BDITA metadata into a staging directory; never modifies published data."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from bdita_html import parse_detail, parse_list


ROOT = Path(__file__).resolve().parents[2]
PREVIOUS = ROOT / "data" / "generated" / "biblioteca"
TESES_BASE = "http://www.bdita.bibl.ita.br/tesesdigitais/"
TGS_BASE = "http://www.bdita.bibl.ita.br/TGsDigitais/"
DEFAULT_TESES_URL = TESES_BASE + "resultado_titulos_programas.php?ano_inicio=1984&ano_fim=2026&tipo_tese=Todos&programa=Engenharia%20Aeron%E1utica%20e%20Mec%E2nica&area_concen=&total_teses_prog=3128"
DEFAULT_TG_AERO_URL = TGS_BASE + "resultado_titulos_cursos.php?ano_inicio=1952&ano_fim=2026&curso=Engenharia%20Aeron%E1utica&total_TGs_curso=741"
DEFAULT_TG_ESP_URL = TGS_BASE + "resultado_titulos_cursos.php?ano_inicio=1952&ano_fim=2026&curso=Engenharia%20Aeroespacial&total_TGs_curso=173"


def session() -> requests.Session:
    retry = Retry(total=3, connect=3, read=3, backoff_factor=1, status_forcelist=(429, 500, 502, 503, 504))
    value = requests.Session()
    value.mount("http://", HTTPAdapter(max_retries=retry))
    value.mount("https://", HTTPAdapter(max_retries=retry))
    contact = os.environ.get("IEA_LIBRARY_CONTACT", "https://www.aer.ita.br/")
    value.headers["User-Agent"] = f"IEA-ITA-library-metadata/1.0 ({contact})"
    return value


def get_text(client: requests.Session, url: str) -> str:
    response = client.get(url, timeout=(10, 45))
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return response.text


def existing_records(kind: str) -> dict[str, dict[str, Any]]:
    """Reconstruct staging metadata from normalized public records, never raw cache."""
    id_key = "num_tese" if kind == "teses" else "num_tg"
    output: dict[str, dict[str, Any]] = {}
    for path in (PREVIOUS / kind / "by_id").glob("*.json"):
        item = json.loads(path.read_text(encoding="utf-8"))
        item["advisors"] = [
            advisor.get("name", "") if isinstance(advisor, dict) else str(advisor)
            for advisor in item.get("advisors", [])
        ]
        item["co_advisors"] = [
            advisor.get("name", "") if isinstance(advisor, dict) else str(advisor)
            for advisor in item.get("co_advisors", [])
        ]
        output[str(item[id_key])] = item
    return output


def enrich(client: requests.Session, rows: list[dict[str, Any]], kind: str, base_url: str, delay: float) -> list[dict[str, Any]]:
    previous = existing_records(kind)
    id_key = "num_tese" if kind == "teses" else "num_tg"
    output: list[dict[str, Any]] = []
    for position, row in enumerate(rows, 1):
        identifier = str(row[id_key])
        if identifier in previous:
            # List-page fields may change even when the stable ID already exists.
            output.append({**previous[identifier], **row})
            continue
        print(f"[{kind} {position}/{len(rows)}] {identifier}")
        detail = parse_detail(get_text(client, row["detail_url"]), base_url)
        output.append({**row, **detail})
        if delay:
            time.sleep(delay)
    return sorted(output, key=lambda item: str(item[id_key]))


def write_raw(path: Path, key: str, records: list[dict[str, Any]], sources: list[str]) -> None:
    value = {
        "metadata": {
            "sources": sources,
            "retrieved_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "total": len(records),
        },
        key: records,
    }
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--type", choices=("all", "teses", "tgs"), default="all")
    parser.add_argument("--delay", type=float, default=0.25)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    client = session()
    try:
        if args.type in {"all", "teses"}:
            url = os.environ.get("BDITA_TESES_URL", DEFAULT_TESES_URL)
            rows = parse_list(get_text(client, url), TESES_BASE, "teses")
            allowed = {"Mestrado Acadêmico", "Doutorado"}
            rows = [row for row in rows if row.get("course") in allowed]
            write_raw(args.output / "teses_raw.json", "teses", enrich(client, rows, "teses", TESES_BASE, args.delay), [url])
        if args.type in {"all", "tgs"}:
            sources = [
                ("Engenharia Aeronáutica", os.environ.get("BDITA_TG_AERO_URL", DEFAULT_TG_AERO_URL)),
                ("Engenharia Aeroespacial", os.environ.get("BDITA_TG_ESP_URL", DEFAULT_TG_ESP_URL)),
            ]
            rows: list[dict[str, Any]] = []
            for course, url in sources:
                rows.extend(parse_list(get_text(client, url), TGS_BASE, "tgs", course))
            write_raw(args.output / "tgs_raw.json", "tgs", enrich(client, rows, "tgs", TGS_BASE, args.delay), [url for _, url in sources])
    except (requests.RequestException, ValueError) as exc:
        print(f"Biblioteca fetch aborted safely: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

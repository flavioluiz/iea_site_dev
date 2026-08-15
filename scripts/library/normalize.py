#!/usr/bin/env python3
"""Normalize staged BDITA metadata, enforce thresholds, and render a review report."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from people_data import load_professors


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PREVIOUS = ROOT / "data" / "generated" / "biblioteca"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_compact(path: Path, value: Any) -> None:
    """Keep the historic compact indexes compact so routine PRs stay reviewable."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def normalized_name(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_value = decomposed.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_value.casefold().replace("-", " ").split())


def public_records(folder: Path, kind: str) -> list[dict[str, Any]]:
    """Reconstruct source-like records from the normalized public contract."""
    id_key = "num_tese" if kind == "teses" else "num_tg"
    records = []
    for path in (folder / kind / "by_id").glob("*.json"):
        item = load(path)
        item["advisors"] = [
            advisor.get("name", "") if isinstance(advisor, dict) else str(advisor)
            for advisor in item.get("advisors", [])
        ]
        item["co_advisors"] = [
            advisor.get("name", "") if isinstance(advisor, dict) else str(advisor)
            for advisor in item.get("co_advisors", [])
        ]
        item[id_key] = str(item[id_key])
        records.append(item)
    return sorted(records, key=lambda item: str(item[id_key]))


def raw_records(folder: Path, previous: Path, kind: str) -> list[dict[str, Any]]:
    path = folder / f"{kind}_raw.json"
    if not path.exists():
        return public_records(previous, kind)
    return load(path)[kind]


def indexed(records: list[dict[str, Any]], id_key: str) -> dict[str, dict[str, Any]]:
    return {str(record[id_key]): record for record in records}


def comparable(record: dict[str, Any], kind: str) -> dict[str, Any]:
    id_key = "num_tese" if kind == "teses" else "num_tg"
    return {
        id_key: str(record.get(id_key, "")),
        "title": record.get("title") or "",
        "author": record.get("author") or "",
        "year": str(record.get("year") or ""),
        # The staging contract calls this field ``course`` while the historic
        # public TG contract calls it ``curso``. They are semantically equal.
        "course": record.get("course") or record.get("curso") or "",
        "area": record.get("area") or "",
        "program": record.get("program") or "",
        "advisors": record.get("advisors") or [],
        "co_advisors": record.get("co_advisors") or [],
        "abstract": record.get("abstract") or "",
        "subjects": record.get("subjects") or [],
        "defense_date": record.get("defense_date") or "",
        "detail_url": record.get("detail_url") or "",
        "pdf_url": record.get("pdf_url") or record.get("fulltext_url") or "",
    }


def has_semantic_change(input_dir: Path, previous: Path) -> bool:
    for kind, id_key in (("teses", "num_tese"), ("tgs", "num_tg")):
        current = {key: comparable(value, kind) for key, value in indexed(raw_records(input_dir, previous, kind), id_key).items()}
        old = {key: comparable(value, kind) for key, value in indexed(public_records(previous, kind), id_key).items()}
        if current != old:
            return True
    return False


def diff_ids(current: list[dict[str, Any]], previous: list[dict[str, Any]], kind: str) -> tuple[list[str], list[str], list[str]]:
    id_key = "num_tese" if kind == "teses" else "num_tg"
    new_index = {key: comparable(value, kind) for key, value in indexed(current, id_key).items()}
    old_index = {key: comparable(value, kind) for key, value in indexed(previous, id_key).items()}
    added = sorted(set(new_index) - set(old_index))
    removed = sorted(set(old_index) - set(new_index))
    changed = sorted(key for key in set(new_index) & set(old_index) if new_index[key] != old_index[key])
    return added, removed, changed


def active_professor_ids() -> set[str]:
    professors = load_professors(ROOT)
    return {item["id"] for item in professors if item["ativo"]}


def prior_advisor_map(previous: Path) -> dict[str, str]:
    allowed = active_professor_ids()
    candidates: dict[str, set[str]] = defaultdict(set)
    for kind in ("teses", "tgs"):
        folder = previous / kind / "by_id"
        for path in folder.glob("*.json"):
            record = load(path)
            for field in ("advisors", "co_advisors"):
                for advisor in record.get(field, []):
                    professor_id = advisor.get("professor_slug")
                    if professor_id in allowed:
                        candidates[normalized_name(advisor["name"])].add(professor_id)
    return {name: next(iter(values)) for name, values in candidates.items() if len(values) == 1}


def curated_advisor_map() -> dict[str, str]:
    professors = load_professors(ROOT)
    mapping = {normalized_name(item["nome"]): item["id"] for item in professors if item["ativo"]}
    aliases = load(ROOT / "data" / "pessoal" / "aliases_biblioteca.json")["aliases"]
    mapping.update({normalized_name(item["nome_fonte"]): item["professor_id"] for item in aliases})
    return mapping


def matched_advisors(names: list[str], mapping: dict[str, str], unmatched: set[str]) -> list[dict[str, Any]]:
    result = []
    for name in names:
        professor_id = mapping.get(normalized_name(name))
        if not professor_id:
            unmatched.add(name)
        result.append({"name": name, "professor_slug": professor_id})
    return result


def validate_thresholds(previous: Path, thesis_count: int, tg_count: int) -> None:
    manifest = load(previous / "manifest.json")
    counts = manifest.get("counts", {})
    old_theses = counts.get("teses_dissertacoes", 0)
    old_tgs = counts.get("trabalhos_graduacao", 0)
    for label, old, new in (("teses/dissertações", old_theses, thesis_count), ("TGs", old_tgs, tg_count)):
        if new == 0:
            raise ValueError(f"coleta de {label} retornou zero registros")
        if old and new < old * 0.95:
            raise ValueError(f"queda de {label} acima de 5% ({old} → {new}); última versão boa preservada")


def add_once(values: list[str], identifier: str) -> None:
    if identifier not in values:
        values.append(identifier)


def thesis_record(source: dict[str, Any], mapping: dict[str, str], unmatched: set[str]) -> dict[str, Any]:
    identifier = str(source["num_tese"])
    return {
        "num_tese": identifier, "type": "tese", "title": source.get("title", ""),
        "author": source.get("author", ""), "year": str(source.get("year", "")),
        "course": source.get("course", ""), "area": source.get("area", ""),
        "program": source.get("program", ""),
        "advisors": matched_advisors(source.get("advisors") or [], mapping, unmatched),
        "co_advisors": matched_advisors(source.get("co_advisors") or [], mapping, unmatched),
        "abstract": source.get("abstract", ""), "subjects": source.get("subjects") or [],
        "defense_date": source.get("defense_date", ""), "detail_url": source.get("detail_url", ""),
        "pdf_url": source.get("pdf_url", "") or source.get("fulltext_url", ""),
    }


def tg_record(source: dict[str, Any], mapping: dict[str, str], unmatched: set[str]) -> dict[str, Any]:
    identifier = str(source["num_tg"])
    return {
        "num_tg": identifier, "type": "tg", "title": source.get("title", ""),
        "author": source.get("author", ""), "year": str(source.get("year", "")),
        "curso": source.get("course") or source.get("curso", ""),
        "advisors": matched_advisors(source.get("advisors") or [], mapping, unmatched),
        "co_advisors": matched_advisors(source.get("co_advisors") or [], mapping, unmatched),
        "abstract": source.get("abstract", ""), "subjects": source.get("subjects") or [],
        "detail_url": source.get("detail_url", ""),
        "pdf_url": source.get("pdf_url", "") or source.get("fulltext_url", ""),
    }


def apply_thesis_additions(
    sources: list[dict[str, Any]], output: Path, mapping: dict[str, str], unmatched: set[str], generated_at: str
) -> None:
    if not sources:
        return
    compact_path = output / "teses" / "lista.json"
    compact = load(compact_path)
    by_professor_path = output / "teses" / "by_professor.json"
    by_professor = load(by_professor_path)
    statistics_path = output / "teses" / "statistics.json"
    statistics = load(statistics_path)
    additions = []
    for source in sources:
        record = thesis_record(source, mapping, unmatched)
        identifier = record["num_tese"]
        write(output / "teses" / "by_id" / f"{identifier}.json", record)
        advisors = record["advisors"]
        coadvisors = record["co_advisors"]
        matched = [item["professor_slug"] for item in advisors + coadvisors if item["professor_slug"]]
        if not matched:
            continue
        is_master = "Mestrado" in record["course"]
        additions.append({
            "id": identifier, "t": record["title"][:200], "a": record["author"], "y": record["year"],
            "c": "M" if is_master else "D", "ad": [item["name"] for item in advisors][:3],
            "ap": [item["professor_slug"] for item in advisors if item["professor_slug"]][:3],
        })
        statistics["total"] = int(statistics.get("total", 0)) + 1
        count_key = "mestrado" if is_master else "doutorado"
        statistics[count_key] = int(statistics.get(count_key, 0)) + 1
        years = statistics.setdefault("by_year", {})
        years[record["year"]] = int(years.get(record["year"], 0)) + 1
        for advisor in advisors:
            professor_id = advisor["professor_slug"]
            if not professor_id:
                continue
            value = by_professor.setdefault(
                professor_id,
                {"as_advisor": [], "as_coadvisor": [], "mestrado_count": 0, "doutorado_count": 0},
            )
            add_once(value["as_advisor"], identifier)
            value[f"{count_key}_count"] = int(value.get(f"{count_key}_count", 0)) + 1
        for advisor in coadvisors:
            professor_id = advisor["professor_slug"]
            if professor_id:
                value = by_professor.setdefault(
                    professor_id,
                    {"as_advisor": [], "as_coadvisor": [], "mestrado_count": 0, "doutorado_count": 0},
                )
                add_once(value["as_coadvisor"], identifier)
    if additions:
        additions.sort(key=lambda item: (item["y"], item["id"]), reverse=True)
        compact = additions + compact
        write_compact(compact_path, compact)
        write_compact(output / "teses" / "index.json", compact)
        write(by_professor_path, by_professor)
        statistics["generated_at"] = generated_at
        write(statistics_path, statistics)


def apply_tg_additions(
    sources: list[dict[str, Any]], output: Path, mapping: dict[str, str], unmatched: set[str], generated_at: str
) -> None:
    if not sources:
        return
    compact_path = output / "tgs" / "lista.json"
    compact = load(compact_path)
    by_professor_path = output / "tgs" / "by_professor.json"
    by_professor = load(by_professor_path)
    statistics_path = output / "tgs" / "statistics.json"
    statistics = load(statistics_path)
    additions = []
    for source in sources:
        record = tg_record(source, mapping, unmatched)
        identifier = record["num_tg"]
        write(output / "tgs" / "by_id" / f"{identifier}.json", record)
        advisors = record["advisors"]
        coadvisors = record["co_advisors"]
        professor_ids = [item["professor_slug"] for item in advisors + coadvisors if item["professor_slug"]]
        is_iea = bool(professor_ids)
        additions.append({
            "id": identifier, "t": record["title"][:200], "a": record["author"], "y": record["year"],
            "cu": record["curso"], "ad": [item["name"] for item in advisors][:3],
            "ap": [item["professor_slug"] for item in advisors if item["professor_slug"]][:3], "iea": is_iea,
        })
        statistics["total"] = int(statistics.get("total", 0)) + 1
        years = statistics.setdefault("by_year", {})
        years[record["year"]] = int(years.get(record["year"], 0)) + 1
        courses = statistics.setdefault("by_curso", {})
        courses[record["curso"]] = int(courses.get(record["curso"], 0)) + 1
        for field, target in (("advisors", "as_advisor"), ("co_advisors", "as_coadvisor")):
            for advisor in record[field]:
                professor_id = advisor["professor_slug"]
                if professor_id:
                    value = by_professor.setdefault(professor_id, {"as_advisor": [], "as_coadvisor": []})
                    add_once(value[target], identifier)
    additions.sort(key=lambda item: (item["y"], item["id"]), reverse=True)
    compact = additions + compact
    write_compact(compact_path, compact)
    write_compact(output / "tgs" / "index.json", compact)
    if any(item["iea"] for item in additions):
        write(by_professor_path, by_professor)
    statistics["generated_at"] = generated_at
    write(statistics_path, statistics)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--previous", type=Path, default=DEFAULT_PREVIOUS)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    if args.output.resolve() == args.previous.resolve():
        print("Library output must be a disposable staging directory, not the published tree.", file=sys.stderr)
        return 2
    if args.output.exists():
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True)
    previous_theses = public_records(args.previous, "teses")
    previous_tgs = public_records(args.previous, "tgs")
    theses = raw_records(args.input, args.previous, "teses")
    tgs = raw_records(args.input, args.previous, "tgs")
    try:
        validate_thresholds(args.previous, len(theses), len(tgs))
    except ValueError as exc:
        print(f"Library normalization aborted safely: {exc}", file=sys.stderr)
        return 1
    thesis_added, thesis_removed, thesis_changed = diff_ids(theses, previous_theses, "teses")
    tg_added, tg_removed, tg_changed = diff_ids(tgs, previous_tgs, "tgs")
    shutil.copytree(args.previous, args.output, dirs_exist_ok=True)
    if not thesis_added and not tg_added:
        duration = time.monotonic() - started
        args.report.write_text(
            "# Atualização da Biblioteca\n\n"
            "Nenhuma entrada nova foi encontrada; nenhuma proposta precisa ser aberta.\n\n"
            f"- Teses/dissertações publicadas: {len(previous_theses)}\n"
            f"- Trabalhos de graduação publicados: {len(previous_tgs)}\n"
            f"- Alterações de metadados existentes preservadas para revisão separada: {len(thesis_changed) + len(tg_changed)}\n"
            f"- Registros ausentes na fonte, mas preservados no site: {len(thesis_removed) + len(tg_removed)}\n"
            f"- Duração da normalização: {duration:.2f} s\n"
            f"- Versão do coletor: `{os.environ.get('GITHUB_SHA', 'local')}`\n",
            encoding="utf-8",
        )
        print("No new library entries; the published tree was preserved byte for byte.")
        return 0

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    mapping = prior_advisor_map(args.previous)
    mapping.update(curated_advisor_map())
    unmatched: set[str] = set()
    thesis_source_index = indexed(theses, "num_tese")
    tg_source_index = indexed(tgs, "num_tg")
    apply_thesis_additions(
        [thesis_source_index[identifier] for identifier in thesis_added],
        args.output, mapping, unmatched, generated_at,
    )
    apply_tg_additions(
        [tg_source_index[identifier] for identifier in tg_added],
        args.output, mapping, unmatched, generated_at,
    )
    published_theses = len(list((args.output / "teses" / "by_id").glob("*.json")))
    published_tgs = len(list((args.output / "tgs" / "by_id").glob("*.json")))
    thesis_compact = load(args.output / "teses" / "lista.json")
    tg_compact = load(args.output / "tgs" / "lista.json")
    manifest = {
        "source": "biblioteca-digital-ita", "generated_at": generated_at, "status": "ok",
        "records": published_theses + published_tgs, "pipeline_version": os.environ.get("GITHUB_SHA", "local"),
        "last_complete_run": generated_at,
        "counts": {
            "teses_dissertacoes": published_theses,
            "trabalhos_graduacao": published_tgs,
            "teses_dissertacoes_iea": len(thesis_compact),
            "trabalhos_graduacao_iea": sum(bool(item.get("iea")) for item in tg_compact),
        },
    }
    write(args.output / "manifest.json", manifest)
    aliases = load(ROOT / "data" / "pessoal" / "aliases_biblioteca.json")["aliases"]
    source_advisor_names = {
        normalized_name(name)
        for record in theses + tgs
        for name in (record.get("advisors") or []) + (record.get("co_advisors") or [])
    }
    aliases_used = sum(normalized_name(item["nome_fonte"]) in source_advisor_names for item in aliases)
    duration = time.monotonic() - started
    report = [
        "# Atualização da Biblioteca", "", f"- Teses/dissertações na fonte: {len(previous_theses)} → {len(theses)}",
        f"- Teses/dissertações publicadas após esta proposta: {published_theses}",
        f"- Trabalhos de graduação na fonte: {len(previous_tgs)} → {len(tgs)}",
        f"- Trabalhos de graduação publicados após esta proposta: {published_tgs}",
        f"- Teses/dissertações: +{len(thesis_added)} / ~{len(thesis_changed)} / -{len(thesis_removed)}",
        f"- TGs: +{len(tg_added)} / ~{len(tg_changed)} / -{len(tg_removed)}",
        f"- Alterações de metadados existentes preservadas para revisão separada: {len(thesis_changed) + len(tg_changed)}",
        f"- Registros ausentes na fonte, mas preservados no site: {len(thesis_removed) + len(tg_removed)}",
        f"- Aliases cadastrados/utilizados: {len(aliases)}/{aliases_used}",
        f"- Nomes de orientadores sem correspondência: {len(unmatched)}",
        f"- Duração da normalização: {duration:.2f} s",
        f"- Versão do coletor: `{manifest['pipeline_version']}`",
        "- Erros: 0", "", "## IDs adicionados, alterados e ausentes", "",
    ]
    report.extend(f"- Tese/dissertação adicionada: `{identifier}`" for identifier in thesis_added[:100])
    report.extend(f"- Tese/dissertação alterada: `{identifier}`" for identifier in thesis_changed[:100])
    report.extend(f"- Tese/dissertação ausente: `{identifier}`" for identifier in thesis_removed[:100])
    report.extend(f"- TG adicionado: `{identifier}`" for identifier in tg_added[:100])
    report.extend(f"- TG alterado: `{identifier}`" for identifier in tg_changed[:100])
    report.extend(f"- TG ausente: `{identifier}`" for identifier in tg_removed[:100])
    if not any((thesis_added, thesis_changed, thesis_removed, tg_added, tg_changed, tg_removed)):
        report.append("- Nenhum.")
    report.extend(["", "## Sem correspondência", ""])
    report.extend(f"- {name}" for name in sorted(unmatched))
    if not unmatched:
        report.append("- Nenhum.")
    args.report.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Normalized {manifest['records']} library records safely.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

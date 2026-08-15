from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from import_content_batch import (  # noqa: E402
    COLLECTIONS,
    current_payload,
    merged_records,
    normalize_records,
    records_from_payload,
    validate_payload,
)


class ImportContentBatchTests(unittest.TestCase):
    def test_accepts_list_and_collection_wrapper(self) -> None:
        records = [{"id": "novo"}]
        self.assertEqual(records, records_from_payload(records, "professores"))
        self.assertEqual(records, records_from_payload({"professores": records}, "professores"))

    def test_merge_updates_in_place_and_appends_new_ids(self) -> None:
        current = [{"id": "a", "nome": "A"}, {"id": "b", "nome": "B"}]
        incoming = {"b": {"id": "b", "nome": "B2"}, "c": {"id": "c", "nome": "C"}}
        self.assertEqual(
            [{"id": "a", "nome": "A"}, {"id": "b", "nome": "B2"}, {"id": "c", "nome": "C"}],
            merged_records(current, incoming),
        )

    def test_people_photo_paths_are_portable(self) -> None:
        records = normalize_records("pessoas", [{"id": "a", "foto": "/images/pessoal/a.jpg"}])
        self.assertEqual("images/pessoal/a.jpg", records[0]["foto"])

    def test_current_people_directory_satisfies_collective_schema(self) -> None:
        records = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted((ROOT / "data/pessoal/professores").glob("*.json"))
        ]
        payload = {"schema_version": 1, "professores": records}
        self.assertEqual([], validate_payload(COLLECTIONS["pessoas"], payload))

    def test_current_laboratory_directory_satisfies_collective_schema(self) -> None:
        header, records = current_payload(COLLECTIONS["laboratorios"])
        self.assertEqual(19, len(records))
        payload = dict(header)
        payload["laboratorios"] = records
        self.assertEqual([], validate_payload(COLLECTIONS["laboratorios"], payload))


if __name__ == "__main__":
    unittest.main()

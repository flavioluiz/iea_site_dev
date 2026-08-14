from pathlib import Path
import sys
import unittest


LIBRARY_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LIBRARY_DIR))

from bdita_html import parse_detail, parse_list  # noqa: E402


FIXTURES = Path(__file__).parent / "fixtures"


class BditaParserTests(unittest.TestCase):
    def test_list_has_stable_id_and_absolute_urls(self) -> None:
        html = (FIXTURES / "list_teses.html").read_text(encoding="utf-8")
        records = parse_list(html, "https://biblioteca.example/teses/", "teses")
        self.assertEqual(records[0]["num_tese"], "123")
        self.assertEqual(records[0]["course"], "Doutorado")
        self.assertEqual(records[0]["pdf_url"], "https://biblioteca.example/teses/123.pdf")

    def test_detail_extracts_repeated_fields_and_fulltext(self) -> None:
        html = (FIXTURES / "detail.html").read_text(encoding="utf-8")
        record = parse_detail(html, "https://biblioteca.example/teses/")
        self.assertEqual(record["advisors"], ["Flávio Luiz Cardoso Ribeiro"])
        self.assertEqual(record["subjects"], ["Aeronáutica"])
        self.assertEqual(record["fulltext_url"], "https://biblioteca.example/teses/123.pdf")

    def test_format_change_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            parse_list("<html><body>sem tabela</body></html>", "https://example/", "teses")


if __name__ == "__main__":
    unittest.main()

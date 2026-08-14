from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class AdminCspTests(unittest.TestCase):
    def test_csp_supports_decap_without_opening_inline_scripts(self) -> None:
        index = (ROOT / "static/admin/index.html").read_text(encoding="utf-8")
        csp = index.split('http-equiv="Content-Security-Policy" content="', 1)[1].split('"', 1)[0]

        self.assertIn("script-src 'self' 'unsafe-eval' https://unpkg.com", csp)
        self.assertNotIn("script-src 'self' 'unsafe-inline'", csp)
        self.assertIn("style-src 'unsafe-inline' https://fonts.googleapis.com", csp)
        self.assertIn("font-src data: https://fonts.gstatic.com", csp)
        self.assertIn("connect-src 'self' https://api.github.com https://github.com https://unpkg.com", csp)
        self.assertNotIn("frame-ancestors", csp)

    def test_frame_guard_runs_before_decap(self) -> None:
        index = (ROOT / "static/admin/index.html").read_text(encoding="utf-8")
        guard_position = index.index('src="./frame-guard.js"')
        decap_position = index.index("decap-cms@3.15.1/dist/decap-cms.js")
        guard = (ROOT / "static/admin/frame-guard.js").read_text(encoding="utf-8")

        self.assertLess(guard_position, decap_position)
        self.assertIn("window.self !== window.top", guard)
        self.assertIn("window.stop()", guard)


if __name__ == "__main__":
    unittest.main()

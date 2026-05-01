
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "html"
if str(HTML) not in sys.path:
    sys.path.insert(0, str(HTML))

from mycelia_platform import MyceliaPlatform


class AdminOverviewPayloadHotfixTest(unittest.TestCase):
    def test_admin_overview_does_not_delete_payload_before_reuse(self) -> None:
        platform = MyceliaPlatform()
        platform.core.database.clear()
        result = platform.admin_overview({"actor_signature": "test-admin"})
        self.assertEqual(result["status"], "ok")
        self.assertIn("users", result)
        self.assertIn("permission_catalog", result)
        self.assertIn("site_texts", result)


if __name__ == "__main__":
    unittest.main()

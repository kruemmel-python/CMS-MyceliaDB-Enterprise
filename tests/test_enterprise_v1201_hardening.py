
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "html"
if str(HTML) not in sys.path:
    sys.path.insert(0, str(HTML))

os.environ["MYCELIA_AUTOSAVE"] = "0"
os.environ["MYCELIA_AUTORESTORE"] = "0"

from mycelia_platform import MyceliaPlatform, verify_native_library_authenticity  # noqa: E402


class EnterpriseV1201HardeningTest(unittest.TestCase):
    def setUp(self) -> None:
        self.platform = MyceliaPlatform()
        self.platform.autosave_enabled = False
        self.platform.core.database.clear()

    def test_local_transport_token_binding_is_enabled_by_default(self) -> None:
        status = self.platform.local_transport_security_status({})
        self.assertEqual(status["status"], "ok")
        self.assertTrue(status["token_binding_enabled"])
        self.assertTrue(Path(status["token_path"]).exists())

    def test_admin_report_redaction_removes_credentials_and_session_tokens(self) -> None:
        raw = {
            "auth_pattern": "secret-auth",
            "profile_seed": "seed",
            "profile_blob": "blob",
            "engine_session": {
                "handle": "abcdefghijklmnopqrstuvwxyz123456",
                "request_token": "request-token-secret",
                "sequence": 3,
                "expires_at": 123.0,
                "rotated": True,
            },
            "nested": {"content_blob": "content", "signature": "a" * 64},
        }
        safe = self.platform._redact_admin_report_object(raw)
        self.assertNotIn("auth_pattern", safe)
        self.assertNotIn("profile_seed", safe)
        self.assertNotIn("profile_blob", safe)
        self.assertEqual(safe["engine_session"]["request_token"], "[redacted:enterprise-report]")
        self.assertNotIn("secret-auth", str(safe))
        self.assertNotIn("request-token-secret", str(safe))
        self.assertNotIn("'content'", str(safe))
        self.assertNotIn("content_blob", safe["nested"])
        self.assertLess(len(safe["nested"]["signature"]), 64)

    def test_smql_query_defaults_to_safe_mode(self) -> None:
        registered = self.platform.register_user({
            "username": "admin",
            "password": "secret",
            "role": "admin",
            "profile": {"email": "admin@example.test"},
        })
        self.assertEqual(registered["status"], "ok")
        response = self.platform.smql_query({"query": "FIND mycelia_users WHERE username=admin LIMIT 1"})
        self.assertEqual(response["status"], "ok")
        self.assertTrue(response["safe_mode"])
        rendered = str(response)
        self.assertNotIn("auth_pattern", rendered)
        self.assertNotIn("profile_blob", rendered)
        self.assertNotIn("profile_seed", rendered)

    def test_native_authenticity_reports_fail_closed_policy(self) -> None:
        dll = ROOT / "build" / "CC_OpenCl.dll"
        if not dll.exists():
            self.skipTest("test fixture DLL missing")
        status = verify_native_library_authenticity(dll, "core_opencl_driver")
        self.assertTrue(status["fail_closed"])
        self.assertFalse(status["fail_closed_triggered"])


if __name__ == "__main__":
    unittest.main()

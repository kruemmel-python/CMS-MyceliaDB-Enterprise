from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "html"
if str(HTML) not in sys.path:
    sys.path.insert(0, str(HTML))

from mycelia_platform import MyceliaPlatform, SNAPSHOT_MAGIC  # noqa: E402


class MyceliaSnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self._old_env = {
            "MYCELIA_AUTOSAVE": os.environ.get("MYCELIA_AUTOSAVE"),
            "MYCELIA_AUTORESTORE": os.environ.get("MYCELIA_AUTORESTORE"),
        }
        os.environ["MYCELIA_AUTOSAVE"] = "0"
        os.environ["MYCELIA_AUTORESTORE"] = "0"

    def tearDown(self) -> None:
        for name, value in self._old_env.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def _platform_with_user(self) -> MyceliaPlatform:
        platform = MyceliaPlatform()
        response = platform.register_user(
            {
                "username": "Ralf",
                "password": "correct horse battery staple",
                "profile": {
                    "vorname": "Ralf",
                    "nachname": "Krümmel",
                    "email": "ralf.kruemmel@example.test",
                },
            }
        )
        self.assertEqual(response["status"], "ok", response)
        return platform

    def test_snapshot_is_binary_encrypted_and_restores_login_after_cold_start(self) -> None:
        platform = self._platform_with_user()

        with tempfile.TemporaryDirectory() as tmp:
            snapshot = Path(tmp) / "coldstart.mycelia"
            created = platform.create_snapshot({"path": str(snapshot)})
            self.assertEqual(created["status"], "ok", created)
            raw = snapshot.read_bytes()

            self.assertTrue(raw.startswith(SNAPSHOT_MAGIC))
            self.assertNotIn(b"Ralf", raw)
            self.assertNotIn("Krümmel".encode("utf-8"), raw)
            self.assertNotIn(b"mycelia_users", raw)
            self.assertNotIn(b"correct horse battery staple", raw)

            restored = MyceliaPlatform()
            restore_response = restored.restore_snapshot({"path": str(snapshot)})
            self.assertEqual(restore_response["status"], "ok", restore_response)
            self.assertGreaterEqual(restore_response["restored"], 1)

            login = restored.login_attractor(
                {"username": "Ralf", "password": "correct horse battery staple"}
            )
            self.assertEqual(login["status"], "ok", login)

            profile = restored.get_profile({"signature": login["signature"]})
            self.assertEqual(profile["status"], "ok", profile)
            self.assertEqual(profile["profile"]["vorname"], "Ralf")
            self.assertEqual(profile["profile"]["nachname"], "Krümmel")

    def test_residency_report_is_conservative_and_machine_readable(self) -> None:
        platform = MyceliaPlatform()
        report = platform.residency_report({})
        self.assertEqual(report["status"], "ok", report)
        self.assertIn("driver_mode", report)
        self.assertIn("opencl_active", report)
        self.assertIn("gpu_crypto_active", report)
        self.assertIn("strict_inflight_vram_claim", report)
        self.assertIn("cpu_cleartext_risk", report)
        self.assertIsInstance(report["strict_inflight_vram_claim"], bool)


if __name__ == "__main__":
    unittest.main()

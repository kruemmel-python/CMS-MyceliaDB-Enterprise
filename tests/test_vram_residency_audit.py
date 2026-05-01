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

from mycelia_platform import MyceliaPlatform  # noqa: E402


class VramResidencyAuditTest(unittest.TestCase):
    def setUp(self) -> None:
        self._old_env = {
            "MYCELIA_AUTOSAVE": os.environ.get("MYCELIA_AUTOSAVE"),
            "MYCELIA_AUTORESTORE": os.environ.get("MYCELIA_AUTORESTORE"),
            "MYCELIA_DIRECT_GPU_INGEST": os.environ.get("MYCELIA_DIRECT_GPU_INGEST"),
            "MYCELIA_NEGATIVE_CPU_RAM_PROBE": os.environ.get("MYCELIA_NEGATIVE_CPU_RAM_PROBE"),
        }
        os.environ["MYCELIA_AUTOSAVE"] = "0"
        os.environ["MYCELIA_AUTORESTORE"] = "0"
        os.environ.pop("MYCELIA_DIRECT_GPU_INGEST", None)
        os.environ.pop("MYCELIA_NEGATIVE_CPU_RAM_PROBE", None)

    def tearDown(self) -> None:
        for name, value in self._old_env.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def test_vram_audit_is_conservative_and_snapshot_has_no_sensitive_probe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            platform = MyceliaPlatform()
            platform.core.database.clear()
            platform.snapshot_path = Path(tmp) / "audit.mycelia"

            secret_probe = "CANARY_PROFILE_SECRET_9482"
            registered = platform.register_user({
                "username": "audit_user",
                "password": "audit-pass",
                "profile": {
                    "email": "audit@example.test",
                    "secret_note": secret_probe,
                },
            })
            self.assertEqual(registered["status"], "ok", registered)

            audit = platform.vram_residency_audit({
                "probes": [secret_probe, "audit_user"],
                "create_temp_snapshot": True,
            })
            self.assertEqual(audit["status"], "ok", audit)
            self.assertFalse(audit["strict_98_security_supported"], audit)
            self.assertTrue(audit["cpu_cleartext_risk"], audit)
            self.assertGreaterEqual(len(audit["boundary_blockers"]), 1)

            # The encrypted profile secret must not appear in the binary snapshot.
            self.assertEqual(
                [f for f in audit["snapshot_plaintext_findings"] if f["probe"].startswith("CANARY")],
                [],
                audit,
            )
            # The current architecture stores usernames as routing metadata in
            # Python-owned graph records, therefore a strict no-CPU-cleartext claim
            # must fail until direct GPU ingest and metadata encryption exist.
            self.assertTrue(
                any(f["probe"] == "audit_user" for f in audit["graph_plaintext_findings"]),
                audit,
            )

    def test_residency_report_requires_external_negative_probe(self) -> None:
        platform = MyceliaPlatform()
        report = platform.residency_report({})
        self.assertIn("strict_inflight_vram_claim", report)
        self.assertFalse(report["strict_inflight_vram_claim"])
        self.assertTrue(report["cpu_cleartext_risk"])


if __name__ == "__main__":
    unittest.main()

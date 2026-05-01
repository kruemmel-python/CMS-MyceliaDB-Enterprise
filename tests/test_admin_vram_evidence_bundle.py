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

from mycelia_platform import MyceliaPlatform  # noqa: E402


class AdminVramEvidenceBundleTest(unittest.TestCase):
    def test_bundle_matches_strict_certification_and_keeps_probe_evidence(self) -> None:
        platform = MyceliaPlatform()
        platform.autosave_enabled = False
        manifest = platform.residency_audit_manifest({})
        probe = {
            "scanner_version": "MYCELIA_CPU_RAM_PROBE_V1",
            "challenge_id": manifest["challenge_id"],
            "pid": os.getpid(),
            "probe_sha256": ["abc"],
            "hits": 0,
            "scanned_regions": 3,
            "scanned_bytes": 1024,
            "operations": ["login_attractor"],
            "evidence_digest": "unit-test",
        }
        accepted = platform.submit_external_memory_probe(probe)
        self.assertEqual(accepted["status"], "ok")

        bundle = platform.strict_vram_evidence_bundle({})
        cert = platform.strict_vram_certification({})

        self.assertEqual(bundle["status"], "ok")
        self.assertEqual(bundle["strict_vram_certification"]["strict_98_security_supported"], cert["strict_98_security_supported"])
        self.assertTrue(bundle["negative_cpu_ram_probe"])
        self.assertEqual(bundle["latest_external_memory_probe"]["evidence_digest"], "unit-test")
        self.assertIn("native_gpu_capability_report", bundle)
        self.assertIn("native_gpu_selftest", bundle)


if __name__ == "__main__":
    unittest.main()

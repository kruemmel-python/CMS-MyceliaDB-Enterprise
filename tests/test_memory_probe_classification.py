from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
HTML = ROOT / "html"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
if str(HTML) not in sys.path:
    sys.path.insert(0, str(HTML))

import mycelia_memory_probe as probe  # noqa: E402
from mycelia_platform import MyceliaPlatform  # noqa: E402


class MemoryProbeClassificationTest(unittest.TestCase):
    def setUp(self) -> None:
        self._old = dict(os.environ)
        os.environ["MYCELIA_AUTOSAVE"] = "0"
        os.environ["MYCELIA_AUTORESTORE"] = "0"

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._old)

    def test_auto_classifies_64_hex_as_public_identifier(self) -> None:
        self.assertEqual(
            probe._auto_probe_kind("4166bbf4b6c623571001321d8721b576d023c9f2299624370d2e12d1df56caf9"),
            "public_identifier",
        )
        self.assertEqual(probe._auto_probe_kind("Leipzig"), "sensitive_cleartext")

    def test_engine_ignores_public_identifier_hits_but_blocks_sensitive_hits(self) -> None:
        platform = MyceliaPlatform()
        platform.autosave_enabled = False
        fake_public_hash = "a" * 64
        public_report = {
            "status": "ok",
            "scanner_version": "MYCELIA_CPU_RAM_PROBE_V2_CLASSIFIED",
            "pid": os.getpid(),
            "challenge_id": "",
            "probe_sha256": [fake_public_hash],
            "probe_manifest": [{
                "probe_sha256": fake_public_hash,
                "probe_kind": "public_identifier",
                "strict_relevant": False,
            }],
            "hits": 1,
            "scanned_regions": 1,
            "scanned_bytes": 128,
            "findings": [{"probe_sha256": fake_public_hash, "probe_kind": "public_identifier"}],
        }
        accepted = platform.submit_external_memory_probe(public_report)["external_memory_probe"]
        self.assertEqual(accepted["hits"], 1)
        self.assertEqual(accepted["strict_hits"], 0)
        self.assertTrue(accepted["strict_negative"])

        fake_sensitive_hash = "b" * 64
        sensitive_report = {
            "status": "ok",
            "scanner_version": "MYCELIA_CPU_RAM_PROBE_V2_CLASSIFIED",
            "pid": os.getpid(),
            "challenge_id": "",
            "probe_sha256": [fake_sensitive_hash],
            "probe_manifest": [{
                "probe_sha256": fake_sensitive_hash,
                "probe_kind": "profile_cleartext",
                "strict_relevant": True,
            }],
            "hits": 1,
            "scanned_regions": 1,
            "scanned_bytes": 128,
            "findings": [{"probe_sha256": fake_sensitive_hash, "probe_kind": "profile_cleartext"}],
        }
        accepted = platform.submit_external_memory_probe(sensitive_report)["external_memory_probe"]
        self.assertEqual(accepted["strict_hits"], 1)
        self.assertFalse(accepted["strict_negative"])

    def test_legacy_unclassified_hits_remain_fail_closed(self) -> None:
        platform = MyceliaPlatform()
        platform.autosave_enabled = False
        legacy = {
            "status": "ok",
            "scanner_version": "MYCELIA_CPU_RAM_PROBE_V1",
            "pid": os.getpid(),
            "probe_sha256": ["c" * 64],
            "hits": 1,
            "scanned_regions": 1,
            "scanned_bytes": 128,
            "findings": [{"probe_sha256": "c" * 64}],
        }
        accepted = platform.submit_external_memory_probe(legacy)["external_memory_probe"]
        self.assertEqual(accepted["strict_hits"], 1)
        self.assertFalse(accepted["negative"])


if __name__ == "__main__":
    unittest.main()

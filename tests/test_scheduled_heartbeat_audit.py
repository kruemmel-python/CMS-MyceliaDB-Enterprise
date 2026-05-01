from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "html"
if str(HTML) not in sys.path:
    sys.path.insert(0, str(HTML))

os.environ["MYCELIA_AUTOSAVE"] = "0"
os.environ["MYCELIA_AUTORESTORE"] = "0"

import mycelia_platform as platform  # noqa: E402
from mycelia_platform import MyceliaPlatform  # noqa: E402


def canonical(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


class HeartbeatAuditStatusTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        platform.HEARTBEAT_AUDIT_LATEST_PATH = self.root / "heartbeat_audit_latest.json"
        platform.HEARTBEAT_PUBLIC_KEY_PATH = self.root / "heartbeat_ed25519_public.pem"
        platform.HEARTBEAT_MAX_AGE_SECONDS = 3600
        self.db = MyceliaPlatform()
        self.db.autosave_enabled = False
        self.db.core.database.clear()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_signed_heartbeat_is_verified_and_reported_certified(self) -> None:
        key = ed25519.Ed25519PrivateKey.generate()
        platform.HEARTBEAT_PUBLIC_KEY_PATH.write_bytes(key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ))
        signed_payload = {
            "tool_version": "TEST_HEARTBEAT",
            "created_at": time.time(),
            "pid": os.getpid(),
            "challenge_id": "abc",
            "driver_mode": "opencl:test+native-vram",
            "secret_sha256": "00" * 32,
            "probe_evidence_digest": "11" * 32,
            "strict_vram_evidence_bundle": {
                "pid": os.getpid(),
                "driver_mode": "opencl:test+native-vram",
                "strict_98_security_supported": True,
                "negative_cpu_ram_probe": True,
                "last_restore_cpu_materialized": False,
                "strict_vram_certification": {
                    "strict_98_security_supported": True,
                    "blockers": [],
                },
                "latest_external_memory_probe": {
                    "strict_negative": True,
                    "strict_hits": 0,
                    "evidence_digest": "11" * 32,
                },
            },
        }
        envelope = {
            "signed_payload": signed_payload,
            "signature_b64": base64.b64encode(key.sign(canonical(signed_payload))).decode("ascii"),
        }
        accepted = self.db.submit_heartbeat_audit(envelope)
        self.assertEqual(accepted["status"], "ok", accepted)
        self.assertTrue(accepted["heartbeat_audit"]["summary"]["certified"])
        self.assertTrue(accepted["heartbeat_audit"]["signature"]["signature_trusted"])
        self.assertTrue(platform.HEARTBEAT_AUDIT_LATEST_PATH.exists())

        status = self.db.heartbeat_audit_status({})
        self.assertEqual(status["status"], "ok", status)
        self.assertTrue(status["heartbeat_present"])
        self.assertTrue(status["certified"])
        self.assertEqual(status["display"]["value"], "ZERTIFIZIERT")

    def test_unsigned_or_untrusted_heartbeat_is_not_certified(self) -> None:
        signed_payload = {
            "tool_version": "TEST_HEARTBEAT",
            "created_at": time.time(),
            "pid": os.getpid(),
            "strict_vram_evidence_bundle": {
                "strict_98_security_supported": True,
                "negative_cpu_ram_probe": True,
                "last_restore_cpu_materialized": False,
                "latest_external_memory_probe": {"strict_negative": True, "strict_hits": 0},
            },
        }
        accepted = self.db.submit_heartbeat_audit({"signed_payload": signed_payload, "signature_b64": ""})
        self.assertEqual(accepted["status"], "ok", accepted)
        self.assertFalse(accepted["heartbeat_audit"]["summary"]["certified"])
        self.assertFalse(self.db.heartbeat_audit_status({})["certified"])


if __name__ == "__main__":
    unittest.main()

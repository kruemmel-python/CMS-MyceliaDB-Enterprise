from __future__ import annotations

import hashlib
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "html"
if str(HTML) not in sys.path:
    sys.path.insert(0, str(HTML))

from mycelia_platform import MyceliaPlatform, MEMORY_PROBE_TOOL  # noqa: E402


class ExternalResidencyEvidenceTest(unittest.TestCase):
    def setUp(self) -> None:
        self._old_env = {
            "MYCELIA_AUTOSAVE": os.environ.get("MYCELIA_AUTOSAVE"),
            "MYCELIA_AUTORESTORE": os.environ.get("MYCELIA_AUTORESTORE"),
            "MYCELIA_STRICT_VRAM_CERTIFICATION": os.environ.get("MYCELIA_STRICT_VRAM_CERTIFICATION"),
            "MYCELIA_NATIVE_GPU_ENVELOPE_OPENER": os.environ.get("MYCELIA_NATIVE_GPU_ENVELOPE_OPENER"),
            "MYCELIA_GPU_RESTORE_OPENER": os.environ.get("MYCELIA_GPU_RESTORE_OPENER"),
        }
        os.environ["MYCELIA_AUTOSAVE"] = "0"
        os.environ["MYCELIA_AUTORESTORE"] = "0"
        os.environ["MYCELIA_STRICT_VRAM_CERTIFICATION"] = "0"
        os.environ["MYCELIA_NATIVE_GPU_ENVELOPE_OPENER"] = "0"
        os.environ["MYCELIA_GPU_RESTORE_OPENER"] = "0"

    def tearDown(self) -> None:
        for key, value in self._old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_manifest_requires_external_probe_without_plaintext_submission(self) -> None:
        platform = MyceliaPlatform()
        manifest = platform.residency_audit_manifest({})
        self.assertEqual(manifest["status"], "ok")
        self.assertEqual(manifest["pid"], os.getpid())
        self.assertIn("mycelia_memory_probe.py", manifest["memory_probe_tool"])
        self.assertTrue(Path(manifest["memory_probe_tool"]).exists())
        self.assertFalse(manifest["capabilities"]["native_gpu_envelope_opener"])
        self.assertIn("Do not send plaintext probes", manifest["probe_submission_rule"])

    def test_negative_external_probe_is_evidence_but_not_strict_without_native_gpu_openers(self) -> None:
        platform = MyceliaPlatform()
        manifest = platform.residency_audit_manifest({})
        fake_report = {
            "scanner_version": "MYCELIA_CPU_RAM_PROBE_V1",
            "challenge_id": manifest["challenge_id"],
            "pid": os.getpid(),
            "probe_sha256": [hashlib.sha256(b"Kr\xfcmmel").hexdigest()],
            "hits": 0,
            "scanned_regions": 42,
            "scanned_bytes": 4096,
            "operations": ["login_attractor", "restore_snapshot"],
            "evidence_digest": "unit-test",
        }
        accepted = platform.submit_external_memory_probe(fake_report)
        self.assertEqual(accepted["status"], "ok")
        self.assertTrue(accepted["external_memory_probe"]["negative"])
        self.assertFalse(accepted["strict_98_security_supported"])
        report = platform.residency_report({})
        self.assertTrue(report["negative_cpu_ram_probe"])
        self.assertFalse(report["strict_inflight_vram_claim"])
        self.assertTrue(report["python_cpu_decrypt_materialized"])

    def test_restore_residency_audit_marks_python_cpu_materialization(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            platform = MyceliaPlatform()
            platform.core.database.clear()
            platform.snapshot_path = Path(tmp) / "autosave.mycelia"
            platform.register_user({
                "username": "Ralf",
                "password": "Krümmel",
                "email": "ralf@example.test",
                "profile": {"city": "Leipzig"},
            })
            platform.create_snapshot({"path": str(platform.snapshot_path)})

            restored = MyceliaPlatform()
            restored.core.database.clear()
            result = restored.restore_snapshot_residency_audit({"path": str(platform.snapshot_path)})
            self.assertEqual(result["status"], "ok")
            self.assertTrue(result["after"]["last_restore_cpu_materialized"])
            self.assertFalse(result["strict_restore_residency_supported"])
            self.assertIn("CPU-materialized", result["conclusion"])


if __name__ == "__main__":
    unittest.main()

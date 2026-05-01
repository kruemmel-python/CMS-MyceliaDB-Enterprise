
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


class NativeGPUResidencyContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self._old_env = dict(os.environ)
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["MYCELIA_SNAPSHOT_PATH"] = str(Path(self.tmp.name) / "autosave.mycelia")
        os.environ["MYCELIA_AUTORESTORE"] = "0"
        os.environ["MYCELIA_AUTOSAVE"] = "0"
        os.environ["MYCELIA_GPU_ENVELOPE_LIBRARY"] = str(Path(self.tmp.name) / "missing_mycelia_gpu_envelope.dll")
        os.environ["MYCELIA_NATIVE_GPU_ENVELOPE_OPENER"] = "1"
        os.environ["MYCELIA_GPU_RESTORE_OPENER"] = "1"
        os.environ["MYCELIA_STRICT_VRAM_CERTIFICATION"] = "1"

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._old_env)
        self.tmp.cleanup()

    def test_native_gpu_report_refuses_to_certify_without_native_exports(self) -> None:
        from mycelia_platform import MyceliaPlatform

        platform = MyceliaPlatform()
        report = platform.native_gpu_capability_report({})

        self.assertEqual(report["status"], "ok")
        self.assertFalse(report["strict_native_prerequisites_met"])
        self.assertTrue(report["blockers"])
        self.assertIn("native_bridge", report)
        self.assertFalse(report["native_bridge"]["available"])

    def test_strict_certification_requires_native_bridge_and_negative_external_probe(self) -> None:
        from mycelia_platform import MyceliaPlatform

        platform = MyceliaPlatform()
        platform.latest_external_memory_probe = {
            "scanner_version": "MYCELIA_CPU_RAM_PROBE_V1",
            "pid": os.getpid(),
            "negative": True,
            "total_hits": 0,
        }
        report = platform.strict_vram_certification({})

        self.assertEqual(report["status"], "ok")
        self.assertFalse(report["strict_98_security_supported"])
        self.assertIn("blockers", report)
        self.assertTrue(any("Native GPU" in item or "Direct-Ingest" in item or "Snapshots" in item for item in report["blockers"]))


if __name__ == "__main__":
    unittest.main()

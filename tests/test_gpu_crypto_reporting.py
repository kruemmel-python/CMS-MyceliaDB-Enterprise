from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "html"
if str(HTML) not in sys.path:
    sys.path.insert(0, str(HTML))

os.environ.setdefault("MYCELIA_AUTORESTORE", "0")
os.environ.setdefault("MYCELIA_AUTOSAVE", "0")

from mycelia_platform import MyceliaPlatform  # noqa: E402


class GpuCryptoReportingTest(unittest.TestCase):
    def test_native_envelope_counts_as_gpu_crypto_in_reports(self) -> None:
        platform = MyceliaPlatform()
        platform.autosave_enabled = False
        platform.driver_mode = "opencl:unit-test"
        platform._native_envelope_to_vram_enabled = lambda: True  # type: ignore[method-assign]
        platform._gpu_restore_to_vram_enabled = lambda: True  # type: ignore[method-assign]

        report = platform.residency_report({})
        self.assertTrue(report["opencl_active"])
        self.assertFalse(report["core_gpu_crypto_active"])
        self.assertTrue(report["native_envelope_crypto_active"])
        self.assertTrue(report["gpu_crypto_active"])

        manifest = platform.residency_audit_manifest({})
        caps = manifest["capabilities"]
        self.assertFalse(caps["core_gpu_crypto_active"])
        self.assertTrue(caps["native_envelope_crypto_active"])
        self.assertTrue(caps["gpu_crypto_active"])


if __name__ == "__main__":
    unittest.main()

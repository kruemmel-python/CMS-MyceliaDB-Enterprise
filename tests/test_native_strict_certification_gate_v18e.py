from __future__ import annotations

import ctypes
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "html" / "native" / "mycelia_gpu_envelope_contract.c"
PLATFORM = ROOT / "html" / "mycelia_platform.py"
PROBE_SCRIPT = ROOT / "tools" / "run_v18e_external_ram_probe.ps1"


class NativeStrictCertificationGateV18ETest(unittest.TestCase):
    def test_source_declares_strict_gate_exports_and_fail_closed_flags(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("MYCELIA_NATIVE_VRAM_OPEN_RESTORE_V1_18F", source)
        self.assertIn("mycelia_gpu_strict_residency_evidence_v1", source)
        self.assertIn("mycelia_gpu_external_probe_contract_v1", source)
        self.assertIn('"native_strict_certification_gate\\":true', source)
        self.assertIn('"external_ram_probe_contract\\":true', source)
        self.assertIn("gpu_resident_open_restore_proven", source)
        self.assertIn("envelope_to_vram", source)
        self.assertIn("snapshot_to_vram", source)
        self.assertIn("gpu_digest_evidence", source)

    def test_platform_knows_strict_gate_exports(self) -> None:
        text = PLATFORM.read_text(encoding="utf-8")
        self.assertIn("VRAM_RESIDENCY_AUDIT_V11_GPU_RESIDENT_OPEN_RESTORE", text)
        self.assertIn("mycelia_gpu_strict_residency_evidence_v1", text)
        self.assertIn("mycelia_gpu_external_probe_contract_v1", text)
        self.assertIn("native_strict_certification_gate", text)
        self.assertIn("external_ram_probe_contract", text)

    def test_external_probe_powershell_orchestrator_exists(self) -> None:
        text = PROBE_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("mycelia_memory_probe.py", text)
        self.assertIn("mycelia_strict_vram_certify.py", text)
        self.assertIn("mycelia_platform.py", text)

    def test_compiled_strict_gate_reports_fail_closed(self) -> None:
        compiler = shutil.which("gcc") or shutil.which("clang")
        if not compiler:
            self.skipTest("No C compiler available for native smoke test")
        with tempfile.TemporaryDirectory() as tmp:
            dll = Path(tmp) / "mycelia_gpu_envelope.dll"
            result = subprocess.run([compiler, "-shared", "-fPIC", str(SOURCE), "-o", str(dll)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            lib = ctypes.CDLL(str(dll))
            fn = lib.mycelia_gpu_strict_residency_evidence_v1
            fn.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_size_t]
            fn.restype = ctypes.c_int
            out = ctypes.create_string_buffer(65536)
            rc = fn(b'{"version":"test"}', out, ctypes.sizeof(out))
            self.assertEqual(rc, 0)
            report = json.loads(out.value.decode("utf-8"))
            self.assertTrue(report["native_strict_certification_gate"])
            self.assertTrue(report["external_ram_probe_contract"])
            self.assertIn("gpu_resident_open_restore_proven", report)
            self.assertIn("envelope_to_vram", report)
            self.assertIn("snapshot_to_vram", report)
            self.assertIn("selftest_passed", report)
            self.assertFalse(report["plaintext_returned_to_python"])


if __name__ == "__main__":
    unittest.main()

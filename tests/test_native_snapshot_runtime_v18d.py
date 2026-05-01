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


class NativeSnapshotRuntimeV18DTest(unittest.TestCase):
    def test_native_source_declares_snapshot_runtime_and_build_script(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("MYCELIA_NATIVE_SNAPSHOT_RUNTIME_V1_18D", source)
        self.assertIn('"native_snapshot_runtime\\":true', source)
        self.assertIn('"native_persistence_mutation\\":true', source)
        self.assertTrue((ROOT / "html" / "native" / "build_native_gpu_envelope.ps1").exists())

    def test_compiled_snapshot_runtime_exports_safe_results_only(self) -> None:
        compiler = shutil.which("gcc") or shutil.which("clang")
        if not compiler:
            self.skipTest("No C compiler available")
        with tempfile.TemporaryDirectory() as tmp:
            lib_path = Path(tmp) / "libmycelia_gpu_envelope.so"
            result = subprocess.run([compiler, "-shared", "-fPIC", str(SOURCE), "-o", str(lib_path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            lib = ctypes.CDLL(str(lib_path))
            for export in [
                "mycelia_gpu_snapshot_runtime_capabilities_v1",
                "mycelia_gpu_persist_mutation_v1",
                "mycelia_gpu_snapshot_commit_v1",
                "mycelia_gpu_snapshot_restore_to_vram_v1",
            ]:
                self.assertTrue(hasattr(lib, export), export)

            caps_fn = lib.mycelia_gpu_snapshot_runtime_capabilities_v1
            caps_fn.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_size_t]
            caps_fn.restype = ctypes.c_int
            out = ctypes.create_string_buffer(65536)
            rc = caps_fn(b'{"version":"test"}', out, ctypes.sizeof(out))
            self.assertEqual(rc, 0)
            caps = json.loads(out.value.decode("utf-8"))
            self.assertTrue(caps["native_snapshot_runtime"])
            self.assertTrue(caps["native_persistence_mutation"])
            self.assertFalse(caps["plaintext_returned_to_python"])
            self.assertFalse(caps["graph_payload_returned"])

            mut_fn = lib.mycelia_gpu_persist_mutation_v1
            mut_fn.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_size_t]
            mut_fn.restype = ctypes.c_int
            out = ctypes.create_string_buffer(65536)
            rc = mut_fn(b'{"op":"native_persist_mutation","opaque_handle":"mut-test"}', out, ctypes.sizeof(out))
            self.assertEqual(rc, 0)
            mutation = json.loads(out.value.decode("utf-8"))
            self.assertTrue(mutation["native_persistence_mutation"])
            self.assertFalse(mutation["plaintext_returned_to_python"])
            self.assertFalse(mutation["graph_payload_returned"])
            self.assertFalse(mutation["mutation_descriptor_returned"])

            commit_fn = lib.mycelia_gpu_snapshot_commit_v1
            commit_fn.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_size_t]
            commit_fn.restype = ctypes.c_int
            out = ctypes.create_string_buffer(65536)
            rc = commit_fn(b'{"op":"native_snapshot_commit","opaque_graph_handle":"graph-test"}', out, ctypes.sizeof(out))
            self.assertEqual(rc, 0)
            commit = json.loads(out.value.decode("utf-8"))
            self.assertTrue(commit["native_snapshot_runtime"])
            self.assertFalse(commit["snapshot_payload_returned"])
            self.assertFalse(commit["graph_payload_returned"])


if __name__ == "__main__":
    unittest.main()

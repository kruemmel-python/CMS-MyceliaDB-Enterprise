from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "html"
if str(HTML) not in sys.path:
    sys.path.insert(0, str(HTML))


class NativeStartupPathsTest(unittest.TestCase):
    def test_native_envelope_candidate_paths_include_html_native(self) -> None:
        import mycelia_platform

        candidates = [str(p) for p in mycelia_platform.NativeGPUResidencyBridge.candidate_paths()]
        expected = str((HTML / "native" / "mycelia_gpu_envelope.dll").resolve())
        if sys.platform == "win32":
            self.assertIn(expected, candidates)

    def test_chat_engine_message_is_explicit_about_cc_opencl(self) -> None:
        source = (HTML / "mycelia_chat_engine.py").read_text(encoding="utf-8")
        self.assertIn("CC_OpenCl/libopencl_driver", source)
        self.assertIn("mycelia_gpu_envelope.dll", source)


if __name__ == "__main__":
    unittest.main()

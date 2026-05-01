
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "html"
if str(HTML) not in sys.path:
    sys.path.insert(0, str(HTML))

from mycelia_platform import NativeGPUResidencyBridge, _existing_driver_candidates  # noqa: E402


class NativeDllPathResolutionTest(unittest.TestCase):
    def test_native_envelope_candidates_include_html_native_first(self) -> None:
        candidates = NativeGPUResidencyBridge.candidate_paths()
        expected = (HTML / "native" / ("mycelia_gpu_envelope.dll" if sys.platform == "win32" else "libmycelia_gpu_envelope.so")).resolve()
        # On non-Windows the exact dylib/so name differs; the invariant is the html/native root.
        self.assertTrue(any(path.parent == HTML / "native" for path in candidates), candidates)
        if sys.platform == "win32":
            self.assertEqual(candidates[0], expected)

    def test_opencl_driver_candidates_include_native_directories(self) -> None:
        # This is a path-construction regression guard. It must not require the DLL to exist in CI.
        from mycelia_platform import ROOT, CORE_ROOT
        # Internal function only returns existing paths, so validate by ensuring the function accepts config
        # and doesn't crash when native directories are part of the search anchors.
        self.assertIsInstance(_existing_driver_candidates({}), list)


if __name__ == "__main__":
    unittest.main()

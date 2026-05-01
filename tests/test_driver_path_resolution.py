from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "html"
if str(HTML) not in sys.path:
    sys.path.insert(0, str(HTML))

import mycelia_platform


class DriverPathResolutionTest(unittest.TestCase):
    def test_resolves_driver_from_core_build_not_cwd_only(self) -> None:
        core_driver = ROOT / "Mycelia_Database-main" / "build" / "CC_OpenCl.dll"
        if not core_driver.exists():
            self.skipTest("Core OpenCL driver DLL is not bundled in clean source package")
        path = mycelia_platform.resolve_core_driver_library(
            {"driver_library_windows": ".\\build\\CC_OpenCl.dll"}
        )
        self.assertTrue(path.exists())
        self.assertIn("Mycelia_Database-main", str(path))
        self.assertEqual(path.name, "CC_OpenCl.dll")


if __name__ == "__main__":
    unittest.main()

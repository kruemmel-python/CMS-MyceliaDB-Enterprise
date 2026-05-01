import importlib.util
import pathlib
import sys
import unittest


class ShutdownSemanticsTest(unittest.TestCase):
    def test_server_uses_reusable_address_class(self) -> None:
        module_path = pathlib.Path(__file__).resolve().parents[1] / "html" / "mycelia_platform.py"
        spec = importlib.util.spec_from_file_location("mycelia_platform_shutdown_test", module_path)
        self.assertIsNotNone(spec)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        self.assertTrue(module.MyceliaTCPServer.allow_reuse_address)


if __name__ == "__main__":
    unittest.main()

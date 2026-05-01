
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "www" / "bootstrap.php"


class DirectIngestTokenDisciplineHotfixTest(unittest.TestCase):
    def test_require_login_does_not_rotate_before_sealed_direct_ingest(self) -> None:
        src = BOOTSTRAP.read_text(encoding="utf-8")
        self.assertIn("function is_direct_ingest_post()", src)
        self.assertIn("if (is_direct_ingest_post())", src)
        self.assertIn("The Engine performs the real authorization inside direct_ingest()", src)
        require_login_pos = src.index("function require_login()")
        skip_pos = src.index("if (is_direct_ingest_post())", require_login_pos)
        validate_pos = src.index("call_mycelia('validate_session'", require_login_pos)
        self.assertLess(skip_pos, validate_pos)

    def test_zero_logic_gateway_still_allows_sealed_forms(self) -> None:
        src = BOOTSTRAP.read_text(encoding="utf-8")
        self.assertIn("!empty($_POST['sealed_ingest']) && !empty($_POST['direct_op'])", src)
        self.assertIn("Klartext-POSTs sind deaktiviert", src)


if __name__ == "__main__":
    unittest.main()

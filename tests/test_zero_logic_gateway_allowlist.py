from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ZeroLogicGatewayAllowlistTest(unittest.TestCase):
    def test_every_non_direct_admin_post_control_is_allowlisted(self) -> None:
        admin = (ROOT / "www" / "admin.php").read_text(encoding="utf-8")
        bootstrap = (ROOT / "www" / "bootstrap.php").read_text(encoding="utf-8")

        forms = re.findall(r'<form[^>]*method="post"[^>]*>.*?</form>', admin, flags=re.S)
        non_direct_controls: set[str] = set()
        for form in forms:
            if "data-direct-op" in form:
                continue
            # Textarea names such as memory_probe_json are payload fields. The
            # submit button name is the actual Zero-Logic control key.
            buttons = re.findall(r'<button[^>]*name="([^"]+)"', form, flags=re.S)
            non_direct_controls.update(buttons)

        self.assertIn("run_vram_evidence_bundle", non_direct_controls)
        missing = [name for name in sorted(non_direct_controls) if f"'{name}'" not in bootstrap and f'"{name}"' not in bootstrap]
        self.assertEqual(missing, [], f"Non-direct admin POST controls missing from Zero-Logic allowlist: {missing}")


if __name__ == "__main__":
    unittest.main()

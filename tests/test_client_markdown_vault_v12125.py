from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "html"
if str(HTML) not in sys.path:
    sys.path.insert(0, str(HTML))

os.environ["MYCELIA_AUTOSAVE"] = "0"
os.environ["MYCELIA_AUTORESTORE"] = "0"

from mycelia_platform import MyceliaPlatform  # noqa: E402


def vault(field: str, marker: str) -> str:
    return json.dumps({
        "version": "client_markdown_vault_v1",
        "alg": "PBKDF2-SHA256/AES-256-GCM",
        "field": field,
        "markdown": True,
        "display_vault": True,
        "aad": f"myceliadb-client-markdown-vault-v1|test|{field}",
        "salt_b64": "AAAAAAAAAAAAAAAAAAAAAA==",
        "iv_b64": "AAAAAAAAAAAAAAAA",
        "ciphertext_b64": "AQIDBAUGBwgJ",
        "sha256": "0" * 64,
        "created_at_ms": 1,
        "marker_for_test_not_secret": marker,
    })


class ClientMarkdownVaultV12125Test(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = MyceliaPlatform()
        self.db.core.database.clear()
        self.db.snapshot_path = Path(self.tmp.name) / "vault.mycelia"
        self.db.autosave_enabled = False
        self.user = self.db.register_user({"username": "vault_user", "password": "pw", "profile": {"role": "user"}})
        self.ctx = {
            "actor_signature": self.user["signature"],
            "actor_username": "vault_user",
            "actor_role": "user",
            "author_signature": self.user["signature"],
            "author_username": "vault_user",
        }

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_forum_thread_vault_response_contains_no_plaintext_body(self) -> None:
        secret = "MYCELIA_SECRET_MARKDOWN_VAULT_BODY"
        created = self.db.create_forum_thread({**self.ctx, "title": "Vault", "body_vault_json": vault("body", secret)})
        self.assertEqual(created["status"], "ok", created)
        got = self.db.get_forum_thread({"signature": created["signature"]})
        self.assertEqual(got["status"], "ok", got)
        thread = got["thread"]
        self.assertIn("body_vault", thread)
        self.assertNotIn("body", thread)
        self.assertNotIn("body_html", thread)
        self.assertFalse(thread["engine_display_plaintext_materialized"])
        self.assertNotIn(secret, json.dumps(thread, ensure_ascii=False))

    def test_blog_description_vault_response_contains_no_plaintext_description(self) -> None:
        secret = "MYCELIA_SECRET_MARKDOWN_VAULT_DESCRIPTION"
        created = self.db.create_blog({**self.ctx, "owner_signature": self.user["signature"], "owner_username": "vault_user", "title": "Vault Blog", "description_vault_json": vault("description", secret)})
        self.assertEqual(created["status"], "ok", created)
        got = self.db.get_blog({"signature": created["signature"]})
        self.assertEqual(got["status"], "ok", got)
        blog = got["blog"]
        self.assertIn("description_vault", blog)
        self.assertNotIn("description", blog)
        self.assertNotIn("description_html", blog)
        self.assertFalse(blog["engine_display_plaintext_materialized"])
        self.assertNotIn(secret, json.dumps(blog, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()

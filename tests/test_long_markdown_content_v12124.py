from __future__ import annotations

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


class LongMarkdownContentV12124Test(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["MYCELIA_SNAPSHOT_PATH"] = str(Path(self.tmp.name) / "autosave.mycelia")
        self.db = MyceliaPlatform()
        self.db.autosave_enabled = False
        self.db.core.database.clear()
        self.user = self.db.register_user({"username": "longform", "password": "pw", "profile": {"role": "user"}})
        self.sig = self.user["signature"]

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_forum_thread_keeps_document_sized_markdown_body(self) -> None:
        block = "Zeile mit langem Inhalt und `inline code`.\n"
        body = "# Sehr langer Beitrag\n\n" + (block * 7000) + "\n```powershell\nWrite-Host 'copy me'\n```\n"
        created = self.db.create_forum_thread({
            "author_signature": self.sig,
            "author_username": "longform",
            "actor_role": "user",
            "title": "Long Markdown",
            "body": body,
        })
        self.assertEqual(created["status"], "ok", created)
        got = self.db.get_forum_thread({"signature": created["signature"]})
        self.assertEqual(got["status"], "ok", got)
        self.assertEqual(got["thread"]["body"], body.strip())
        html = got["thread"]["body_html"]["text"]
        self.assertIn("Write-Host", html)
        self.assertIn("md-codeblock", html)
        self.assertNotIn("[gekürzt", html)

    def test_blog_description_keeps_more_than_legacy_1000_chars(self) -> None:
        description = "## Langer Blog\n\n" + ("Absatz mit Dokumentation.\n\n" * 900)
        created = self.db.create_blog({
            "actor_signature": self.sig,
            "actor_username": "longform",
            "actor_role": "user",
            "owner_signature": self.sig,
            "owner_username": "longform",
            "title": "Long Blog",
            "description": description,
        })
        self.assertEqual(created["status"], "ok", created)
        got = self.db.get_blog({"signature": created["signature"]})
        self.assertEqual(got["status"], "ok", got)
        self.assertEqual(got["blog"]["description"], description.strip())
        self.assertGreater(len(got["blog"]["description"]), 1000)
        self.assertNotIn("[gekürzt", got["blog"]["description_html"]["text"])


if __name__ == "__main__":
    unittest.main()

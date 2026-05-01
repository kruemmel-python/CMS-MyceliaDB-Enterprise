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


class MarkdownRenderingV12123Test(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["MYCELIA_SNAPSHOT_PATH"] = str(Path(self.tmp.name) / "autosave.mycelia")
        self.db = MyceliaPlatform()
        self.db.autosave_enabled = False
        self.db.core.database.clear()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_engine_markdown_fragment_renders_codeblock_safely(self) -> None:
        fragment = self.db._markdown_fragment("""# Titel

> Hinweis

```powershell
cd D:\\web
python mycelia_platform.py
```

- eins
- zwei
""")
        self.assertEqual(fragment["policy"], "engine-safe-markdown-html")
        html = fragment["text"]
        self.assertIn("<h1>Titel</h1>", html)
        self.assertIn("md-copy-code", html)
        self.assertIn("language-powershell", html)
        self.assertIn("cd D:\\web", html)
        self.assertIn("<blockquote>", html)
        self.assertIn("<ul>", html)

    def test_forum_thread_returns_markdown_html_without_raw_html_passthrough(self) -> None:
        user = self.db.register_user({"username": "mduser", "password": "pw", "profile": {"role": "user"}})
        thread = self.db.create_forum_thread({
            "author_signature": user["signature"],
            "author_username": "mduser",
            "actor_role": "user",
            "title": "Markdown",
            "body": "# Hallo\n\n<script>alert(1)</script>\n\n```python\nprint('ok')\n```",
        })
        self.assertEqual(thread["status"], "ok", thread)
        got = self.db.get_forum_thread({"signature": thread["signature"]})
        fragment = got["thread"]["body_html"]
        self.assertEqual(fragment["policy"], "engine-safe-markdown-html")
        rendered = fragment["text"]
        self.assertIn("<h1>Hallo</h1>", rendered)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", rendered)
        self.assertNotIn("<script>alert(1)</script>", rendered)
        self.assertIn("md-copy-code", rendered)


if __name__ == "__main__":
    unittest.main()

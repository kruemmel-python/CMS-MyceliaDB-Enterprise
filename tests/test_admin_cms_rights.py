
import os
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "html"
if str(HTML) not in sys.path:
    sys.path.insert(0, str(HTML))

os.environ["MYCELIA_AUTORESTORE"] = "0"
os.environ["MYCELIA_AUTOSAVE"] = "0"

from mycelia_platform import MyceliaPlatform  # noqa: E402


class AdminCmsRightsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["MYCELIA_SNAPSHOT_PATH"] = str(Path(self.tmp.name) / "autosave.mycelia")
        self.db = MyceliaPlatform()
        self.db.autosave_enabled = False
        self.admin = self.db.register_user({"username": "admin", "password": "secret", "profile": {"role": "admin"}})
        self.user = self.db.register_user({"username": "alice", "password": "secret", "profile": {"role": "user"}})
        self.admin_login = self.db.login_attractor({"username": "admin", "password": "secret"})
        self.user_login = self.db.login_attractor({"username": "alice", "password": "secret"})

    def tearDown(self):
        self.tmp.cleanup()

    def _ctx(self, login):
        return {
            "engine_session_handle": login["engine_session"]["handle"],
            "engine_request_token": login["engine_session"]["request_token"],
        }

    def test_admin_can_edit_site_text_and_snapshot_roundtrip(self):
        ctx = self._ctx(self.admin_login)
        res = self.db.dispatch("admin_set_site_text", {
            **ctx,
            "key": "home.title",
            "value": "Mycelia Sovereign Portal",
            "context": "web",
        })
        self.assertEqual(res["status"], "ok", res)

        texts = self.db.dispatch("list_site_texts", {})
        self.assertEqual(texts["texts"]["home.title"]["value"], "Mycelia Sovereign Portal")
        snap = self.db.create_snapshot({"path": str(Path(self.tmp.name) / "cms.mycelia")})
        self.assertEqual(snap["status"], "ok")
        raw = Path(snap["path"]).read_bytes()
        self.assertNotIn(b"Mycelia Sovereign Portal", raw)

        fresh = MyceliaPlatform()
        fresh.autosave_enabled = False
        restored = fresh.restore_snapshot({"path": snap["path"]})
        self.assertEqual(restored["status"], "ok")
        restored_texts = fresh.list_site_texts({})
        self.assertEqual(restored_texts["texts"]["home.title"]["value"], "Mycelia Sovereign Portal")

    def test_admin_can_revoke_forum_creation_and_user_is_blocked_without_relogin(self):
        # User can create before revocation.
        ctx_user = self._ctx(self.user_login)
        created = self.db.dispatch("create_forum_thread", {**ctx_user, "title": "A", "body": "B"})
        self.assertEqual(created["status"], "ok", created)

        # Admin revokes forum.create from Alice.
        ctx_admin = self._ctx(self.admin_login)
        rights = self.db.dispatch("admin_update_user_rights", {
            **ctx_admin,
            "signature": self.user["signature"],
            "role": "user",
            "permissions": ["profile.update"],
        })
        self.assertEqual(rights["status"], "ok", rights)

        # Existing session is refreshed by the Engine and loses forum.create.
        ctx_user = {
            "engine_session_handle": ctx_user["engine_session_handle"],
            "engine_request_token": created["engine_session"]["request_token"],
        }
        blocked = self.db.dispatch("create_forum_thread", {**ctx_user, "title": "C", "body": "D"})
        self.assertEqual(blocked["status"], "error")
        self.assertIn("forum.create", blocked["message"])


if __name__ == "__main__":
    unittest.main()

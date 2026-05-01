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


class PluginAttractorSystemTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["MYCELIA_SNAPSHOT_PATH"] = str(Path(self.tmp.name) / "autosave.mycelia")
        self.db = MyceliaPlatform()
        self.db.autosave_enabled = False
        self.db.core.database.clear()
        self.admin_reg = self.db.register_user({"username": "admin", "password": "secret", "profile": {"role": "admin"}})
        self.user_reg = self.db.register_user({"username": "alice", "password": "secret", "profile": {"role": "user"}})
        self.admin_login = self.db.login_attractor({"username": "admin", "password": "secret"})
        self.user_login = self.db.login_attractor({"username": "alice", "password": "secret"})

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _ctx(self, login: dict) -> dict:
        return {
            "engine_session_handle": login["engine_session"]["handle"],
            "engine_request_token": login["engine_session"]["request_token"],
        }

    def _apply(self, login: dict, response: dict) -> dict:
        if isinstance(response.get("engine_session"), dict):
            login["engine_session"] = response["engine_session"]
        return response

    def _manifest(self, plugin_id: str = "anonymous_stats") -> dict:
        return {
            "plugin_id": plugin_id,
            "name": "Anonyme Statistiken",
            "version": "1.0.0",
            "description": "Nur sichere Aggregate ohne Rohdatenzugriff.",
            "author": "Mycelia QA",
            "hooks": ["admin.dashboard"],
            "capabilities": ["stats.user.count", "stats.forum.count", "stats.blog_post.count"],
            "constraints": {"max_records": 10000, "tension_threshold": 0.72},
            "outputs": [{"key": "summary", "type": "metric_cards"}],
        }

    def test_admin_installs_enables_runs_and_deletes_safe_plugin(self) -> None:
        # Create a few records so aggregate outputs are meaningful.
        user_ctx = self._ctx(self.user_login)
        created = self.db.dispatch("create_forum_thread", {**user_ctx, "title": "Hello", "body": "secret body should not leak"})
        self.assertEqual(created["status"], "ok", created)
        self._apply(self.user_login, created)

        admin_ctx = self._ctx(self.admin_login)
        install = self.db.dispatch("admin_install_plugin", {**admin_ctx, "manifest_json": json.dumps(self._manifest())})
        self.assertEqual(install["status"], "ok", install)
        self._apply(self.admin_login, install)
        self.assertFalse(install["enabled"])
        signature = install["signature"]

        plugins = self.db.dispatch("list_plugins", {**self._ctx(self.admin_login)})
        self.assertEqual(plugins["status"], "ok", plugins)
        self._apply(self.admin_login, plugins)
        self.assertEqual(len(plugins["plugins"]), 1)
        self.assertEqual(plugins["plugins"][0]["plugin_id"], "anonymous_stats")

        enable = self.db.dispatch("admin_set_plugin_state", {**self._ctx(self.admin_login), "signature": signature, "enabled": True})
        self.assertEqual(enable["status"], "ok", enable)
        self._apply(self.admin_login, enable)

        run = self.db.dispatch("run_plugin", {**self._ctx(self.admin_login), "signature": signature})
        self.assertEqual(run["status"], "ok", run)
        self._apply(self.admin_login, run)
        self.assertEqual(run["plugin"]["raw_records_returned"], 0)
        rendered = json.dumps(run, ensure_ascii=False)
        self.assertNotIn("secret body should not leak", rendered)
        self.assertIn("stats.user.count", rendered)

        delete = self.db.dispatch("admin_delete_plugin", {**self._ctx(self.admin_login), "signature": signature})
        self.assertEqual(delete["status"], "ok", delete)
        self._apply(self.admin_login, delete)
        listed = self.db.dispatch("list_plugins", {**self._ctx(self.admin_login)})
        self.assertEqual(listed["status"], "ok", listed)
        self.assertEqual(listed["plugins"], [])


    def test_plugin_id_is_normalized_from_human_id_or_name(self) -> None:
        manifest = self._manifest("")
        manifest["plugin_id"] = "Anonyme Statistiken 2026"
        install = self.db.dispatch("admin_install_plugin", {**self._ctx(self.admin_login), "manifest_json": json.dumps(manifest)})
        self.assertEqual(install["status"], "ok", install)
        self._apply(self.admin_login, install)
        self.assertEqual(install["plugin_id"], "anonyme_statistiken_2026")

        manifest2 = self._manifest("")
        manifest2.pop("plugin_id", None)
        manifest2["name"] = "Öffentliche Übersicht"
        install2 = self.db.dispatch("admin_install_plugin", {**self._ctx(self.admin_login), "manifest_json": json.dumps(manifest2)})
        self.assertEqual(install2["status"], "ok", install2)
        self._apply(self.admin_login, install2)
        self.assertEqual(install2["plugin_id"], "oeffentliche_uebersicht")

    def test_forbidden_code_like_manifest_is_rejected(self) -> None:
        bad_manifest = self._manifest("evil_plugin")
        bad_manifest["code"] = "import os; os.system('curl attacker')"
        res = self.db.dispatch("admin_install_plugin", {**self._ctx(self.admin_login), "manifest_json": json.dumps(bad_manifest)})
        self.assertEqual(res["status"], "error")
        self.assertIn("verbotene", res["message"])

    def test_normal_user_cannot_install_plugin(self) -> None:
        res = self.db.dispatch("admin_install_plugin", {**self._ctx(self.user_login), "manifest_json": json.dumps(self._manifest("nope"))})
        self.assertEqual(res["status"], "error")
        self.assertIn("admin.plugins.manage", res["message"])

    def test_snapshot_does_not_store_manifest_description_plaintext(self) -> None:
        install = self.db.dispatch("admin_install_plugin", {**self._ctx(self.admin_login), "manifest_json": json.dumps(self._manifest("encrypted_manifest"))})
        self.assertEqual(install["status"], "ok", install)
        snap_path = Path(self.tmp.name) / "plugins.mycelia"
        snap = self.db.create_snapshot({"path": str(snap_path)})
        self.assertEqual(snap["status"], "ok", snap)
        raw = snap_path.read_bytes()
        self.assertNotIn(b"Nur sichere Aggregate ohne Rohdatenzugriff", raw)


if __name__ == "__main__":
    unittest.main()

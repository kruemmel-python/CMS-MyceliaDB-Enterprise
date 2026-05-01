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


class EnterprisePluginsV1217Test(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["MYCELIA_SNAPSHOT_PATH"] = str(Path(self.tmp.name) / "autosave.mycelia")
        self.db = MyceliaPlatform()
        self.db.autosave_enabled = False
        self.db.core.database.clear()
        self.admin = self.db.register_user({"username": "admin", "password": "secret", "profile": {"role": "admin"}})
        self.alice = self.db.register_user({"username": "alice", "password": "secret", "profile": {"role": "user"}})
        self.bob = self.db.register_user({"username": "bob", "password": "secret", "profile": {"role": "user"}})
        self.alice_login = self.db.login_attractor({"username": "alice", "password": "secret"})
        self.bob_login = self.db.login_attractor({"username": "bob", "password": "secret"})

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def ctx(self, login: dict) -> dict:
        return {
            "engine_session_handle": login["engine_session"]["handle"],
            "engine_request_token": login["engine_session"]["request_token"],
        }

    def apply(self, login: dict, response: dict) -> dict:
        if isinstance(response.get("engine_session"), dict):
            login["engine_session"] = response["engine_session"]
        return response

    def enable_catalog_plugin(self, login: dict, plugin_id: str) -> None:
        import json
        catalog = self.db.dispatch("plugin_catalog", self.ctx(login))
        self.apply(login, catalog)
        manifest = next(p for p in catalog["enterprise_plugins"] if p["plugin_id"] == plugin_id)
        install = self.db.dispatch("admin_install_plugin", {**self.ctx(login), "manifest_json": json.dumps(manifest)})
        self.assertEqual(install["status"], "ok", install)
        self.apply(login, install)
        enable = self.db.dispatch("admin_set_plugin_state", {**self.ctx(login), "signature": install["signature"], "enabled": True})
        self.assertEqual(enable["status"], "ok", enable)
        self.apply(login, enable)


    def test_catalog_exposes_three_enterprise_plugins(self) -> None:
        catalog = self.db.dispatch("plugin_catalog", self.ctx(self.alice_login))
        self.assertEqual(catalog["status"], "ok", catalog)
        ids = {p["plugin_id"] for p in catalog["enterprise_plugins"]}
        self.assertTrue({"mycelia_digest", "privacy_guardian", "content_trust_lens"}.issubset(ids))
        capabilities = {c["key"] for c in catalog["capabilities"]}
        self.assertIn("digest.own.activity", capabilities)
        self.assertIn("privacy.own.inventory", capabilities)
        self.assertIn("trust.public.content", capabilities)

    def test_enterprise_dashboard_returns_safe_user_plugins(self) -> None:
        admin_login = self.db.login_attractor({"username": "admin", "password": "secret"})
        for plugin_id in ["mycelia_digest", "privacy_guardian", "content_trust_lens"]:
            self.enable_catalog_plugin(admin_login, plugin_id)
        created = self.db.dispatch("create_blog", {**self.ctx(self.alice_login), "title": "Alice Blog", "description": "Visible public blog"})
        self.assertEqual(created["status"], "ok", created)
        self.apply(self.alice_login, created)
        bob_comment = self.db.dispatch("create_comment", {**self.ctx(self.bob_login), "target_signature": created["signature"], "target_type": "blog", "body": "Hi Alice"})
        self.assertEqual(bob_comment["status"], "ok", bob_comment)
        self.apply(self.bob_login, bob_comment)
        bob_like = self.db.dispatch("react_content", {**self.ctx(self.bob_login), "target_signature": created["signature"], "target_type": "blog", "reaction": "like"})
        self.assertEqual(bob_like["status"], "ok", bob_like)
        self.apply(self.bob_login, bob_like)

        dashboard = self.db.dispatch("enterprise_plugin_dashboard", self.ctx(self.alice_login))
        self.assertEqual(dashboard["status"], "ok", dashboard)
        self.apply(self.alice_login, dashboard)
        plugins = dashboard["plugins"]
        self.assertEqual(plugins["mycelia_digest"]["summary"]["own_blogs"], 1)
        self.assertEqual(plugins["mycelia_digest"]["summary"]["comments_on_own_content"], 1)
        self.assertGreaterEqual(plugins["mycelia_digest"]["summary"]["reactions_on_own_content"], 1)
        self.assertEqual(plugins["privacy_guardian"]["inventory"]["blogs"], 1)
        self.assertIn("content_trust_lens", plugins)
        rendered = str(dashboard)
        self.assertNotIn("Hi Alice", rendered)
        self.assertEqual(dashboard["raw_records_returned"], 0)

    def test_enterprise_plugins_are_inert_until_installed_and_enabled(self) -> None:
        dashboard = self.db.dispatch("enterprise_plugin_dashboard", self.ctx(self.alice_login))
        self.assertEqual(dashboard["status"], "ok", dashboard)
        self.assertEqual(dashboard["plugins"], {})
        self.assertEqual(dashboard["activation_policy"], "installed_and_enabled_only")


    def test_enterprise_manifests_can_be_installed_and_run(self) -> None:
        admin_login = self.db.login_attractor({"username": "admin", "password": "secret"})
        catalog = self.db.dispatch("plugin_catalog", self.ctx(admin_login))
        self.apply(admin_login, catalog)
        manifest = next(p for p in catalog["enterprise_plugins"] if p["plugin_id"] == "mycelia_digest")
        import json
        install = self.db.dispatch("admin_install_plugin", {**self.ctx(admin_login), "manifest_json": json.dumps(manifest)})
        self.assertEqual(install["status"], "ok", install)
        self.apply(admin_login, install)
        enable = self.db.dispatch("admin_set_plugin_state", {**self.ctx(admin_login), "signature": install["signature"], "enabled": True})
        self.assertEqual(enable["status"], "ok", enable)
        self.apply(admin_login, enable)
        run = self.db.dispatch("run_plugin", {**self.ctx(admin_login), "signature": install["signature"]})
        self.assertEqual(run["status"], "ok", run)
        self.assertEqual(run["plugin"]["raw_records_returned"], 0)
        self.assertIn("digest.own.activity", str(run))

    def test_all_enterprise_plugin_template_capabilities_are_allowlisted(self) -> None:
        catalog = self.db.dispatch("plugin_catalog", self.ctx(self.alice_login))
        self.assertEqual(catalog["status"], "ok", catalog)
        allowed = {c["key"] for c in catalog["capabilities"]}
        unknown = {}
        for manifest in catalog["enterprise_plugins"]:
            missing = sorted(set(manifest.get("capabilities", [])) - allowed)
            if missing:
                unknown[manifest.get("plugin_id", "<unknown>")] = missing
        self.assertEqual(unknown, {})

    def test_fun_plugin_templates_can_be_installed_and_run(self) -> None:
        admin_login = self.db.login_attractor({"username": "admin", "password": "secret"})
        catalog = self.db.dispatch("plugin_catalog", self.ctx(admin_login))
        self.apply(admin_login, catalog)
        import json
        for plugin_id in ["mycelia_achievements", "mycelia_quests", "reaction_stickers", "blog_mood_themes"]:
            manifest = next(p for p in catalog["enterprise_plugins"] if p["plugin_id"] == plugin_id)
            install = self.db.dispatch("admin_install_plugin", {**self.ctx(admin_login), "manifest_json": json.dumps(manifest)})
            self.assertEqual(install["status"], "ok", install)
            self.apply(admin_login, install)
            enable = self.db.dispatch("admin_set_plugin_state", {**self.ctx(admin_login), "signature": install["signature"], "enabled": True})
            self.assertEqual(enable["status"], "ok", enable)
            self.apply(admin_login, enable)
            run = self.db.dispatch("run_plugin", {**self.ctx(admin_login), "signature": install["signature"]})
            self.assertEqual(run["status"], "ok", run)
            self.apply(admin_login, run)
            self.assertEqual(run["plugin"]["raw_records_returned"], 0)


if __name__ == "__main__":
    unittest.main()

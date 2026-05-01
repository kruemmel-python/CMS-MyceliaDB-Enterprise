import os
import sys
import unittest
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "html"
if str(HTML) not in sys.path:
    sys.path.insert(0, str(HTML))

from mycelia_platform import MyceliaPlatform


class FunPluginUiIntegrationV12120Test(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.platform = MyceliaPlatform()
        self.platform.core.database.clear()
        self.platform.snapshot_path = Path(self.tmp.name) / "fun_plugins.autosave.mycelia"
        self.platform.autosave_enabled = True

    def tearDown(self):
        self.tmp.cleanup()

    def enable_fun_plugin(self, plugin_id):
        catalog = self.platform.plugin_catalog({})
        manifest = next(p for p in catalog["enterprise_plugins"] if p["plugin_id"] == plugin_id)
        install = self.platform.admin_install_plugin({"actor_role": "admin", "manifest_json": json.dumps(manifest)})
        self.assertEqual(install["status"], "ok", install)
        enable = self.platform.admin_set_plugin_state({"actor_role": "admin", "signature": install["signature"], "enabled": True})
        self.assertEqual(enable["status"], "ok", enable)
        return install["signature"]


    def test_blog_mood_theme_is_stored_and_returned(self):
        self.enable_fun_plugin("blog_mood_themes")
        user = self.platform.register_user({
            "username": "theme_user",
            "password": "pw",
            "profile": {"role": "user"},
        })
        sig = user["signature"]
        blog = self.platform.create_blog({
            "actor_signature": sig,
            "actor_username": "theme_user",
            "actor_role": "user",
            "owner_signature": sig,
            "owner_username": "theme_user",
            "title": "Sci-Fi Blog",
            "description": "Theme test",
            "blog_theme": "scifi",
        })
        self.assertEqual(blog["status"], "ok")
        got = self.platform.get_blog({"signature": blog["signature"]})
        self.assertEqual(got["status"], "ok")
        self.assertEqual(got["blog"]["blog_theme"], "scifi")
        self.assertEqual(got["blog"]["blog_theme_descriptor"]["label"], "Sci-Fi")

    def test_reaction_stickers_work_on_public_content(self):
        self.enable_fun_plugin("reaction_stickers")
        user = self.platform.register_user({
            "username": "reaction_user",
            "password": "pw",
            "profile": {"role": "user"},
        })
        sig = user["signature"]
        thread = self.platform.create_forum_thread({
            "author_signature": sig,
            "author_username": "reaction_user",
            "actor_role": "user",
            "title": "Sticker Thread",
            "body": "Body",
        })
        self.assertEqual(thread["status"], "ok")
        result = self.platform.react_content({
            "author_signature": sig,
            "author_username": "reaction_user",
            "target_signature": thread["signature"],
            "target_type": "forum_thread",
            "reaction": "fire",
        })
        self.assertEqual(result["status"], "ok")
        got = self.platform.get_forum_thread({"signature": thread["signature"]})
        self.assertEqual(got["thread"]["reaction_breakdown"].get("fire"), 1)

    def test_fun_plugins_are_inert_until_installed_and_enabled(self):
        user = self.platform.register_user({
            "username": "inactive_user",
            "password": "pw",
            "profile": {"role": "user"},
        })
        sig = user["signature"]
        dashboard = self.platform.fun_plugin_dashboard({"actor_signature": sig})
        self.assertEqual(dashboard["plugins"], {})
        self.assertEqual(dashboard["activation_policy"], "installed_and_enabled_only")

        thread = self.platform.create_forum_thread({
            "author_signature": sig,
            "author_username": "inactive_user",
            "actor_role": "user",
            "title": "No Sticker Thread",
            "body": "Body",
        })
        blocked_reaction = self.platform.react_content({
            "author_signature": sig,
            "author_username": "inactive_user",
            "target_signature": thread["signature"],
            "target_type": "forum_thread",
            "reaction": "fire",
        })
        self.assertEqual(blocked_reaction["status"], "error")
        self.assertTrue(blocked_reaction.get("plugin_required"))

        blocked_theme = self.platform.create_blog({
            "actor_signature": sig,
            "actor_username": "inactive_user",
            "actor_role": "user",
            "owner_signature": sig,
            "owner_username": "inactive_user",
            "title": "Blocked Theme",
            "description": "Theme should require plugin",
            "blog_theme": "scifi",
        })
        self.assertEqual(blocked_theme["status"], "error")
        self.assertTrue(blocked_theme.get("plugin_required"))



if __name__ == "__main__":
    unittest.main()

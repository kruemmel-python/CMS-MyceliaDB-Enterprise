import tempfile
import unittest
from pathlib import Path

import sys
ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "html"
if str(HTML) not in sys.path:
    sys.path.insert(0, str(HTML))

from mycelia_platform import MyceliaPlatform


class EnterpriseContentPersistenceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.platform = MyceliaPlatform()
        self.platform.core.database.clear()
        self.platform.snapshot_path = Path(self.tmp.name) / "enterprise.autosave.mycelia"
        self.platform.autosave_enabled = True

    def tearDown(self):
        self.tmp.cleanup()

    def _register(self, username: str):
        result = self.platform.register_user({
            "username": username,
            "password": "secret",
            "profile": {"email": f"{username}@example.test", "role": "user"},
        })
        self.assertEqual(result["status"], "ok")
        return result["signature"]

    def test_forum_blog_comments_reactions_survive_cold_restore(self):
        user_a = self._register("enterprise_alice")
        user_b = self._register("enterprise_bob")

        thread = self.platform.create_forum_thread({
            "author_signature": user_a,
            "author_username": "enterprise_alice",
            "title": "Mycelia Forum Thread",
            "body": "A forum body stored as encrypted content packet.",
        })
        self.assertEqual(thread["status"], "ok")

        comment = self.platform.create_comment({
            "author_signature": user_b,
            "author_username": "enterprise_bob",
            "target_signature": thread["signature"],
            "target_type": "forum_thread",
            "body": "A comment from Bob.",
        })
        self.assertEqual(comment["status"], "ok")

        reaction = self.platform.react_content({
            "actor_signature": user_b,
            "actor_username": "enterprise_bob",
            "target_signature": thread["signature"],
            "target_type": "forum_thread",
            "reaction": "like",
        })
        self.assertEqual(reaction["status"], "ok")
        self.assertEqual(reaction["likes"], 1)

        blog = self.platform.create_blog({
            "owner_signature": user_a,
            "owner_username": "enterprise_alice",
            "title": "Alice Mycelia Blog",
            "description": "A SQL-free blog.",
        })
        self.assertEqual(blog["status"], "ok")

        post = self.platform.create_blog_post({
            "author_signature": user_a,
            "author_username": "enterprise_alice",
            "blog_signature": blog["signature"],
            "title": "First Post",
            "body": "The first encrypted blog post.",
            "publish_status": "published",
        })
        self.assertEqual(post["status"], "ok")

        self.assertTrue(self.platform.snapshot_path.exists())
        raw = self.platform.snapshot_path.read_bytes()
        self.assertNotIn(b"A forum body", raw)
        self.assertNotIn(b"Alice Mycelia Blog", raw)

        restored = MyceliaPlatform()
        restored.core.database.clear()
        restored.snapshot_path = self.platform.snapshot_path
        restore_result = restored.restore_snapshot({"path": str(self.platform.snapshot_path)})
        self.assertEqual(restore_result["status"], "ok")

        restored_thread = restored.get_forum_thread({"signature": thread["signature"]})
        self.assertEqual(restored_thread["status"], "ok")
        self.assertEqual(restored_thread["thread"]["title"], "Mycelia Forum Thread")
        self.assertEqual(restored_thread["thread"]["likes"], 1)

        comments = restored.list_comments({"target_signature": thread["signature"]})
        self.assertEqual(comments["status"], "ok")
        self.assertEqual(len(comments["comments"]), 1)
        self.assertEqual(comments["comments"][0]["body"], "A comment from Bob.")

        comment_reaction = restored.react_content({
            "actor_signature": user_a,
            "actor_username": "enterprise_alice",
            "target_signature": comment["signature"],
            "target_type": "comment",
            "reaction": "dislike",
        })
        self.assertEqual(comment_reaction["status"], "ok")
        self.assertEqual(comment_reaction["dislikes"], 1)
        comments_after_reaction = restored.list_comments({"target_signature": thread["signature"]})
        self.assertEqual(comments_after_reaction["comments"][0]["dislikes"], 1)

        restored_blog = restored.get_blog({"signature": blog["signature"]})
        self.assertEqual(restored_blog["status"], "ok")
        self.assertEqual(restored_blog["blog"]["title"], "Alice Mycelia Blog")

        restored_post = restored.get_blog_post({"signature": post["signature"]})
        self.assertEqual(restored_post["status"], "ok")
        self.assertIn("encrypted blog post", restored_post["post"]["body"])


    def test_public_blog_accepts_comments_and_reactions_from_other_users(self):
        owner = self._register("blog_owner")
        reader = self._register("blog_reader")

        blog = self.platform.create_blog({
            "owner_signature": owner,
            "owner_username": "blog_owner",
            "title": "Public Blog",
            "description": "Visible to all users.",
        })
        self.assertEqual(blog["status"], "ok")

        comment = self.platform.create_comment({
            "author_signature": reader,
            "author_username": "blog_reader",
            "target_signature": blog["signature"],
            "target_type": "blog",
            "body": "A reader can comment on the public blog.",
        })
        self.assertEqual(comment["status"], "ok")

        reaction = self.platform.react_content({
            "actor_signature": reader,
            "actor_username": "blog_reader",
            "target_signature": blog["signature"],
            "target_type": "blog",
            "reaction": "like",
        })
        self.assertEqual(reaction["status"], "ok")
        self.assertEqual(reaction["likes"], 1)

        public_blog = self.platform.get_blog({"signature": blog["signature"]})
        self.assertEqual(public_blog["status"], "ok")
        self.assertEqual(public_blog["blog"]["comments"], 1)
        self.assertEqual(public_blog["blog"]["likes"], 1)

        listed = self.platform.list_blogs({})
        visible = [item for item in listed["blogs"] if item["signature"] == blog["signature"]]
        self.assertEqual(len(visible), 1)
        self.assertEqual(visible[0]["comments"], 1)
        self.assertEqual(visible[0]["likes"], 1)



    def test_session_bound_public_blogs_are_not_owner_filtered(self):
        owner_sig = self._register("public_blog_owner")
        reader_sig = self._register("public_blog_reader")

        blog = self.platform.create_blog({
            "owner_signature": owner_sig,
            "owner_username": "public_blog_owner",
            "title": "Visible Public Blog",
            "description": "Must be visible in public Blogs for other sessions.",
        })
        self.assertEqual(blog["status"], "ok")

        login = self.platform.login_attractor({"username": "public_blog_reader", "password": "secret"})
        self.assertEqual(login["status"], "ok")
        session = login["engine_session"]

        listed = self.platform.dispatch("list_blogs", {
            "engine_session_handle": session["handle"],
            "engine_request_token": session["request_token"],
        })
        self.assertEqual(listed["status"], "ok")
        self.assertTrue(any(item["signature"] == blog["signature"] for item in listed["blogs"]))

        own_only = self.platform.list_blogs({"owner_signature": reader_sig})
        self.assertFalse(any(item["signature"] == blog["signature"] for item in own_only["blogs"]))

    def test_authorization_blocks_foreign_delete_but_allows_admin(self):
        owner = self._register("enterprise_owner")
        intruder = self._register("enterprise_intruder")
        thread = self.platform.create_forum_thread({
            "author_signature": owner,
            "author_username": "enterprise_owner",
            "title": "Protected",
            "body": "Only owner or admin can delete.",
        })
        denied = self.platform.delete_forum_thread({
            "signature": thread["signature"],
            "actor_signature": intruder,
            "actor_role": "user",
        })
        self.assertEqual(denied["status"], "error")

        allowed = self.platform.delete_forum_thread({
            "signature": thread["signature"],
            "actor_signature": intruder,
            "actor_role": "admin",
        })
        self.assertEqual(allowed["status"], "ok")


if __name__ == "__main__":
    unittest.main()

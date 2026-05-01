from __future__ import annotations

import base64
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "html"
if str(HTML) not in sys.path:
    sys.path.insert(0, str(HTML))

os.environ["MYCELIA_AUTOSAVE"] = "0"
os.environ["MYCELIA_AUTORESTORE"] = "0"

from mycelia_platform import MyceliaPlatform, MEDIA_TABLE  # noqa: E402


class MediaAttractorSystemTest(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MyceliaPlatform()
        self.db.autosave_enabled = False
        self.db.core.database.clear()
        self.actor = {
            "actor_role": "admin",
            "actor_signature": "actor-media-admin",
            "author_signature": "actor-media-admin",
            "author_username": "media_admin",
            "actor_permissions": ["media.upload", "media.moderate", "forum.create", "blog.create", "blog.post.create"],
        }

    def test_forum_thread_can_store_and_render_image_attractor(self) -> None:
        # 1x1 transparent PNG
        png = base64.b64encode(base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
        )).decode("ascii")
        result = self.db.create_forum_thread({
            **self.actor,
            "title": "Thread mit Bild",
            "body": "Media body",
            "media_file_b64": png,
            "media_file_name": "pixel.png",
            "media_mime": "image/png",
            "media_title": "Pixel",
        })
        self.assertEqual(result["status"], "ok", result)
        self.assertEqual(len(result["media_signatures"]), 1)
        thread = self.db.get_forum_thread({"signature": result["signature"]})
        self.assertEqual(thread["status"], "ok", thread)
        self.assertEqual(len(thread["thread"]["media"]), 1)
        self.assertTrue(thread["thread"]["media"][0]["data_uri"].startswith("data:image/png;base64,"))

    def test_embed_descriptor_is_allowlisted_and_moderatable(self) -> None:
        thread = self.db.create_forum_thread({**self.actor, "title": "Embed", "body": "Body"})
        self.assertEqual(thread["status"], "ok")
        upload = self.db.upload_media({
            **self.actor,
            "target_signature": thread["signature"],
            "target_type": "forum_thread",
            "embed_url": "https://youtu.be/dQw4w9WgXcQ",
            "media_title": "Safe YouTube",
        })
        self.assertEqual(upload["status"], "ok", upload)
        media = self.db.list_media_for_content({"target_signature": thread["signature"]})
        self.assertEqual(media["count"], 1)
        self.assertEqual(media["media"][0]["embed"]["provider"], "youtube")
        mod = self.db.moderate_media({**self.actor, "signature": upload["media_signatures"][0], "action": "quarantine"})
        self.assertEqual(mod["status"], "ok", mod)
        media_after = self.db.list_media_for_content({"target_signature": thread["signature"]})
        self.assertEqual(media_after["count"], 0)
        records = self.db.core.query_sql_like(table=MEDIA_TABLE, filters={}, limit=None)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["data"]["moderation_status"], "quarantined")



    def test_lists_include_media_preview_for_forum_and_blog(self) -> None:
        png = base64.b64encode(base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
        )).decode("ascii")
        thread = self.db.create_forum_thread({
            **self.actor,
            "title": "Forum Preview",
            "body": "Body",
            "media_file_b64": png,
            "media_file_name": "pixel.png",
            "media_mime": "image/png",
        })
        self.assertEqual(thread["status"], "ok", thread)
        threads = self.db.list_forum_threads({"limit": 10})["threads"]
        preview_thread = next(t for t in threads if t["signature"] == thread["signature"])
        self.assertEqual(preview_thread["media_count"], 1)
        self.assertTrue(preview_thread["media_preview"][0]["data_uri"].startswith("data:image/png;base64,"))

        blog = self.db.create_blog({**self.actor, "title": "Media Blog", "description": "Preview"})
        self.assertEqual(blog["status"], "ok", blog)
        post = self.db.create_blog_post({
            **self.actor,
            "blog_signature": blog["signature"],
            "title": "Blog Preview",
            "body": "Body",
            "media_file_b64": png,
            "media_file_name": "pixel.png",
            "media_mime": "image/png",
        })
        self.assertEqual(post["status"], "ok", post)
        posts = self.db.list_blog_posts({"blog_signature": blog["signature"]})["posts"]
        preview_post = next(p for p in posts if p["signature"] == post["signature"])
        self.assertEqual(preview_post["media_count"], 1)
        self.assertTrue(preview_post["media_preview"][0]["data_uri"].startswith("data:image/png;base64,"))

    def test_update_blog_post_accepts_post_signature_and_attaches_media(self) -> None:
        png = base64.b64encode(base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
        )).decode("ascii")
        blog = self.db.create_blog({**self.actor, "title": "Update Media Blog", "description": "Preview"})
        post = self.db.create_blog_post({
            **self.actor,
            "blog_signature": blog["signature"],
            "title": "Before",
            "body": "Before",
        })
        self.assertEqual(post["status"], "ok", post)
        updated = self.db.update_blog_post({
            **self.actor,
            "post_signature": post["signature"],
            "title": "After",
            "body": "After",
            "publish_status": "published",
            "media_file_b64": png,
            "media_file_name": "pixel.png",
            "media_mime": "image/png",
        })
        self.assertEqual(updated["status"], "ok", updated)
        self.assertEqual(len(updated["media_signatures"]), 1)
        rendered = self.db.get_blog_post({"signature": post["signature"]})
        self.assertEqual(len(rendered["post"]["media"]), 1)


    def test_direct_update_forum_thread_normalizer_preserves_media_fields(self) -> None:
        png = base64.b64encode(base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
        )).decode("ascii")
        thread = self.db.create_forum_thread({**self.actor, "title": "Before", "body": "Before"})
        self.assertEqual(thread["status"], "ok", thread)

        normalized = self.db._normalize_direct_payload("update_forum_thread", {
            "signature": thread["signature"],
            "title": "After",
            "body": "After",
            "media_file_b64": png,
            "media_file_name": "pixel.png",
            "media_mime": "image/png",
            "media_size_bytes": "68",
            "media_title": "Pixel",
        })
        updated = self.db.update_forum_thread({**self.actor, **normalized})
        self.assertEqual(updated["status"], "ok", updated)
        self.assertEqual(len(updated["media_signatures"]), 1)
        rendered = self.db.get_forum_thread({"signature": thread["signature"]})
        self.assertEqual(len(rendered["thread"]["media"]), 1)

    def test_direct_blog_post_normalizers_preserve_media_fields(self) -> None:
        png = base64.b64encode(base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
        )).decode("ascii")
        blog = self.db.create_blog({**self.actor, "title": "Direct Blog", "description": "Media"})
        self.assertEqual(blog["status"], "ok", blog)

        create_payload = self.db._normalize_direct_payload("create_blog_post", {
            "blog_signature": blog["signature"],
            "title": "Created",
            "body": "Body",
            "publish_status": "published",
            "media_file_b64": png,
            "media_file_name": "pixel.png",
            "media_mime": "image/png",
        })
        created = self.db.create_blog_post({**self.actor, **create_payload})
        self.assertEqual(created["status"], "ok", created)
        self.assertEqual(len(created["media_signatures"]), 1)

        update_payload = self.db._normalize_direct_payload("update_blog_post", {
            "post_signature": created["signature"],
            "title": "Updated",
            "body": "Updated",
            "publish_status": "published",
            "embed_url": "https://youtu.be/dQw4w9WgXcQ",
            "media_title": "Video",
        })
        updated = self.db.update_blog_post({**self.actor, **update_payload})
        self.assertEqual(updated["status"], "ok", updated)
        self.assertEqual(len(updated["media_signatures"]), 1)
        rendered = self.db.get_blog_post({"signature": created["signature"]})
        self.assertEqual(len(rendered["post"]["media"]), 2)


    def test_blog_creation_and_update_accept_media_attractors(self) -> None:
        png = base64.b64encode(base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
        )).decode("ascii")

        create_payload = self.db._normalize_direct_payload("create_blog", {
            "title": "Blog mit Cover",
            "description": "Cover beim Erstellen",
            "media_file_b64": png,
            "media_file_name": "cover.png",
            "media_mime": "image/png",
            "media_title": "Cover",
        })
        blog = self.db.create_blog({**self.actor, **create_payload})
        self.assertEqual(blog["status"], "ok", blog)
        self.assertEqual(len(blog["media_signatures"]), 1)

        rendered = self.db.get_blog({"signature": blog["signature"]})
        self.assertEqual(rendered["status"], "ok", rendered)
        self.assertEqual(rendered["blog"]["media_count"], 1)
        self.assertTrue(rendered["blog"]["media"][0]["data_uri"].startswith("data:image/png;base64,"))

        update_payload = self.db._normalize_direct_payload("update_blog", {
            "blog_signature": blog["signature"],
            "title": "Blog mit Cover Update",
            "description": "Video-Link beim Bearbeiten",
            "embed_url": "https://youtu.be/dQw4w9WgXcQ",
            "media_title": "Intro",
        })
        updated = self.db.update_blog({**self.actor, **update_payload})
        self.assertEqual(updated["status"], "ok", updated)
        self.assertEqual(len(updated["media_signatures"]), 1)

        listed = self.db.list_blogs({"owner_signature": self.actor["actor_signature"]})["blogs"]
        preview = next(b for b in listed if b["signature"] == blog["signature"])
        self.assertEqual(preview["media_count"], 2)
        embed_items = [m for m in preview["media_preview"] if m.get("embed")]
        self.assertTrue(embed_items)
        self.assertEqual(embed_items[0]["embed"]["provider"], "youtube")

    def test_plugin_catalog_exposes_media_capabilities(self) -> None:
        caps = {c["key"] for c in self.db.plugin_catalog({})["capabilities"]}
        self.assertIn("media.image.upload", caps)
        self.assertIn("media.embed.link.create", caps)
        self.assertIn("media.moderate.hide", caps)


if __name__ == "__main__":
    unittest.main()

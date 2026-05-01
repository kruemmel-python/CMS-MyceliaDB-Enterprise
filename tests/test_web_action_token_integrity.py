from __future__ import annotations

import base64
import json
import os
import sys
import time
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "html"
if str(HTML) not in sys.path:
    sys.path.insert(0, str(HTML))

from mycelia_platform import MyceliaPlatform  # noqa: E402


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


class WebActionTokenIntegrityTest(unittest.TestCase):
    """Regression coverage for every mutating website action.

    This simulates the PHP Zero-Logic Gateway:
    - every page read forwards the current opaque engine session token,
    - ingest_manifest.php fetches a fresh one-time form token,
    - the browser seals that token inside the Direct-Ingest envelope,
    - the Engine consumes the sealed token and returns the next token.

    The important invariant: normal navigation and all website actions must not
    produce "Request-Token passt nicht..." while old tokens remain one-time.
    """

    def setUp(self) -> None:
        self._old_env = {
            "MYCELIA_AUTOSAVE": os.environ.get("MYCELIA_AUTOSAVE"),
            "MYCELIA_AUTORESTORE": os.environ.get("MYCELIA_AUTORESTORE"),
        }
        os.environ["MYCELIA_AUTOSAVE"] = "0"
        os.environ["MYCELIA_AUTORESTORE"] = "0"
        self.platform = MyceliaPlatform()
        self.platform.core.database.clear()
        self.session: dict[str, str] | None = None
        self.signature = ""

    def tearDown(self) -> None:
        for name, value in self._old_env.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def _seal(self, op: str, payload: dict[str, str]) -> dict[str, str | int]:
        manifest = self.platform.direct_ingest_manifest({})
        public_key = serialization.load_der_public_key(base64.b64decode(manifest["public_key_spki_b64"]))
        aes_key = AESGCM.generate_key(bit_length=256)
        iv = os.urandom(12)
        aad = b"myceliadb-direct-ingest-v1"
        body = {
            "op": op,
            "issued_at_ms": int(time.time() * 1000),
            "nonce": _b64(os.urandom(18)),
            "payload": payload,
        }
        ciphertext = AESGCM(aes_key).encrypt(iv, json.dumps(body).encode("utf-8"), aad)
        encrypted_key = public_key.encrypt(
            aes_key,
            padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=aad),
        )
        return {
            "v": 1,
            "alg": "RSA-OAEP-3072-SHA256/AES-256-GCM",
            "aad": aad.decode("ascii"),
            "key_b64": _b64(encrypted_key),
            "iv_b64": _b64(iv),
            "ciphertext_b64": _b64(ciphertext),
        }

    def _apply_session(self, response: dict) -> None:
        if isinstance(response.get("engine_session"), dict):
            self.session = response["engine_session"]

    def _login(self) -> None:
        reg = self.platform.direct_ingest({
            "op": "register_user",
            "sealed": self._seal("register_user", {
                "username": "web_token_user",
                "password": "secret",
                "email": "web-token@example.test",
            }),
        })
        self.assertEqual(reg["status"], "ok", reg)
        login = self.platform.direct_ingest({
            "op": "login_attractor",
            "sealed": self._seal("login_attractor", {
                "username": "web_token_user",
                "password": "secret",
            }),
        })
        self.assertEqual(login["status"], "ok", login)
        self.signature = str(login["signature"])
        self._apply_session(login)
        self.assertIsNotNone(self.session)

    def _page_call(self, command: str, payload: dict | None = None) -> dict:
        assert self.session is not None
        data = dict(payload or {})
        data["engine_session_handle"] = self.session["handle"]
        data["engine_request_token"] = self.session["request_token"]
        response = self.platform.dispatch(command, data)
        self.assertEqual(response["status"], "ok", response)
        self._apply_session(response)
        return response

    def _manifest_form_token(self) -> str:
        assert self.session is not None
        manifest = self.platform.dispatch("direct_ingest_manifest", {
            "engine_session_handle": self.session["handle"],
            "engine_request_token": self.session["request_token"],
        })
        self.assertEqual(manifest["status"], "ok", manifest)
        self._apply_session(manifest)
        return str(manifest["engine_request_token"])

    def _mutate(self, op: str, payload: dict[str, str]) -> dict:
        assert self.session is not None
        form_token = self._manifest_form_token()
        sealed_payload = {"__mycelia_request_token": form_token, **payload}
        result = self.platform.direct_ingest({
            "op": op,
            "actor_context": {"engine_session_handle": self.session["handle"]},
            "sealed": self._seal(op, sealed_payload),
        })
        self.assertEqual(result["status"], "ok", result)
        self._apply_session(result)
        return result

    def test_every_website_action_survives_navigation_token_rotation(self) -> None:
        self._login()

        # Profile page: require_login + get_profile + update_profile.
        self._page_call("validate_session")
        self._page_call("get_profile", {"signature": self.signature})
        self._mutate("update_profile", {"vorname": "Ralf", "ort": "Leipzig", "email": "safe@example.test"})

        # Forum list page: require_login + list + create thread.
        self._page_call("validate_session")
        self._page_call("list_forum_threads", {"limit": 200})
        thread = self._mutate("create_forum_thread", {"title": "Enterprise Thread", "body": "Forum payload"})

        # Thread page: read thread/comments, comment, react, update, delete comment.
        self._page_call("validate_session")
        self._page_call("get_forum_thread", {"signature": thread["signature"]})
        self._page_call("list_comments", {"target_signature": thread["signature"]})
        comment = self._mutate("create_comment", {
            "target_signature": thread["signature"],
            "target_type": "forum_thread",
            "body": "Thread comment",
        })
        self._mutate("react_content", {
            "target_signature": thread["signature"],
            "target_type": "forum_thread",
            "reaction": "like",
        })
        self._mutate("react_content", {
            "target_signature": comment["signature"],
            "target_type": "comment",
            "reaction": "dislike",
        })
        self._mutate("delete_comment", {"signature": comment["signature"]})
        self._mutate("update_forum_thread", {"signature": thread["signature"], "title": "Updated Thread", "body": "Updated body"})

        # Blog overview/my blog: create blog, update it, create/update/react/delete post.
        self._page_call("validate_session")
        self._page_call("list_blogs", {})
        blog = self._mutate("create_blog", {"title": "Enterprise Blog", "description": "Blog description"})
        self._mutate("update_blog", {"blog_signature": blog["signature"], "title": "Enterprise Blog 2", "description": "Changed"})

        self._page_call("get_blog", {"signature": blog["signature"]})
        self._page_call("list_blog_posts", {"blog_signature": blog["signature"]})
        post = self._mutate("create_blog_post", {
            "blog_signature": blog["signature"],
            "title": "Post 1",
            "body": "Post body",
            "publish_status": "published",
        })
        self._page_call("get_blog_post", {"signature": post["signature"]})
        self._page_call("list_comments", {"target_signature": post["signature"]})
        post_comment = self._mutate("create_comment", {
            "post_signature": post["signature"],
            "target_type": "blog_post",
            "body": "Post comment",
        })
        self._mutate("react_content", {
            "post_signature": post["signature"],
            "target_type": "blog_post",
            "reaction": "like",
        })
        self._mutate("delete_comment", {"signature": post_comment["signature"]})
        self._mutate("update_blog_post", {
            "post_signature": post["signature"],
            "title": "Post 1 updated",
            "body": "Post body updated",
            "publish_status": "draft",
        })
        self._mutate("delete_blog_post", {"post_signature": post["signature"]})
        self._mutate("delete_blog", {"blog_signature": blog["signature"]})

        # Finally delete the forum thread.
        self._mutate("delete_forum_thread", {"signature": thread["signature"]})

    def test_manifest_token_is_one_time_but_does_not_break_following_forms(self) -> None:
        self._login()
        first_form_token = self._manifest_form_token()
        blog = self.platform.direct_ingest({
            "op": "create_blog",
            "actor_context": {"engine_session_handle": self.session["handle"]},
            "sealed": self._seal("create_blog", {
                "__mycelia_request_token": first_form_token,
                "title": "One Time",
                "description": "first",
            }),
        })
        self.assertEqual(blog["status"], "ok", blog)
        self._apply_session(blog)

        replay = self.platform.direct_ingest({
            "op": "create_blog",
            "actor_context": {"engine_session_handle": self.session["handle"]},
            "sealed": self._seal("create_blog", {
                "__mycelia_request_token": first_form_token,
                "title": "Replay",
                "description": "must fail",
            }),
        })
        self.assertEqual(replay["status"], "error")
        self.assertIn("Token", replay["message"])

        # A fresh manifest immediately yields a valid form token again.
        second = self._mutate("create_blog", {"title": "Fresh", "description": "works"})
        self.assertEqual(second["status"], "ok")


if __name__ == "__main__":
    unittest.main()


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

os.environ["MYCELIA_AUTOSAVE"] = "0"
os.environ["MYCELIA_AUTORESTORE"] = "0"

from mycelia_platform import MyceliaPlatform  # noqa: E402


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


class PrivacyRightsExportErasureTest(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MyceliaPlatform()
        self.db.autosave_enabled = False
        self.db.core.database.clear()
        self.session: dict[str, str] | None = None

    def _seal(self, op: str, payload: dict[str, str]) -> dict[str, str | int]:
        manifest = self.db.direct_ingest_manifest({})
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

    def _login(self) -> str:
        reg = self.db.direct_ingest({
            "op": "register_user",
            "sealed": self._seal("register_user", {
                "username": "privacy_user",
                "password": "secret",
                "vorname": "Ralf",
                "ort": "Leipzig",
                "email": "privacy@example.test",
            }),
        })
        self.assertEqual(reg["status"], "ok", reg)
        login = self.db.direct_ingest({
            "op": "login_attractor",
            "sealed": self._seal("login_attractor", {"username": "privacy_user", "password": "secret"}),
        })
        self.assertEqual(login["status"], "ok", login)
        self._apply_session(login)
        return str(login["signature"])

    def _page_call(self, command: str, payload: dict | None = None) -> dict:
        assert self.session is not None
        request = dict(payload or {})
        request["engine_session_handle"] = self.session["handle"]
        request["engine_request_token"] = self.session["request_token"]
        response = self.db.dispatch(command, request)
        self.assertEqual(response["status"], "ok", response)
        self._apply_session(response)
        return response

    def _manifest_form_token(self) -> str:
        assert self.session is not None
        manifest = self.db.dispatch("direct_ingest_manifest", {
            "engine_session_handle": self.session["handle"],
            "engine_request_token": self.session["request_token"],
        })
        self.assertEqual(manifest["status"], "ok", manifest)
        self._apply_session(manifest)
        return str(manifest["engine_request_token"])

    def _mutate(self, op: str, payload: dict[str, str]) -> dict:
        assert self.session is not None
        form_token = self._manifest_form_token()
        result = self.db.direct_ingest({
            "op": op,
            "actor_context": {"engine_session_handle": self.session["handle"]},
            "sealed": self._seal(op, {"__mycelia_request_token": form_token, **payload}),
        })
        self.assertEqual(result["status"], "ok", result)
        self._apply_session(result)
        return result

    def test_user_can_export_and_delete_all_owned_data(self) -> None:
        signature = self._login()
        thread = self._mutate("create_forum_thread", {"title": "Privacy Thread", "body": "Leipzig content"})
        comment = self._mutate("create_comment", {
            "target_signature": thread["signature"],
            "target_type": "forum_thread",
            "body": "My comment",
        })
        self._mutate("react_content", {
            "target_signature": thread["signature"],
            "target_type": "forum_thread",
            "reaction": "like",
        })
        blog = self._mutate("create_blog", {"title": "Privacy Blog", "description": "Portable"})
        post = self._mutate("create_blog_post", {
            "blog_signature": blog["signature"],
            "title": "Privacy Post",
            "body": "Portable body",
            "publish_status": "published",
        })

        exported = self._page_call("export_my_data")
        package = exported["export"]
        self.assertEqual(package["subject"]["username"], "privacy_user")
        self.assertEqual(package["profile"]["ort"], "Leipzig")
        self.assertFalse(package["security_exclusions"]["auth_pattern_exported"])
        self.assertEqual(package["content"]["forum_threads"][0]["body"], "Leipzig content")
        self.assertEqual(package["content"]["comments"][0]["body"], "My comment")
        self.assertEqual(package["content"]["blogs"][0]["title"], "Privacy Blog")
        self.assertEqual(package["content"]["blog_posts"][0]["body"], "Portable body")

        deleted = self._mutate("delete_my_account", {"confirm_delete": "DELETE", "password": "secret"})
        self.assertEqual(deleted["status"], "ok", deleted)
        self.assertTrue(deleted["logout"])
        self.assertGreaterEqual(deleted["deleted_nodes"], 5)

        self.assertIsNone(self.db.core.get_sql_record(signature))
        self.assertEqual(self.db.core.query_sql_like(table="mycelia_users", filters={"username": "privacy_user"}, limit=None), [])
        self.assertEqual(self.db.list_forum_threads({})["threads"], [])
        self.assertEqual(self.db.list_blogs({})["blogs"], [])
        self.assertEqual(self.db.list_blog_posts({})["posts"], [])
        self.assertEqual(self.db.list_comments({})["comments"], [])

        relogin = self.db.login_attractor({"username": "privacy_user", "password": "secret"})
        self.assertEqual(relogin["status"], "error")

    def test_delete_requires_password_and_delete_confirmation(self) -> None:
        self._login()
        missing_confirm = self._mutate_expect_error("delete_my_account", {"confirm_delete": "NO", "password": "secret"})
        self.assertIn("DELETE", missing_confirm["message"])
        wrong_password = self._mutate_expect_error("delete_my_account", {"confirm_delete": "DELETE", "password": "wrong"})
        self.assertIn("Passwort", wrong_password["message"])

    def _mutate_expect_error(self, op: str, payload: dict[str, str]) -> dict:
        assert self.session is not None
        form_token = self._manifest_form_token()
        result = self.db.direct_ingest({
            "op": op,
            "actor_context": {"engine_session_handle": self.session["handle"]},
            "sealed": self._seal(op, {"__mycelia_request_token": form_token, **payload}),
        })
        self.assertEqual(result["status"], "error", result)
        self._apply_session(result)
        # Error responses still return the rotated Engine session, preventing
        # token drift after a valid but semantically rejected Direct-Ingest.
        self._page_call("validate_session")
        return result


if __name__ == "__main__":
    unittest.main()

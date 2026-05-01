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


class SessionTokenDriftRegressionTest(unittest.TestCase):
    def setUp(self) -> None:
        self._old_env = {
            "MYCELIA_AUTOSAVE": os.environ.get("MYCELIA_AUTOSAVE"),
            "MYCELIA_AUTORESTORE": os.environ.get("MYCELIA_AUTORESTORE"),
        }
        os.environ["MYCELIA_AUTOSAVE"] = "0"
        os.environ["MYCELIA_AUTORESTORE"] = "0"
        self.platform = MyceliaPlatform()
        self.platform.core.database.clear()

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

    def _login(self) -> tuple[str, dict[str, str]]:
        reg = self.platform.direct_ingest({
            "op": "register_user",
            "sealed": self._seal("register_user", {
                "username": "drift_user",
                "password": "secret",
                "email": "drift@example.test",
            }),
        })
        self.assertEqual(reg["status"], "ok", reg)
        login = self.platform.direct_ingest({
            "op": "login_attractor",
            "sealed": self._seal("login_attractor", {
                "username": "drift_user",
                "password": "secret",
            }),
        })
        self.assertEqual(login["status"], "ok", login)
        return str(login["signature"]), login["engine_session"]

    def test_session_bound_read_returns_rotated_token_for_next_page_form(self) -> None:
        signature, session = self._login()

        validation = self.platform.dispatch("validate_session", {
            "engine_session_handle": session["handle"],
            "engine_request_token": session["request_token"],
        })
        self.assertEqual(validation["status"], "ok", validation)
        page_token = validation["engine_session"]["request_token"]

        profile = self.platform.dispatch("get_profile", {
            "signature": signature,
            "engine_session_handle": session["handle"],
            "engine_request_token": page_token,
        })
        self.assertEqual(profile["status"], "ok", profile)
        self.assertIn("engine_session", profile, profile)
        form_token = profile["engine_session"]["request_token"]
        self.assertNotEqual(form_token, page_token)

        stale = self.platform.direct_ingest({
            "op": "create_forum_thread",
            "actor_context": {"engine_session_handle": session["handle"]},
            "sealed": self._seal("create_forum_thread", {
                "__mycelia_request_token": page_token,
                "title": "stale",
                "body": "this must not be accepted",
            }),
        })
        self.assertEqual(stale["status"], "error")
        self.assertIn("Token", stale["message"])

        ok = self.platform.direct_ingest({
            "op": "create_forum_thread",
            "actor_context": {"engine_session_handle": session["handle"]},
            "sealed": self._seal("create_forum_thread", {
                "__mycelia_request_token": form_token,
                "title": "fresh",
                "body": "fresh token accepted after session-bound read",
            }),
        })
        self.assertEqual(ok["status"], "ok", ok)
        self.assertIn("engine_session", ok)


if __name__ == "__main__":
    unittest.main()

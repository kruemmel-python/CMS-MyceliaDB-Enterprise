from __future__ import annotations

import base64
import json
import sys
import time
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "html"
if str(HTML) not in sys.path:
    sys.path.insert(0, str(HTML))

from mycelia_platform import MyceliaPlatform  # noqa: E402


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


class DirectGpuIngestTest(unittest.TestCase):
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
        self.assertEqual(manifest["status"], "ok")
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
            padding.OAEP(
                mgf=padding.MGF1(hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=aad,
            ),
        )
        return {
            "v": 1,
            "alg": "RSA-OAEP-3072-SHA256/AES-256-GCM",
            "aad": aad.decode("ascii"),
            "key_b64": _b64(encrypted_key),
            "iv_b64": _b64(iv),
            "ciphertext_b64": _b64(ciphertext),
        }

    def test_direct_ingest_registers_and_logs_in_without_php_plaintext(self) -> None:
        sealed_register = self._seal(
            "register_user",
            {
                "username": "direct_alice",
                "password": "top secret passphrase",
                "vorname": "Alice",
                "nachname": "Cipher",
                "email": "alice@example.test",
            },
        )
        registered = self.platform.direct_ingest({"op": "register_user", "sealed": sealed_register})
        self.assertEqual(registered["status"], "ok", registered)
        self.assertEqual(registered["direct_ingest"]["mode"], "phase1_php_blind")
        self.assertFalse(registered["direct_ingest"]["php_cleartext_fields_seen"])
        self.assertFalse(registered["direct_ingest"]["strict_vram_residency_proven"])

        sealed_login = self._seal(
            "login_attractor",
            {"username": "direct_alice", "password": "top secret passphrase"},
        )
        login = self.platform.direct_ingest({"op": "login_attractor", "sealed": sealed_login})
        self.assertEqual(login["status"], "ok", login)
        self.assertEqual(login["username"], "direct_alice")

    def test_direct_ingest_replay_is_rejected(self) -> None:
        sealed = self._seal("login_attractor", {"username": "nobody", "password": "pw"})
        first = self.platform.direct_ingest({"op": "login_attractor", "sealed": sealed})
        self.assertEqual(first["status"], "error")  # no such user, but nonce is consumed after opening

        replay = self.platform.direct_ingest({"op": "login_attractor", "sealed": sealed})
        self.assertEqual(replay["status"], "error")
        self.assertIn("replay", replay["message"].lower())

    def test_residency_report_marks_phase1_not_strict_vram(self) -> None:
        report = self.platform.residency_report({})
        self.assertTrue(report["direct_gpu_ingest"])
        self.assertIn(report["direct_ingest_phase"], ("phase1_php_blind", "phase2_native_gpu_envelope"))
        self.assertTrue(report["php_blind_form_transport"])
        self.assertIn(report["python_cpu_decrypt_materialized"], (True, False))
        self.assertIn("strict_inflight_vram_claim", report)


if __name__ == "__main__":
    unittest.main()

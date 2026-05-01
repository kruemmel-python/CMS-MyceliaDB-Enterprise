import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "html"
if str(HTML) not in sys.path:
    sys.path.insert(0, str(HTML))

import mycelia_platform as mp


class EnterpriseEvolutionV1217Tests(unittest.TestCase):
    def test_direct_ingest_manifest_advertises_pfs(self):
        manifest = mp.PLATFORM.direct_ingest_manifest({"op": "login_attractor"})
        self.assertEqual(manifest["status"], "ok")
        self.assertEqual(manifest["version"], 2)
        self.assertIn("pfs", manifest)
        self.assertIn("X25519", manifest["pfs_alg"])

    def test_smql_vector_cue_projects_to_mood_vector(self):
        vec = mp.PLATFORM._cue_vector("VECTOR [0.2, 0.4, 0.6, 0.8]")
        self.assertEqual(len(vec), 3)
        self.assertTrue(all(0.0 <= v <= 1.0 for v in vec))
        parsed = mp.PLATFORM._parse_smql('FIND mycelia_media_nodes ASSOCIATED WITH VECTOR [0.2, 0.4, 0.6] LIMIT 3')
        self.assertEqual(parsed["table"], "mycelia_media_nodes")
        self.assertTrue(parsed["cue"].startswith("VECTOR"))

    def test_security_evolution_status_contains_all_eight_features(self):
        status = mp.PLATFORM.security_evolution_status({})
        self.assertEqual(status["status"], "ok")
        features = status["features"]
        expected = {
            "direct_ingest_pfs",
            "e2ee_blind_messages",
            "telemetry_dashboard",
            "ephemeral_pheromone_decay",
            "smql_multimodal_vectors",
            "webauthn_bridge",
            "classified_memory_probe_canaries",
            "vram_zeroing_contract_audit",
        }
        self.assertTrue(expected.issubset(features.keys()))

    def test_e2ee_directory_resolves_user_recipient_from_key_signature(self):
        db = mp.MyceliaPlatform()
        db.autosave_enabled = False
        db.core.database.clear()

        alice = db.register_user({"username": "e2ee_alice", "password": "pw", "profile": {"role": "user"}})
        bob = db.register_user({"username": "e2ee_bob", "password": "pw", "profile": {"role": "user"}})
        self.assertEqual(alice["status"], "ok")
        self.assertEqual(bob["status"], "ok")

        bob_key = db.e2ee_register_public_key({
            "actor_signature": bob["signature"],
            "actor_username": "e2ee_bob",
            "public_key_jwk": {"kty": "EC", "crv": "P-256", "x": "x", "y": "y"},
            "encrypted_private_key": "browser-local",
        })
        self.assertEqual(bob_key["status"], "ok", bob_key)

        directory = db.e2ee_recipient_directory({"actor_signature": alice["signature"]})
        self.assertEqual(directory["status"], "ok", directory)
        bob_entry = next(r for r in directory["recipients"] if r["user_signature"] == bob["signature"])
        self.assertTrue(bob_entry["messageable"])
        self.assertEqual(bob_entry["latest_key"]["signature"], bob_key["signature"])

        # Backward compatibility: even if a client submits the concrete key
        # signature as recipient_signature, the Engine resolves it to the
        # owning user signature so Bob's inbox receives the message.
        sent = db.e2ee_send_message({
            "actor_signature": alice["signature"],
            "actor_username": "e2ee_alice",
            "recipient_signature": bob_key["signature"],
            "ciphertext_b64": "Y" * 32,
            "nonce_b64": "N" * 12,
        })
        self.assertEqual(sent["status"], "ok", sent)
        self.assertEqual(sent["recipient_signature"], bob["signature"])
        self.assertEqual(sent["recipient_key_signature"], bob_key["signature"])

        inbox = db.e2ee_inbox({"actor_signature": bob["signature"]})
        self.assertEqual(inbox["status"], "ok", inbox)
        self.assertEqual(inbox["count"], 1)
        self.assertEqual(inbox["messages"][0]["recipient_key_signature"], bob_key["signature"])


if __name__ == "__main__":
    unittest.main()

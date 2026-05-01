from __future__ import annotations

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

from mycelia_platform import MyceliaPlatform  # noqa: E402


class EnterpriseV120ExtensionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MyceliaPlatform()
        self.db.autosave_enabled = False
        self.db.core.database.clear()

    def test_smql_combines_filter_and_semantic_rank(self) -> None:
        reg = self.db.register_user({
            "username": "admin_case",
            "password": "secret",
            "profile": {"role": "admin", "permissions": ["admin.system.manage"]},
        })
        self.assertEqual(reg["status"], "ok")
        result = self.db.smql_query({"query": 'FIND mycelia_users WHERE username="admin_case" ASSOCIATED WITH "High Security" LIMIT 5'})
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["count"], 1)
        self.assertIn("smql_score", result["results"][0])
        plan = self.db.smql_explain({"query": "FIND mycelia_users LIMIT 1"})
        self.assertEqual(plan["status"], "ok")

    def test_provenance_ledger_verifies_after_mutation(self) -> None:
        reg = self.db.register_user({"username": "prov_user", "password": "secret", "profile": {"role": "user"}})
        self.assertEqual(reg["status"], "ok")
        self.db._record_provenance_event("unit_test", reg["signature"], {"field": "value"}, actor_signature=reg["signature"])
        verified = self.db.provenance_verify({})
        self.assertEqual(verified["status"], "ok")
        self.assertTrue(verified["verified"])
        log = self.db.provenance_log({"signature": reg["signature"]})
        self.assertEqual(log["status"], "ok")
        self.assertGreaterEqual(log["count"], 1)

    def test_federation_influx_imports_stable_handles(self) -> None:
        admin = {"actor_role": "admin", "actor_signature": "admin-sig", "permissions": ["admin.system.manage"]}
        add = self.db.federation_peer_add({"peer_id": "node-b", "url": "https://node-b.local:9999", **admin})
        self.assertEqual(add["status"], "ok")
        imp = self.db.federation_import_influx({
            **admin,
            "attractors": [{
                "signature": "abc123",
                "table": "remote_table",
                "payload_hash": "00" * 32,
                "energy_hash": "11" * 32,
                "stability": 0.97,
                "mood_vector": [0.9, 0.2, 0.8],
            }],
        })
        self.assertEqual(imp["status"], "ok")
        self.assertEqual(imp["imported"], 1)
        status = self.db.federation_status({})
        self.assertEqual(status["peer_count"], 1)

    def test_security_status_endpoints_are_machine_readable(self) -> None:
        self.assertEqual(self.db.local_transport_security_status({})["status"], "ok")
        self.assertEqual(self.db.native_library_authenticity({})["version"], "MYCELIA_NATIVE_AUTHENTICITY_V1")
        self.assertEqual(self.db.quantum_guard_status({})["version"], "MYCELIA_QUANTUM_TENSION_GUARD_V1")


if __name__ == "__main__":
    unittest.main()

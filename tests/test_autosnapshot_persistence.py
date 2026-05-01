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

from mycelia_platform import MyceliaPlatform, SNAPSHOT_MAGIC  # noqa: E402


class AutoSnapshotPersistenceTest(unittest.TestCase):
    def test_registered_user_survives_engine_restart_via_default_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            snapshot = Path(tmp) / "autosave.mycelia"
            old_path = os.environ.get("MYCELIA_SNAPSHOT_PATH")
            old_autosave = os.environ.get("MYCELIA_AUTOSAVE")
            old_autorestore = os.environ.get("MYCELIA_AUTORESTORE")
            try:
                os.environ["MYCELIA_SNAPSHOT_PATH"] = str(snapshot)
                os.environ["MYCELIA_AUTOSAVE"] = "1"
                os.environ["MYCELIA_AUTORESTORE"] = "1"

                first = MyceliaPlatform()
                registered = first.register_user(
                    {
                        "username": "Ralf",
                        "password": "persist-pass",
                        "profile": {"vorname": "Ralf", "nachname": "Krümmel"},
                    }
                )
                self.assertEqual(registered["status"], "ok", registered)
                self.assertEqual(registered["autosave"], "ok", registered)
                self.assertTrue(snapshot.exists())
                self.assertTrue(snapshot.read_bytes().startswith(SNAPSHOT_MAGIC))

                # Simulates a cold engine restart: a fresh Platform instance has
                # an empty DAD first, then autorestore reconstructs it from the
                # encrypted binary snapshot without touching SQL.
                second = MyceliaPlatform()
                login = second.login_attractor({"username": "Ralf", "password": "persist-pass"})
                self.assertEqual(login["status"], "ok", login)

                profile = second.get_profile({"signature": login["signature"]})
                self.assertEqual(profile["status"], "ok", profile)
                self.assertEqual(profile["profile"]["nachname"], "Krümmel")
            finally:
                def restore_env(name: str, value: str | None) -> None:
                    if value is None:
                        os.environ.pop(name, None)
                    else:
                        os.environ[name] = value

                restore_env("MYCELIA_SNAPSHOT_PATH", old_path)
                restore_env("MYCELIA_AUTOSAVE", old_autosave)
                restore_env("MYCELIA_AUTORESTORE", old_autorestore)


if __name__ == "__main__":
    unittest.main()

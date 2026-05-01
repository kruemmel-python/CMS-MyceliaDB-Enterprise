
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "html"
if str(HTML) not in sys.path:
    sys.path.insert(0, str(HTML))


class SnapshotPathFallbackTest(unittest.TestCase):
    def setUp(self) -> None:
        self._old_env = dict(os.environ)
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["MYCELIA_AUTORESTORE"] = "0"
        os.environ["MYCELIA_AUTOSAVE"] = "0"
        os.environ["MYCELIA_SNAPSHOT_PATH"] = str(Path(self.tmp.name) / "snapshots" / "autosave.mycelia")

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._old_env)
        self.tmp.cleanup()

    def test_restore_snapshot_missing_file_returns_error_not_500_exception(self) -> None:
        from mycelia_platform import MyceliaPlatform
        p = MyceliaPlatform()
        result = p.restore_snapshot({})
        self.assertEqual(result["status"], "error")
        self.assertIn("Snapshot-Datei nicht gefunden", result["message"])

    def test_restore_snapshot_falls_back_to_autosave_when_legacy_path_requested(self) -> None:
        from mycelia_platform import MyceliaPlatform
        p = MyceliaPlatform()
        p.autosave_enabled = False
        p.register_user({"username": "fallback_user", "password": "secret", "profile": {}})
        snap_path = p.snapshot_path
        created = p.create_snapshot({"path": str(snap_path)})
        self.assertEqual(created["status"], "ok")

        fresh = MyceliaPlatform()
        fresh.autosave_enabled = False
        restored = fresh.restore_snapshot({"path": "snapshots/mycelia.snapshot"})
        self.assertEqual(restored["status"], "ok", restored)
        self.assertEqual(restored["path"], str(snap_path.resolve()))
        login = fresh.login_attractor({"username": "fallback_user", "password": "secret"})
        self.assertEqual(login["status"], "ok", login)


if __name__ == "__main__":
    unittest.main()

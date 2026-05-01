from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import mycelia_strict_vram_certify as certify


class StrictVramCertifyTransportTest(unittest.TestCase):
    def test_call_engine_uses_command_payload_protocol(self) -> None:
        captured: dict[str, object] = {}

        class FakeResponse:
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return False
            def read(self) -> bytes:
                return b'{"status":"ok"}'

        def fake_urlopen(req, timeout=20):
            captured["data"] = json.loads(req.data.decode("utf-8"))
            captured["timeout"] = timeout
            return FakeResponse()

        with patch("urllib.request.urlopen", fake_urlopen):
            result = certify.call_engine("http://127.0.0.1:9999", "native_gpu_capability_report", {"x": 1})

        self.assertEqual(result["status"], "ok")
        self.assertEqual(captured["data"], {
            "command": "native_gpu_capability_report",
            "payload": {"x": 1},
        })


if __name__ == "__main__":
    unittest.main()

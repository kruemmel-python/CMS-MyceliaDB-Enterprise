#!/usr/bin/env python3
"""Enterprise strict-VRAM certification orchestrator for MyceliaDB.

This helper talks to the local MyceliaDB HTTP API, requests a native GPU
capability report, optionally runs an external CPU-RAM probe result submission
workflow, and asks the engine for the final strict certification gate.

It intentionally does not claim success unless the engine itself reports:
- native Direct-Ingest envelope opening into VRAM,
- native snapshot restore into VRAM,
- native residency self-test passed,
- negative external CPU-RAM probe for the current engine PID,
- strict certification mode enabled.

Example:
    python tools/mycelia_strict_vram_certify.py --engine http://127.0.0.1:9999 --json-out strict_cert.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Any


def mycelia_local_transport_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    candidates: list[Path] = []
    env_path = os.environ.get("MYCELIA_API_TOKEN_FILE") or os.environ.get("MYCELIA_LOCAL_TRANSPORT_TOKEN_PATH")
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(Path.cwd() / "html" / "keys" / "local_transport.token")
    candidates.append(Path(__file__).resolve().parents[1] / "html" / "keys" / "local_transport.token")
    for candidate in candidates:
        try:
            if candidate.exists():
                token = candidate.read_text(encoding="utf-8").strip()
                if token:
                    headers["X-Mycelia-Local-Token"] = token
                    break
        except Exception:
            continue
    return headers


def call_engine(engine: str, cmd: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = json.dumps({"command": cmd, "payload": payload or {}}).encode("utf-8")
    req = urllib.request.Request(engine, data=body, headers=mycelia_local_transport_headers(), method="POST")
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read().decode("utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise RuntimeError(f"Engine response for {cmd} is not an object")
    return data


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default="http://127.0.0.1:9999", help="MyceliaDB engine endpoint")
    ap.add_argument("--probe-report", help="Optional JSON report from tools/mycelia_memory_probe.py")
    ap.add_argument("--json-out", help="Write certification report to this file")
    args = ap.parse_args(argv)

    result: dict[str, Any] = {
        "tool": "MYCELIA_STRICT_VRAM_CERTIFY_V1",
        "engine": args.engine,
        "steps": {},
    }

    result["steps"]["native_gpu_capability_report"] = call_engine(args.engine, "native_gpu_capability_report", {})
    result["steps"]["native_gpu_residency_selftest"] = call_engine(args.engine, "native_gpu_residency_selftest", {})

    if args.probe_report:
        probe_path = Path(args.probe_report)
        if not probe_path.exists():
            result["steps"]["submit_external_memory_probe"] = {
                "status": "error",
                "message": f"Probe-Report nicht gefunden: {probe_path}. Erzeuge ihn zuerst mit tools/mycelia_memory_probe.py.",
            }
        else:
            report = json.loads(probe_path.read_text(encoding="utf-8"))
            result["steps"]["submit_external_memory_probe"] = call_engine(args.engine, "submit_external_memory_probe", report)

    result["steps"]["strict_vram_certification"] = call_engine(args.engine, "strict_vram_certification", {})
    result["strict_98_security_supported"] = bool(
        result["steps"]["strict_vram_certification"].get("strict_98_security_supported")
    )

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.json_out:
        Path(args.json_out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["strict_98_security_supported"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

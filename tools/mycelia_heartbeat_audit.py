#!/usr/bin/env python3
"""Scheduled MyceliaDB Hardware-Residency Heartbeat Audit.

Runs the same external evidence chain used manually:
1. Ask the Engine for a residency manifest (PID + challenge_id).
2. Generate a fresh random secret that has never been stored in MyceliaDB.
3. Scan the Engine process with mycelia_memory_probe.py via --probe-file.
4. Submit the probe report back to the Engine.
5. Fetch strict_vram_evidence_bundle.
6. Sign the resulting audit evidence with an Ed25519 key.
7. Submit the signed heartbeat to the Engine and persist JSON artifacts.

This tool intentionally runs outside mycelia_platform.py so the Engine does not
certify itself. The plaintext random secret is only used by the external scanner
and is not submitted to the Engine.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import secrets
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any


def mycelia_local_transport_headers(project_root: Path | None = None) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    candidates: list[Path] = []
    if project_root is not None:
        candidates.append(project_root / "html" / "keys" / "local_transport.token")
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

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


TOOL_VERSION = "MYCELIA_HEARTBEAT_AUDIT_TOOL_V1"


def canonical(obj: dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def post_json(engine: str, command: str, payload: dict[str, Any]) -> dict[str, Any]:
    raw = json.dumps({"command": command, "payload": payload}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(engine, data=raw, headers=mycelia_local_transport_headers(Path.cwd()), method="POST")
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def ensure_keypair(private_key_path: Path, public_key_path: Path) -> ed25519.Ed25519PrivateKey:
    private_key_path.parent.mkdir(parents=True, exist_ok=True)
    public_key_path.parent.mkdir(parents=True, exist_ok=True)
    if private_key_path.exists():
        key = serialization.load_pem_private_key(private_key_path.read_bytes(), password=None)
        if not isinstance(key, ed25519.Ed25519PrivateKey):
            raise RuntimeError(f"Existing heartbeat private key is not Ed25519: {private_key_path}")
    else:
        key = ed25519.Ed25519PrivateKey.generate()
        private_key_path.write_bytes(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    public = key.public_key()
    public_key_path.write_bytes(public.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ))
    return key


def run_probe(memory_probe_tool: Path, pid: int, challenge_id: str, secret: str, out_path: Path) -> dict[str, Any]:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, newline="\n", suffix=".probe.txt") as fh:
        probe_file = Path(fh.name)
        fh.write(secret)
        fh.write("\n")
    try:
        cmd = [
            sys.executable,
            str(memory_probe_tool),
            "--pid",
            str(pid),
            "--challenge-id",
            challenge_id,
            "--probe-file",
            str(probe_file),
            "--json-out",
            str(out_path),
        ]
        completed = subprocess.run(cmd, text=True, capture_output=True, timeout=180)
        if completed.returncode != 0:
            raise RuntimeError(
                f"memory probe failed with code {completed.returncode}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
            )
        return json.loads(out_path.read_text(encoding="utf-8"))
    finally:
        try:
            # Best effort: overwrite small file before deletion.
            if probe_file.exists():
                probe_file.write_bytes(b"\x00" * max(1, probe_file.stat().st_size))
                probe_file.unlink()
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", default="http://127.0.0.1:9999/")
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--json-out", default="")
    parser.add_argument("--artifact-dir", default="")
    parser.add_argument("--private-key", default="")
    parser.add_argument("--public-key", default="")
    parser.add_argument("--memory-probe-tool", default="")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    artifact_dir = Path(args.artifact_dir).resolve() if args.artifact_dir else project_root / "docs" / "heartbeat"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    private_key_path = Path(args.private_key).resolve() if args.private_key else project_root / "docs" / "audit_keys" / "heartbeat_ed25519_private.pem"
    public_key_path = Path(args.public_key).resolve() if args.public_key else project_root / "docs" / "audit_keys" / "heartbeat_ed25519_public.pem"
    memory_probe_tool = Path(args.memory_probe_tool).resolve() if args.memory_probe_tool else project_root / "tools" / "mycelia_memory_probe.py"

    started_at = time.time()
    manifest = post_json(args.engine, "residency_audit_manifest", {})
    if manifest.get("status") != "ok":
        raise RuntimeError(f"residency_audit_manifest failed: {manifest}")

    secret = "HEARTBEAT_VRAM_ONLY_" + secrets.token_hex(24)
    secret_sha256 = hashlib.sha256(secret.encode("utf-8")).hexdigest()
    probe_path = artifact_dir / "heartbeat_probe_report.json"
    probe_report = run_probe(memory_probe_tool, int(manifest["pid"]), str(manifest["challenge_id"]), secret, probe_path)

    submit = post_json(args.engine, "submit_external_memory_probe", probe_report)
    if submit.get("status") != "ok":
        raise RuntimeError(f"submit_external_memory_probe failed: {submit}")

    bundle = post_json(args.engine, "strict_vram_evidence_bundle", {})
    if bundle.get("status") != "ok":
        raise RuntimeError(f"strict_vram_evidence_bundle failed: {bundle}")

    signed_payload = {
        "tool_version": TOOL_VERSION,
        "created_at": time.time(),
        "engine": args.engine,
        "pid": int(manifest["pid"]),
        "challenge_id": str(manifest["challenge_id"]),
        "driver_mode": str(bundle.get("driver_mode", "")),
        "secret_sha256": secret_sha256,
        "probe_evidence_digest": str(probe_report.get("evidence_digest", "")),
        "probe_summary": {
            "hits": int(probe_report.get("hits", 0) or 0),
            "strict_hits": int(probe_report.get("strict_hits", 0) or 0),
            "strict_negative": bool(probe_report.get("strict_negative")),
            "scanned_regions": int(probe_report.get("scanned_regions", 0) or 0),
            "scanned_bytes": int(probe_report.get("scanned_bytes", 0) or 0),
        },
        "strict_vram_evidence_bundle": {
            "pid": bundle.get("pid"),
            "driver_mode": bundle.get("driver_mode"),
            "strict_vram_certification_enabled": bundle.get("strict_vram_certification_enabled"),
            "negative_cpu_ram_probe": bundle.get("negative_cpu_ram_probe"),
            "last_restore_mode": bundle.get("last_restore_mode"),
            "last_restore_cpu_materialized": bundle.get("last_restore_cpu_materialized"),
            "strict_98_security_supported": bundle.get("strict_98_security_supported"),
            "strict_vram_certification": {
                "strict_98_security_supported": (bundle.get("strict_vram_certification") or {}).get("strict_98_security_supported"),
                "strict_vram_residency_claim": (bundle.get("strict_vram_certification") or {}).get("strict_vram_residency_claim"),
                "negative_cpu_ram_probe": (bundle.get("strict_vram_certification") or {}).get("negative_cpu_ram_probe"),
                "blockers": (bundle.get("strict_vram_certification") or {}).get("blockers", []),
            },
            "latest_external_memory_probe": {
                "audit_version": (bundle.get("latest_external_memory_probe") or {}).get("audit_version"),
                "classification_version": (bundle.get("latest_external_memory_probe") or {}).get("classification_version"),
                "challenge_id": (bundle.get("latest_external_memory_probe") or {}).get("challenge_id"),
                "pid": (bundle.get("latest_external_memory_probe") or {}).get("pid"),
                "hits": (bundle.get("latest_external_memory_probe") or {}).get("hits"),
                "strict_hits": (bundle.get("latest_external_memory_probe") or {}).get("strict_hits"),
                "strict_negative": (bundle.get("latest_external_memory_probe") or {}).get("strict_negative"),
                "evidence_digest": (bundle.get("latest_external_memory_probe") or {}).get("evidence_digest"),
            },
        },
        "duration_ms": round((time.time() - started_at) * 1000, 3),
    }

    key = ensure_keypair(private_key_path, public_key_path)
    signature = key.sign(canonical(signed_payload))
    heartbeat_envelope = {
        "signed_payload": signed_payload,
        "signature_algorithm": "ed25519",
        "signature_b64": base64.b64encode(signature).decode("ascii"),
        "public_key_path": str(public_key_path),
    }
    heartbeat_submit = post_json(args.engine, "submit_heartbeat_audit", heartbeat_envelope)

    final_report = {
        "status": "ok",
        "audit_version": "MYCELIA_HEARTBEAT_RESIDENCY_AUDIT_V1",
        "signed_payload": signed_payload,
        "signature_b64": heartbeat_envelope["signature_b64"],
        "heartbeat_submit": heartbeat_submit,
        "certified": bool((heartbeat_submit.get("heartbeat_audit") or {}).get("summary", {}).get("certified")),
    }
    out_path = Path(args.json_out).resolve() if args.json_out else artifact_dir / "heartbeat_audit_signed.json"
    out_path.write_text(json.dumps(final_report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(final_report, indent=2, ensure_ascii=False))
    return 0 if final_report["certified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

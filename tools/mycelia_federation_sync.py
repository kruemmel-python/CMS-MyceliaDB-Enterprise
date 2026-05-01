#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, urllib.request, os
from pathlib import Path


def mycelia_local_transport_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    candidates = []
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

def call(engine: str, command: str, payload: dict) -> dict:
    raw = json.dumps({"command": command, "payload": payload}).encode("utf-8")
    req = urllib.request.Request(engine, data=raw, headers=mycelia_local_transport_headers(), method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main() -> int:
    ap = argparse.ArgumentParser(description="MyceliaDB federation export/import helper")
    ap.add_argument("--source", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--min-stability", type=float, default=0.95)
    ap.add_argument("--limit", type=int, default=100)
    args = ap.parse_args()
    export = call(args.source, "federation_export_stable", {"min_stability": args.min_stability, "limit": args.limit})
    print(json.dumps({"export": export}, indent=2, ensure_ascii=False))
    if export.get("status") != "ok":
        return 1
    # Import requires an authenticated admin session in production; this helper
    # intentionally does not bypass the Zero-Logic Gateway.  Operators can paste
    # the export into the Admin Enterprise v1.20 panel or invoke with an admin
    # session token extension.
    print("Export complete. Submit attractors to federation_import_influx via authenticated admin channel.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

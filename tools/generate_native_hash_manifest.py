#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
pairs = [
    ("core_opencl_driver", ROOT / "build" / "CC_OpenCl.dll"),
    ("native_gpu_envelope", ROOT / "build" / "mycelia_gpu_envelope.dll"),
    ("native_gpu_envelope", ROOT / "html" / "native" / "mycelia_gpu_envelope.dll"),
]
libs = {}
for role, path in pairs:
    if path.exists():
        key = role if role not in libs else f"{role}:{path.parent.name}"
        libs[key] = {
            "role": role,
            "path": str(path.relative_to(ROOT)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "algorithm": "sha256",
        }
out = ROOT / "docs" / "native_library_hashes.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"version":"MYCELIA_NATIVE_AUTHENTICITY_V1","generated_at":time.time(),"libraries":libs}, indent=2), encoding="utf-8")
print(out)

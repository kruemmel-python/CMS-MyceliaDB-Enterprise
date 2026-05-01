#!/usr/bin/env python3
from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
candidates = [
    Path.cwd() / "native" / "mycelia_gpu_envelope.dll",
    Path.cwd() / "mycelia_gpu_envelope.dll",
    ROOT / "html" / "native" / "mycelia_gpu_envelope.dll",
    ROOT / "native" / "mycelia_gpu_envelope.dll",
]
env = os.environ.get("MYCELIA_GPU_ENVELOPE_LIBRARY")
if env:
    candidates.insert(0, Path(env))

seen = set()
print("Mycelia Native GPU Envelope Diagnostic")
print(f"cwd={Path.cwd()}")
for cand in candidates:
    cand = cand.resolve()
    if cand in seen:
        continue
    seen.add(cand)
    print(f"- {cand}: {'FOUND' if cand.exists() else 'missing'}")
    if cand.exists():
        try:
            if sys.platform == "win32":
                os.add_dll_directory(str(cand.parent))
            lib = ctypes.CDLL(str(cand))
            required = [
                "mycelia_gpu_envelope_capabilities_v1",
                "mycelia_gpu_residency_selftest_v1",
            ]
            optional = [
                "mycelia_gpu_envelope_open_to_vram_v1",
                "mycelia_gpu_snapshot_restore_to_vram_v1",
            ]
            for name in required + optional:
                print(f"  export {name}: {'OK' if hasattr(lib, name) else 'MISSING'}")
            raise SystemExit(0)
        except Exception as exc:
            print(f"  LOAD ERROR: {exc}")
            raise SystemExit(2)
print("No mycelia_gpu_envelope.dll found.")
raise SystemExit(1)

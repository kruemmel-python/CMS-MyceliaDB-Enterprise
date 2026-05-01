#!/usr/bin/env python3
"""External CPU-RAM probe for MyceliaDB VRAM-residency audits.

The tool scans another process for known UTF-8 probe byte sequences.  It does
not print probe values in the JSON report; it reports SHA-256 hashes and hit
counts only.  Run it from a separate terminal while mycelia_platform.py handles
register/login/query/restore workloads.

Windows requires PROCESS_QUERY_INFORMATION and PROCESS_VM_READ rights.  Linux
requires permission to read /proc/<pid>/mem and often ptrace_scope adjustment or
root privileges.

Example:
    python tools/mycelia_memory_probe.py --pid 1234 --probe Leipzig --probe "Krümmel" --json-out probe.json
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import platform
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SCANNER_VERSION = "MYCELIA_CPU_RAM_PROBE_V3_CLASSIFIED_CANARY"


@dataclass
class Region:
    start: int
    end: int
    readable: bool
    label: str = ""

    @property
    def size(self) -> int:
        return max(0, self.end - self.start)


SENSITIVE_KINDS = {"sensitive_cleartext", "profile_cleartext", "content_body", "credential_equivalent"}
CANARY_KINDS = {"probe_canary_positive"}
NON_STRICT_KINDS = {"public_identifier", "audit_artifact"}


def _auto_probe_kind(value: str) -> str:
    """Classify probes without leaking the plaintext value into the report.

    64-hex strings are operational node handles/signatures in MyceliaDB.  They
    are still reported, but strict residency certification does not treat them
    like user-provided cleartext.  Everything else defaults to sensitive.
    """
    if re.fullmatch(r"[0-9a-fA-F]{64}", value or ""):
        return "public_identifier"
    if re.fullmatch(r"[0-9a-fA-F]{32}", value or ""):
        return "audit_artifact"
    return "sensitive_cleartext"


@dataclass(frozen=True)
class ProbeSpec:
    value: str
    kind: str


@dataclass(frozen=True)
class EncodedProbe:
    raw: bytes
    kind: str
    source_hash: str
    encoding: str

    @property
    def hash(self) -> str:
        return _hash_probe(self.raw)


def _probe_bytes(specs: list[ProbeSpec]) -> list[EncodedProbe]:
    out: list[EncodedProbe] = []
    for spec in specs:
        if not spec.value:
            continue
        source_hash = hashlib.sha256(spec.value.encode("utf-8")).hexdigest()
        out.append(EncodedProbe(spec.value.encode("utf-8"), spec.kind, source_hash, "utf-8"))
        # Many Python/Windows allocations may use UTF-16LE internally.
        out.append(EncodedProbe(spec.value.encode("utf-16le"), spec.kind, source_hash, "utf-16le"))
    # preserve order, remove duplicates by bytes
    unique: list[EncodedProbe] = []
    seen: set[bytes] = set()
    for item in out:
        if item.raw not in seen:
            seen.add(item.raw)
            unique.append(item)
    return unique


def _load_probe_file(path: str | None) -> list[str]:
    if not path:
        return []
    p = Path(path)
    return [line.rstrip("\n") for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def _hash_probe(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _scan_buffer(buf: bytes, probes: list[EncodedProbe]) -> list[dict[str, object]]:
    hits: list[dict[str, object]] = []
    for probe in probes:
        idx = buf.find(probe.raw)
        if idx >= 0:
            strict_relevant = probe.kind in SENSITIVE_KINDS
            hits.append({
                "probe_sha256": probe.hash,
                "source_probe_sha256": probe.source_hash,
                "probe_kind": probe.kind,
                "strict_relevant": strict_relevant,
                "encoding": probe.encoding,
                "encoding_bytes": len(probe.raw),
                "offset": idx,
            })
    return hits


def _linux_regions(pid: int) -> Iterable[Region]:
    maps_path = Path(f"/proc/{pid}/maps")
    for line in maps_path.read_text(errors="ignore").splitlines():
        parts = line.split(maxsplit=5)
        if len(parts) < 2:
            continue
        addr, perms = parts[0], parts[1]
        label = parts[5] if len(parts) >= 6 else ""
        if "r" not in perms:
            continue
        start_s, end_s = addr.split("-", 1)
        yield Region(int(start_s, 16), int(end_s, 16), True, label)


def _scan_linux(pid: int, probes: list[EncodedProbe], max_region_bytes: int) -> tuple[list[dict[str, object]], int, int]:
    findings: list[dict[str, object]] = []
    scanned_regions = 0
    scanned_bytes = 0
    mem_path = Path(f"/proc/{pid}/mem")
    with mem_path.open("rb", buffering=0) as mem:
        for region in _linux_regions(pid):
            if region.size <= 0:
                continue
            to_read = min(region.size, max_region_bytes)
            try:
                mem.seek(region.start)
                data = mem.read(to_read)
            except Exception:
                continue
            scanned_regions += 1
            scanned_bytes += len(data)
            for hit in _scan_buffer(data, probes):
                findings.append({
                    "region_start": hex(region.start),
                    "region_end": hex(region.end),
                    "region_label": region.label,
                    **hit,
                })
    return findings, scanned_regions, scanned_bytes


# Windows structures based on MEMORY_BASIC_INFORMATION.
class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", ctypes.c_ulong),
        ("RegionSize", ctypes.c_size_t),
        ("State", ctypes.c_ulong),
        ("Protect", ctypes.c_ulong),
        ("Type", ctypes.c_ulong),
    ]


def _scan_windows(pid: int, probes: list[EncodedProbe], max_region_bytes: int) -> tuple[list[dict[str, object]], int, int]:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010
    MEM_COMMIT = 0x1000
    PAGE_NOACCESS = 0x01
    PAGE_GUARD = 0x100

    handle = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not handle:
        raise PermissionError(f"OpenProcess failed for pid={pid}, error={ctypes.get_last_error()}")

    findings: list[dict[str, object]] = []
    scanned_regions = 0
    scanned_bytes = 0
    address = 0
    mbi = MEMORY_BASIC_INFORMATION()
    try:
        while kernel32.VirtualQueryEx(handle, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi)):
            base = int(mbi.BaseAddress or 0)
            size = int(mbi.RegionSize or 0)
            protect = int(mbi.Protect or 0)
            state = int(mbi.State or 0)
            readable = state == MEM_COMMIT and not (protect & PAGE_NOACCESS) and not (protect & PAGE_GUARD)
            if readable and size > 0:
                to_read = min(size, max_region_bytes)
                buf = ctypes.create_string_buffer(to_read)
                bytes_read = ctypes.c_size_t(0)
                ok = kernel32.ReadProcessMemory(
                    handle,
                    ctypes.c_void_p(base),
                    buf,
                    to_read,
                    ctypes.byref(bytes_read),
                )
                if ok and bytes_read.value:
                    data = buf.raw[: bytes_read.value]
                    scanned_regions += 1
                    scanned_bytes += len(data)
                    for hit in _scan_buffer(data, probes):
                        findings.append({
                            "region_start": hex(base),
                            "region_end": hex(base + size),
                            **hit,
                        })
            next_address = base + size
            if next_address <= address:
                break
            address = next_address
    finally:
        kernel32.CloseHandle(handle)
    return findings, scanned_regions, scanned_bytes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan a running process for sensitive cleartext probes.")
    parser.add_argument("--pid", type=int, required=True, help="Target mycelia_platform.py process id")
    parser.add_argument("--probe", action="append", default=[], help="Plaintext probe; may be repeated. Auto-classifies 64-hex values as public_identifier.")
    parser.add_argument("--probe-sensitive", action="append", default=[], help="Sensitive cleartext probe; strict hits block certification.")
    parser.add_argument("--probe-public", action="append", default=[], help="Public identifier probe; hits are reported but do not block strict certification.")
    parser.add_argument("--probe-audit", action="append", default=[], help="Audit artifact probe; hits are reported but do not block strict certification.")
    parser.add_argument("--probe-file", help="UTF-8 file with one sensitive plaintext probe per line")
    parser.add_argument("--operation", action="append", default=[], help="Operation observed during scan, e.g. login_attractor")
    parser.add_argument("--challenge-id", default="", help="Challenge id from residency_audit_manifest")
    parser.add_argument("--json-out", default="", help="Write report to this path")
    parser.add_argument("--max-region-bytes", type=int, default=64 * 1024 * 1024, help="Cap bytes per memory region")
    parser.add_argument("--canary-positive", action="append", default=[], help="Toxic canary expected to be found; proves scanner visibility / anti-evasion baseline.")
    parser.add_argument("--require-canary-positive", action="store_true", help="Fail the report unless all --canary-positive values are found at least once.")
    args = parser.parse_args(argv)

    specs: list[ProbeSpec] = []
    specs.extend(ProbeSpec(value, _auto_probe_kind(value)) for value in list(args.probe))
    specs.extend(ProbeSpec(value, "sensitive_cleartext") for value in list(args.probe_sensitive))
    specs.extend(ProbeSpec(value, "public_identifier") for value in list(args.probe_public))
    specs.extend(ProbeSpec(value, "audit_artifact") for value in list(args.probe_audit))
    specs.extend(ProbeSpec(value, "probe_canary_positive") for value in list(args.canary_positive))
    specs.extend(ProbeSpec(value, "sensitive_cleartext") for value in _load_probe_file(args.probe_file))
    probes = _probe_bytes(specs)
    if not probes:
        parser.error("At least one --probe, --probe-sensitive, --probe-public, --probe-audit or --probe-file entry is required")

    started = time.time()
    system = platform.system().lower()
    try:
        if system == "windows":
            findings, regions, scanned_bytes = _scan_windows(args.pid, probes, args.max_region_bytes)
        elif system == "linux":
            findings, regions, scanned_bytes = _scan_linux(args.pid, probes, args.max_region_bytes)
        else:
            raise RuntimeError(f"Unsupported OS for direct memory scanning: {platform.system()}")
        status = "ok"
        error = ""
    except Exception as exc:
        findings, regions, scanned_bytes = [], 0, 0
        status = "error"
        error = str(exc)

    # Hash both UTF-8 and UTF-16LE forms, because both were scanned.
    probe_hashes = [p.hash for p in probes]
    probe_manifest = [
        {
            "probe_sha256": p.hash,
            "source_probe_sha256": p.source_hash,
            "probe_kind": p.kind,
            "strict_relevant": p.kind in SENSITIVE_KINDS,
            "encoding": p.encoding,
            "encoding_bytes": len(p.raw),
        }
        for p in probes
    ]
    hit_counts_by_kind: dict[str, int] = {}
    strict_hits = 0
    for hit in findings:
        kind = str(hit.get("probe_kind", "sensitive_cleartext"))
        hit_counts_by_kind[kind] = hit_counts_by_kind.get(kind, 0) + 1
        if bool(hit.get("strict_relevant", kind in SENSITIVE_KINDS)):
            strict_hits += 1
    strict_negative = status == "ok" and strict_hits == 0 and regions > 0 and scanned_bytes > 0
    canary_hashes = {hashlib.sha256(v.encode("utf-8")).hexdigest() for v in list(args.canary_positive)}
    canary_hits = {str(hit.get("source_probe_sha256", "")) for hit in findings if str(hit.get("probe_kind", "")) == "probe_canary_positive"}
    canary_positive_ok = (not canary_hashes) or canary_hashes.issubset(canary_hits)
    if args.require_canary_positive and not canary_positive_ok and status == "ok":
        status = "error"
        error = (error + "; " if error else "") + "Required positive scanner canary was not observed."
        strict_negative = False
    report = {
        "status": status,
        "scanner_version": SCANNER_VERSION,
        "pid": args.pid,
        "challenge_id": args.challenge_id,
        "started_at": started,
        "finished_at": time.time(),
        "duration_ms": round((time.time() - started) * 1000, 3),
        "platform": platform.platform(),
        "operations": args.operation,
        "probe_sha256": probe_hashes,
        "probe_manifest": probe_manifest,
        "hit_counts_by_kind": hit_counts_by_kind,
        "hits": len(findings),
        "strict_hits": strict_hits,
        "non_strict_hits": max(0, len(findings) - strict_hits),
        "negative": strict_negative,
        "strict_negative": strict_negative,
        "raw_negative": status == "ok" and len(findings) == 0 and regions > 0 and scanned_bytes > 0,
        "scanned_regions": regions,
        "scanned_bytes": scanned_bytes,
        "canary_positive_required": bool(args.require_canary_positive),
        "canary_positive_ok": canary_positive_ok,
        "canary_expected_count": len(canary_hashes),
        "canary_hit_count": len(canary_hits),
        "findings": findings[:100],
        "truncated_findings": max(0, len(findings) - 100),
        "error": error,
    }
    report["evidence_digest"] = hashlib.sha256(
        json.dumps({k: v for k, v in report.items() if k != "evidence_digest"}, sort_keys=True).encode("utf-8")
    ).hexdigest()

    raw = json.dumps(report, ensure_ascii=False, indent=2)
    if args.json_out:
        Path(args.json_out).write_text(raw, encoding="utf-8")
    print(raw)
    return 0 if status == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())

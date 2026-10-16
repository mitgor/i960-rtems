#!/usr/bin/env python3
"""Verify a fallback-only loader hook entirely in memory; never emit flash."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "startup"))
from analyze import analyze
from audit_helper_site import aligned_refs, word
from verify_full_dump import unpack

LOADER_BASE = 0xC000A000
CALLSITE = 0xC000C638
CAVE = 0xC000E1D8
TABLE_8E = 0xC00234F8
TABLE_8F = 0xC00234FC
STOCK_UNSUPPORTED = 0xC0023790
STOCK_SETUP = 0xC000C6C0
EXPECTED_CALLSITE = bytes.fromhex("a01b0009")
EXPECTED_STUB = bytes.fromhex(
    "e8e4ff09"                 # call stock setup
    "0030888cf0e100c0"         # lda fallback,g1
    "00308892fc3402c0"         # st g1, table[0x8f]
    "0000000a"                 # ret
    "a0550108"                 # b stock unsupported
)


def audit(flash, stub, callsite):
    if stub != EXPECTED_STUB or callsite != EXPECTED_CALLSITE:
        raise ValueError("unreviewed routing code")
    stock = analyze(flash)
    if not stock["accepted_stock"]:
        raise ValueError("requires exact accepted paired stock image")
    loader = stock["loader"]
    base = loader["flash_offset"]
    size = loader["size"]
    if loader["destination"] != LOADER_BASE or size != 0x6000:
        raise ValueError("unexpected loader mapping")
    site = base + CALLSITE - LOADER_BASE
    cave = base + CAVE - LOADER_BASE
    if flash[site:site + 4] != bytes.fromhex("88000009"):
        raise ValueError("stock setup call changed")
    if flash[cave:base + size] != b"\xff" * (base + size - cave):
        raise ValueError("loader cave no longer erased")
    region = next(r for r in stock["regions"] if r["selector"] == 2)
    runtime, _ = unpack(flash[stock["runtime"]["flash_zip_offset"]:
                              region["offset"] + region["size"] - 0xA0])
    if word(runtime, TABLE_8E - 0xC0010000) != 0xC002371C:
        raise ValueError("normal 0x8e target changed")
    if word(runtime, TABLE_8F - 0xC0010000) != STOCK_UNSUPPORTED:
        raise ValueError("stock 0x8f target changed")
    for data in (flash[base:base + size], runtime):
        if aligned_refs(data, CAVE, LOADER_BASE + size):
            raise ValueError("stock references loader cave")
    # This single entry route has been traced; it is not a proof for all
    # recovery/board variants. The compiled fallback has no request success path.
    candidate = bytearray(flash)
    candidate[site:site + len(callsite)] = callsite
    candidate[cave:cave + len(stub)] = stub
    checksum = sum(struct.unpack_from(f"<{size // 4}I", candidate, base)) & 0xFFFFFFFF
    trailer = stock["trailer_offset"]
    struct.pack_into("<I", candidate, trailer + 24, checksum)
    trailer_sum = sum(struct.unpack_from("<31I", candidate, trailer)) & 0xFFFFFFFF
    struct.pack_into("<I", candidate, trailer + 124, trailer_sum)
    checked = analyze(candidate)
    if checked["accepted_stock"] or checked["runtime"] != stock["runtime"]:
        raise ValueError("candidate runtime/status mismatch")
    if not checked["loader"]["checksum_passed"] or not checked["trailer_checksum_passed"]:
        raise ValueError("candidate known checksums failed")
    allowed = (set(range(site, site + len(callsite))) |
               set(range(cave, cave + len(stub))) |
               set(range(trailer + 24, trailer + 28)) |
               set(range(trailer + 124, trailer + 128)))
    changed = {i for i, (old, new) in enumerate(zip(flash, candidate)) if old != new}
    if not changed <= allowed or not {site, cave} <= changed:
        raise ValueError("unreviewed flash difference")
    return {
        "stock_sha256": stock["flash_sha256"],
        "candidate_sha256_in_memory_only": hashlib.sha256(candidate).hexdigest(),
        "callsite": f"0x{CALLSITE:08x}",
        "original_call_target": f"0x{STOCK_SETUP:08x}",
        "hook": f"0x{CAVE:08x}",
        "fallback": f"0x{CAVE + 24:08x}",
        "runtime_table_8e_unchanged": f"0x{TABLE_8E:08x}",
        "runtime_table_8f_stock": f"0x{TABLE_8F:08x} -> 0x{STOCK_UNSUPPORTED:08x}",
        "runtime_table_8f_loader_write": f"0x{TABLE_8F:08x} -> 0x{CAVE + 24:08x}",
        "fallback_target": f"0x{STOCK_UNSUPPORTED:08x}",
        "stub_bytes": len(stub),
        "changed_flash_bytes": len(changed),
        "loader_checksum": f"0x{checksum:08x}",
        "trailer_checksum": f"0x{trailer_sum:08x}",
        "runtime_sha256_unchanged": checked["runtime"]["sha256"],
        "known_checksums_pass": True,
        "entry_executed_or_boot_proven": False,
        "image_written": False,
        "ping_implemented": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("flash", type=Path)
    parser.add_argument("stub", type=Path)
    parser.add_argument("callsite", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.flash.read_bytes(), args.stub.read_bytes(),
                           args.callsite.read_bytes()), indent=2))

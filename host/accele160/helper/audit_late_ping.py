#!/usr/bin/env python3
"""Audit the late-loader zero-DMA PING route in memory; emit no flash image."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from audit_dispatch_rehearsal import analyze, unpack, aligned_refs, word

LOADER_BASE = 0xC000A000
RUNTIME_BASE = 0xC0010000
LOADER_RETURN = 0xC000C9CC
CAVE = 0xC000E1D8
TABLE_8E = 0xC00234F8
TABLE_8F = 0xC00234FC
PING = CAVE + 20
HANDLER_SHA256 = "dbbfa3c99bdc30895a811b4e8828d2edc38203eb2762170cb2304a549bd1bf45"
CALLSITE = bytes.fromhex("0c180008")


def expect(blob, base, address, raw, name):
    expected = bytes.fromhex(raw)
    if blob[address - base:address - base + len(expected)] != expected:
        raise ValueError(f"stock {name} anchor changed")


def audit(flash, handler, callsite):
    if (len(handler) != 144 or hashlib.sha256(handler).hexdigest() != HANDLER_SHA256
            or callsite != CALLSITE):
        raise ValueError("unreviewed late PING binary or branch")
    stock = analyze(flash)
    if not stock["accepted_stock"]:
        raise ValueError("requires exact accepted paired stock flash")
    loader_info = stock["loader"]
    if loader_info["destination"] != LOADER_BASE or loader_info["entry"] != 0xC000C590:
        raise ValueError("unexpected loader address or entry")
    base, size = loader_info["flash_offset"], loader_info["size"]
    loader = flash[base:base + size]
    boot = flash[0xF0000:0x100000]
    region = next(r for r in stock["regions"] if r["selector"] == 2)
    runtime, _ = unpack(flash[stock["runtime"]["flash_zip_offset"]:
                              region["offset"] + region["size"] - 0xA0])

    # The boot block calls the descriptor-selected loader, and enables the
    # data cache only after it returns. On the primary loader entry the ZIP
    # expansion precedes stock setup; the descriptor pass then reaches this
    # common return. These exact bytes are necessary, not a full CFG proof.
    expect(boot, 0xFEFF0000, 0xFEFFC11C, "a4070009", "loader call")
    expect(boot, 0xFEFF0000, 0xFEFFC120, "011e8865", "D-cache enable")
    expect(boot, 0xFEFF0000, 0xFEFFC124, "00100484", "main handoff")
    expect(loader, LOADER_BASE, 0xC000C590, "1016205c1116285c", "entry")
    expect(loader, LOADER_BASE, 0xC000C634, "8ce0ff09", "ZIP expansion")
    expect(loader, LOADER_BASE, 0xC000C638, "88000009", "stock setup")
    expect(loader, LOADER_BASE, 0xC000C650, "30010008", "descriptor pass")
    expect(loader, LOADER_BASE, LOADER_RETURN, "0000000a", "common return")
    if loader[CAVE - LOADER_BASE:] != b"\xff" * (size - (CAVE - LOADER_BASE)):
        raise ValueError("copied-loader cave no longer erased")
    for blob in (loader, runtime):
        if aligned_refs(blob, CAVE, LOADER_BASE + size):
            raise ValueError("stock image references cave")
    if (word(runtime, TABLE_8E - RUNTIME_BASE) != 0xC002371C or
            word(runtime, TABLE_8F - RUNTIME_BASE) != 0xC0023790):
        raise ValueError("stock IOCTL table changed")
    if (word(handler, 4) != PING or word(handler, 12) != TABLE_8F or
            handler[16:20] != bytes.fromhex("0000000a") or
            handler[20:24] != bytes.fromhex("02202988") or
            handler[-8:-4] != bytes.fromhex("e0060408") or
            handler[-4:] != bytes.fromhex("2c550108")):
        raise ValueError("late hook or completion anchor changed")

    candidate = bytearray(flash)
    site = base + LOADER_RETURN - LOADER_BASE
    cave = base + CAVE - LOADER_BASE
    candidate[site:site + 4] = callsite
    candidate[cave:cave + len(handler)] = handler
    checksum = sum(struct.unpack_from(f"<{size // 4}I", candidate, base)) & 0xFFFFFFFF
    trailer = stock["trailer_offset"]
    struct.pack_into("<I", candidate, trailer + 24, checksum)
    trailer_sum = sum(struct.unpack_from("<31I", candidate, trailer)) & 0xFFFFFFFF
    struct.pack_into("<I", candidate, trailer + 124, trailer_sum)
    checked = analyze(candidate)
    if (checked["accepted_stock"] or checked["runtime"] != stock["runtime"] or
            not checked["loader"]["checksum_passed"] or
            not checked["trailer_checksum_passed"]):
        raise ValueError("candidate structural verification failed")
    allowed = (set(range(site, site + 4)) |
               set(range(cave, cave + len(handler))) |
               set(range(trailer + 24, trailer + 28)) |
               set(range(trailer + 124, trailer + 128)))
    changed = {i for i, (a, b) in enumerate(zip(flash, candidate)) if a != b}
    if not changed <= allowed or not {site, cave} <= changed:
        raise ValueError("candidate changed unexpected bytes")
    return {
        "stock_sha256": stock["flash_sha256"],
        "in_memory_candidate_sha256": hashlib.sha256(candidate).hexdigest(),
        "handler_sha256": HANDLER_SHA256,
        "late_branch": f"0x{LOADER_RETURN:08x} -> 0x{CAVE:08x}",
        "ping_entry": f"0x{PING:08x}",
        "changed_flash_bytes": len(changed),
        "loader_checksum": f"0x{checksum:08x}",
        "trailer_checksum": f"0x{trailer_sum:08x}",
        "runtime_sha256_unchanged": checked["runtime"]["sha256"],
        "known_checksums_pass": True,
        "image_written": False,
        "card_executed": False,
        "hook_persistence_or_recovery_proven": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("flash", type=Path)
    parser.add_argument("handler", type=Path)
    parser.add_argument("callsite", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.flash.read_bytes(), args.handler.read_bytes(),
                           args.callsite.read_bytes()), indent=2))

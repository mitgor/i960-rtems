#!/usr/bin/env python3
"""Verify a strict no-DMA PING image in memory; never export or flash it."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from audit_dispatch_rehearsal import (
    CALLSITE, CAVE, EXPECTED_CALLSITE, LOADER_BASE, STOCK_UNSUPPORTED,
    TABLE_8E, TABLE_8F, word,
)
from audit_dispatch_rehearsal import analyze, unpack
from audit_helper_site import aligned_refs

HANDLER_SHA256 = "0ea35c1381dd17938cfc42b112a353aad6cb5299036e17c75b9e586d463f0e44"
PING_ENTRY = CAVE + 24
REJECT_ENTRY = CAVE + 144
STOCK_COMPLETE = 0xC004E940


def audit(flash, handler, callsite):
    if (hashlib.sha256(handler).hexdigest() != HANDLER_SHA256 or
            len(handler) != 148 or callsite != EXPECTED_CALLSITE):
        raise ValueError("unreviewed i960 PING binary or callsite")
    stock = analyze(flash)
    if not stock["accepted_stock"]:
        raise ValueError("requires exact accepted paired stock image")
    loader = stock["loader"]
    if loader["destination"] != LOADER_BASE or loader["size"] != 0x6000:
        raise ValueError("unexpected loader mapping")
    base = loader["flash_offset"]
    size = loader["size"]
    site = base + CALLSITE - LOADER_BASE
    cave = base + CAVE - LOADER_BASE
    if flash[site:site + 4] != bytes.fromhex("88000009"):
        raise ValueError("stock setup call changed")
    if flash[cave:base + size] != b"\xff" * (base + size - cave):
        raise ValueError("loader cave changed")
    region = next(r for r in stock["regions"] if r["selector"] == 2)
    runtime, _ = unpack(flash[stock["runtime"]["flash_zip_offset"]:
                              region["offset"] + region["size"] - 0xA0])
    if (word(runtime, TABLE_8E - 0xC0010000) != 0xC002371C or
            word(runtime, TABLE_8F - 0xC0010000) != STOCK_UNSUPPORTED):
        raise ValueError("stock IOCTL table changed")
    for data in (flash[base:base + size], runtime):
        if aligned_refs(data, CAVE, LOADER_BASE + size):
            raise ValueError("stock references loader cave")
    # Structural anchors for the exact disassembled machine code. Its SHA
    # fixes all instructions, while these anchors explain the dispatch path.
    if (handler[:4] != bytes.fromhex("e8e4ff09") or
            word(handler, 8) != PING_ENTRY or word(handler, 16) != TABLE_8F or
            handler[24:28] != bytes.fromhex("02202988") or
            handler[-8:-4] != bytes.fromhex("dc060408") or
            handler[-4:] != bytes.fromhex("28550108")):
        raise ValueError("PING control-flow anchor changed")
    candidate = bytearray(flash)
    candidate[site:site + 4] = callsite
    candidate[cave:cave + len(handler)] = handler
    loader_sum = sum(struct.unpack_from(f"<{size // 4}I", candidate, base)) & 0xFFFFFFFF
    trailer = stock["trailer_offset"]
    struct.pack_into("<I", candidate, trailer + 24, loader_sum)
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
        raise ValueError("candidate modified unrelated bytes")
    return {
        "stock_sha256": stock["flash_sha256"],
        "in_memory_candidate_sha256": hashlib.sha256(candidate).hexdigest(),
        "handler_sha256": HANDLER_SHA256,
        "handler_bytes": len(handler),
        "handler_entry": f"0x{PING_ENTRY:08x}",
        "reject_target": f"0x{STOCK_UNSUPPORTED:08x}",
        "success_target": f"0x{STOCK_COMPLETE:08x}",
        "ioctl_8e_unchanged": f"0x{TABLE_8E:08x}",
        "ioctl_8f_loader_write": f"0x{TABLE_8F:08x} -> 0x{PING_ENTRY:08x}",
        "changed_flash_bytes": len(changed),
        "loader_checksum": f"0x{loader_sum:08x}",
        "trailer_checksum": f"0x{trailer_sum:08x}",
        "runtime_sha256_unchanged": checked["runtime"]["sha256"],
        "known_checksums_pass": True,
        "image_written": False,
        "card_executed": False,
        "boot_or_recovery_qualified": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("flash", type=Path)
    parser.add_argument("handler", type=Path)
    parser.add_argument("callsite", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.flash.read_bytes(), args.handler.read_bytes(),
                           args.callsite.read_bytes()), indent=2))

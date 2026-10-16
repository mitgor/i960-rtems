#!/usr/bin/env python3
"""Audit stock helper sites and rehearse checksum packaging entirely offline.

The in-memory candidate inserts the existing bounded probe in erased loader
space but does not link it to dispatch. No flashable image is written.
"""

import argparse
import hashlib
import json
from pathlib import Path
import struct

from analyze import analyze
from verify_full_dump import unpack

LOADER_CAVE = 0x41D8
NORMAL_CALLBACK = 0xC0023910
NORMAL_CALLBACK_SITES = (0x2A38, 0x2B90, 0x2EB4, 0x2F9C,
                         0x307C, 0x315C, 0x323C, 0x336C)
RUNTIME_BASE = 0xC0010000
LOADER_BASE = 0xC000A000


def word(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def aligned_refs(data, lo, hi):
    return [(offset, word(data, offset)) for offset in range(0, len(data) - 3, 4)
            if lo <= word(data, offset) < hi]


def inspect(flash, probe):
    original = analyze(flash)
    if not original["accepted_stock"]:
        raise ValueError("requires accepted paired 6.00-05 stock dump")
    loader_info = original["loader"]
    lo = loader_info["flash_offset"]
    size = loader_info["size"]
    loader = flash[lo:lo + size]
    region = next(r for r in original["regions"] if r["selector"] == 2)
    runtime, _ = unpack(flash[original["runtime"]["flash_zip_offset"]:
                              region["offset"] + region["size"] - 0xA0])
    if hashlib.sha256(runtime).hexdigest() != original["runtime"]["sha256"]:
        raise ValueError("runtime hash mismatch")
    if runtime[0x132A8:0x132AC] != bytes.fromhex("15208980"):
        raise ValueError("IOCTL subcommand input changed")
    if runtime[0x132B0:0x132B4] != bytes.fromhex("0149a459"):
        raise ValueError("IOCTL table index changed")
    table = 0x132C4
    if word(runtime, table + (0x8E - 1) * 4) != 0xC002371C:
        raise ValueError("stock 0x8e route changed")
    if word(runtime, table + (0x8F - 1) * 4) != 0xC0023790:
        raise ValueError("0x8f is not the stock unsupported route")
    if runtime[0x1379C:0x137B0] != bytes.fromhex(
            "0401988c5620998acc6bfe090416805c94b10208"):
        raise ValueError("unsupported status/completion path changed")
    sites = [offset for offset in range(0, size - 3, 4)
             if word(loader, offset) == NORMAL_CALLBACK]
    if sites != list(NORMAL_CALLBACK_SITES):
        raise ValueError("stock callback initializers changed")
    if not probe or len(probe) > 256 or len(probe) % 4:
        raise ValueError("bounded probe must be 4-byte aligned and at most 256 bytes")
    if any(x != 0xFF for x in loader[LOADER_CAVE:]):
        raise ValueError("loader cave is not entirely erased")
    cave_address = LOADER_BASE + LOADER_CAVE
    if aligned_refs(loader, cave_address, LOADER_BASE + size):
        raise ValueError("loader references proposed cave")
    if aligned_refs(runtime, cave_address, LOADER_BASE + size):
        raise ValueError("runtime references proposed cave")
    # Rehearse only the known additive checksums. This does not establish all
    # vendor update rules, boot behavior, recovery, or a callable entry.
    candidate = bytearray(flash)
    candidate[lo + LOADER_CAVE:lo + LOADER_CAVE + len(probe)] = probe
    checksum = sum(struct.unpack_from(f"<{size // 4}I", candidate, lo)) & 0xFFFFFFFF
    trailer = original["trailer_offset"]
    struct.pack_into("<I", candidate, trailer + 6 * 4, checksum)
    trailer_checksum = sum(struct.unpack_from("<31I", candidate, trailer)) & 0xFFFFFFFF
    struct.pack_into("<I", candidate, trailer + 31 * 4, trailer_checksum)
    checked = analyze(candidate)
    if checked["accepted_stock"] or not checked["loader"]["checksum_passed"]:
        raise ValueError("candidate verification failed")
    if checked["runtime"]["sha256"] != original["runtime"]["sha256"]:
        raise ValueError("runtime changed")
    changed = [i for i, (a, b) in enumerate(zip(flash, candidate)) if a != b]
    allowed = set(range(lo + LOADER_CAVE, lo + LOADER_CAVE + len(probe)))
    allowed.update(range(trailer + 24, trailer + 28))
    allowed.update(range(trailer + 124, trailer + 128))
    if not set(changed) <= allowed:
        raise ValueError("candidate modified an unexpected flash address")
    return {
        "stock_sha256": original["flash_sha256"],
        "runtime_sha256_unchanged": original["runtime"]["sha256"],
        "loader_cave": {"loader_offset": f"0x{LOADER_CAVE:x}",
                        "flash_offset": f"0x{lo + LOADER_CAVE:x}",
                        "ram_address": f"0x{cave_address:08x}",
                        "erased_bytes": size - LOADER_CAVE,
                        "aligned_absolute_references": 0},
        "ioctl_dispatch": {
            "subcommand_field": "+0x15", "index_subtract": 1,
            "stock_0x8e_target": "0xc002371c (normal SET_MEM_MBOX slot)",
            "stock_0x8f_target": "0xc0023790 (unsupported, status 0x104)",
            "table_runtime_address": f"0x{RUNTIME_BASE + table:08x}",
            "normal_callback_initializer_offsets": [f"0x{x:x}" for x in sites],
        },
        "offline_packaging_rehearsal": {
            "embedded_probe_bytes": len(probe),
            "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
            "changed_byte_count": len(changed),
            "loader_checksum": f"0x{checksum:08x}",
            "trailer_checksum": f"0x{trailer_checksum:08x}",
            "known_checksums_pass": True,
            "runtime_unchanged": True,
            "entry_wired": False,
            "image_written": False,
            "boot_or_recovery_qualified": False,
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("flash", type=Path)
    parser.add_argument("probe", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.flash.read_bytes(), args.probe.read_bytes()), indent=2))

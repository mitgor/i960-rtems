#!/usr/bin/env python3
"""Compare a guarded live stock dispatch-page capture with exact stock ROM."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from audit_dispatch_rehearsal import analyze, unpack

PAGE_START = 0xC0023000
RUNTIME_START = 0xC0010000
PAGE_BYTES = 4096


def audit(flash, page):
    stock = analyze(flash)
    if not stock["accepted_stock"]:
        raise ValueError("requires exact accepted paired stock flash")
    if len(page) != PAGE_BYTES:
        raise ValueError("expected one 4 KiB translated table page")
    region = next(r for r in stock["regions"] if r["selector"] == 2)
    runtime, _ = unpack(flash[stock["runtime"]["flash_zip_offset"]:
                              region["offset"] + region["size"] - 0xA0])
    start = PAGE_START - RUNTIME_START
    expected = runtime[start:start + PAGE_BYTES]
    if page != expected:
        changes = sum(a != b for a, b in zip(page, expected))
        raise ValueError(f"live page differs from stock runtime at {changes} bytes")
    table_8e = struct.unpack_from("<I", page, 0x4F8)[0]
    table_8f = struct.unpack_from("<I", page, 0x4FC)[0]
    if (table_8e, table_8f) != (0xC002371C, 0xC0023790):
        raise ValueError("unexpected stock IOCTL entries")
    return {
        "stock_flash_sha256": stock["flash_sha256"],
        "live_page_start": f"0x{PAGE_START:08x}",
        "live_page_sha256": hashlib.sha256(page).hexdigest(),
        "matched_stock_runtime_bytes": PAGE_BYTES,
        "stock_8e": f"0x{table_8e:08x}",
        "stock_8f": f"0x{table_8f:08x}",
        "modified_firmware_executed": False,
        "patched_table_persistence_proven": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("flash", type=Path)
    parser.add_argument("live_page", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.flash.read_bytes(), args.live_page.read_bytes()),
                     indent=2))

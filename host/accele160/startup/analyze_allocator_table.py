#!/usr/bin/env python3
"""Decode the stock AcceleRAID 160 32 KiB allocation table from a page capture."""

import argparse
import hashlib
import json
from pathlib import Path
import struct

BASE = 0xC0000000
BLOCK = 0x8000
COUNT_OFFSET = 0x2A0  # c03852a0 in the c0385000 captured page
OWNER_OFFSET = 0x6A0  # c03856a0 in the same page
EXPECTED_SHA = "f78d008373c0f0b9103f417377db279a0bcccbe5f47cd79b469b22b6a6f55096"


def parse(page: bytes, *, pin: bool = True) -> dict:
    if len(page) != 4096 or (pin and hashlib.sha256(page).hexdigest() != EXPECTED_SHA):
        raise ValueError("allocator-page length or exact snapshot hash")
    counts = struct.unpack_from("<256I", page, COUNT_OFFSET)
    owners = struct.unpack_from("<256I", page, OWNER_OFFSET)
    if any((count == 0) != (owner == 0) for count, owner in zip(counts, owners)):
        raise ValueError("allocation count/owner mismatch")
    runs = []
    start = 0
    for end in range(1, 257):
        if end == 256 or (counts[end], owners[end]) != (counts[start], owners[start]):
            runs.append(dict(first_block=start, end_block_exclusive=end,
                             start=f"0x{BASE + start * BLOCK:08x}",
                             end_exclusive=f"0x{BASE + end * BLOCK:08x}",
                             bytes=(end - start) * BLOCK, count=counts[start],
                             owner=f"0x{owners[start]:08x}"))
            start = end
    def free(pool_start, pool_end):
        return [r for r in runs if r["first_block"] >= pool_start and
                r["end_block_exclusive"] <= pool_end and r["count"] == 0]
    return dict(sha256=hashlib.sha256(page).hexdigest(), block_bytes=BLOCK,
                entries=256, runs=runs,
                lower_pool=dict(blocks=[152, 192], free_runs=free(152, 192)),
                upper_pool=dict(blocks=[192, 256], free_runs=free(192, 256)))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("page", type=Path)
    args = ap.parse_args()
    print(json.dumps(parse(args.page.read_bytes()), indent=2))


if __name__ == "__main__":
    main()

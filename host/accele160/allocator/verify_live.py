#!/usr/bin/env python3
"""Replay a completed exact allocator call without touching the card."""

import argparse
import hashlib
import json
from pathlib import Path
import struct

CANDIDATE_SHA = "0124657ded5618f1a00737d4917a500bccbbeea951e3f1e33cee6d84799dd5d0"
MODULE_SHA = "0a0d0e223ac2b2b092e5375ca4f81a08f0fb5eaab61e135ea079f15056a1d85e"
SESSION_SHA = "f8d842bcfcd043f1597aafe28ac8796630368226404cf85bbcc7aeb61c96d1d5"
NONCE = 0x16161031


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def verify(path: Path) -> dict:
    meta = json.loads((path / "preflight.json").read_text())
    result = json.loads((path / "result.json").read_text())
    if (meta["candidate_sha256"] != CANDIDATE_SHA or
            meta["module_sha256"] != MODULE_SHA or
            meta["session_sha256"] != SESSION_SHA or
            meta["old_card"]["driver"] is not None or
            meta["card"]["driver"] != "myrsread" or
            result["returncode"] != 0 or
            result["old_after"]["driver"] is not None or
            result["card_after"]["driver"] != "myrsread" or
            result["command"].get("done") != "1" or
            result["command"].get("status") != "0" or
            result["command"].get("residual") != "0" or
            result["command"].get("released") != "1"):
        raise ValueError("ownership, command, or binary identity failure")
    before = (path / "page-before.bin").read_bytes()
    after = (path / "page-after-call.bin").read_bytes()
    table_before = (path / "table-before.bin").read_bytes()
    table_after = (path / "table-after.bin").read_bytes()
    if any(len(blob) != 4096 for blob in (before, after, table_before, table_after)):
        raise ValueError("capture size")
    if before != b"\xff" * 4096 or \
            table_before[0x2a0:0xaa0] != table_after[0x2a0:0xaa0]:
        raise ValueError("page preimage or allocator count/owner restoration")
    changed = {i for i, (a, b) in enumerate(zip(before, after)) if a != b}
    if changed != set(range(0x820, 0x830)):
        raise ValueError("result escaped its fixed 16-byte slot")
    magic, nonce, pointer, size = struct.unpack_from("<4I", after, 0x820)
    if (magic, nonce, size) != (0x4f4c4c41, NONCE, 0x40000) or \
            pointer < 0xc0618000 or pointer >= 0xc0790000 or pointer & 0x7fff:
        raise ValueError("unexpected allocator result")
    block = (pointer - 0xc0000000) // 0x8000
    if block + size // 0x8000 > 242:
        raise ValueError("allocation extends into stock-owned blocks")
    for index in range(block, block + size // 0x8000):
        count = struct.unpack_from("<I", table_before, 0x2a0 + index * 4)[0]
        owner = struct.unpack_from("<I", table_before, 0x6a0 + index * 4)[0]
        if count or owner:
            raise ValueError("reported allocation was not free in preimage")
    return dict(pointer=f"0x{pointer:08x}", size=size,
                changed_bytes=len(changed),
                allocator_metadata_sha256=sha(table_before[0x2a0:0xaa0]),
                adjacent_table_page_changed_bytes=sum(
                    a != b for i, (a, b) in enumerate(zip(table_before, table_after))
                    if i < 0x2a0 or i >= 0xaa0),
                page_preimage_sha256=sha(before), image_sha256=CANDIDATE_SHA,
                allocator_table_restored=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("capture", type=Path)
    print(json.dumps(verify(p.parse_args().capture), indent=2))

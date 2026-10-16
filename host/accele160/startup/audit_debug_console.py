#!/usr/bin/env python3
"""Verify stock debug-console dispatch against flash and an optional RAM snapshot."""

import argparse
import hashlib
import json
from pathlib import Path
import struct

from analyze import analyze
from verify_full_dump import unpack


def word(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def audit(flash, live_table=None):
    boot = analyze(flash)
    if not boot["accepted_stock"]:
        raise ValueError("requires accepted 6.00-05 stock flash")
    region = next(r for r in boot["regions"] if r["selector"] == 2)
    start = boot["runtime"]["flash_zip_offset"]
    end = region["offset"] + region["size"] - 0xa0
    runtime, _ = unpack(flash[start:end])
    if hashlib.sha256(runtime).hexdigest() != boot["runtime"]["sha256"]:
        raise ValueError("expanded runtime digest changed")
    loader_info = boot["loader"]
    loader = flash[loader_info["flash_offset"]:loader_info["flash_offset"] + loader_info["size"]]
    # Exact loader branch and UART presence-probe instructions. Offsets are
    # relative to the verified 0xc000a000 copy destination.
    anchors = {
        0x37e8: "00302082070060e0",  # stob 1,0xe0600007
        0x37f0: "00308082060060e0",  # stob 0,0xe0600006
        0x37f8: "00302080070060e0",  # ldob 0xe0600007
        0x3800: "08200935",          # compare against 1
        0x3784: "54e2a592",          # real +0x254
        0x3790: "58e2ad92",          # real +0x258
        0x3794: "5ce2b592",          # real +0x25c
        0x37a0: "60e2a592",          # real +0x260
        0x37b8: "54e2a592",          # stub +0x254
        0x37c4: "58e2ad92",          # stub +0x258
        0x37c8: "5ce2b592",          # stub +0x25c
        0x37d4: "60e2a592",          # stub +0x260
        0x220: "7100808c0000000a",  # fixed 'q'; ret
        0x230: "7100808c0000000a",  # fixed 'q'; ret
        0x240: "0000000a",          # output no-op
    }
    for offset, hex_bytes in anchors.items():
        expected = bytes.fromhex(hex_bytes)
        if loader[offset:offset + len(expected)] != expected:
            raise ValueError(f"loader anchor changed at {offset:#x}")
    # Immediate operands in the loader are two words after each lda opcode.
    real = [word(loader, x) for x in (0x3778, 0x3780, 0x378c, 0x379c)]
    stub = [word(loader, x) for x in (0x37ac, 0x37b4, 0x37c0, 0x37d0)]
    if real != [0xc000a0c0, 0xc000a0f0, 0xc000a150, 0xc000a190]:
        raise ValueError("real console callbacks changed")
    if stub != [0xc000a210, 0xc000a220, 0xc000a230, 0xc000a240]:
        raise ValueError("stub console callbacks changed")
    if runtime[0x3694:0x369c] != bytes.fromhex("0034a58ccfffffff"):
        raise ValueError("menu index changed")
    cases = {"cache_invalidate_e": ("e", 0xc001386c),
             "code_manager_u": ("u", 0xc0013930)}
    for key, (char, target) in cases.items():
        index = ord(char) - ord("1")
        if word(runtime, 0x36ac + index * 4) != target:
            raise ValueError(f"{key} dispatch changed")
    if runtime[0x386c:0x3870] != bytes.fromhex("021ee065"):
        raise ValueError("cache invalidate changed")
    result = {
        "flash_sha256": boot["flash_sha256"],
        "runtime_sha256": boot["runtime"]["sha256"],
        "loader_sha256": hashlib.sha256(loader).hexdigest(),
        "uart_probe": "write 1 to e0600007, 0 to e0600006, read e0600007; real callbacks only if readback is 1",
        "real_callbacks": [f"0x{x:08x}" for x in real],
        "stub_callbacks": [f"0x{x:08x}" for x in stub],
        "stub_input_returns": "0x71 ('q')",
        "stub_output": "ret (no output)",
        "menu_cases": {key: {"character": char, "index": ord(char) - ord("1"),
                             "target": f"0x{target:08x}"}
                       for key, (char, target) in cases.items()},
        "safe_ssh_execution_route_proven": False,
    }
    if live_table is not None:
        if len(live_table) != 4096:
            raise ValueError("expected 4 KiB snapshot of local c048b000")
        observed = [word(live_table, 0x774 + x * 4) for x in range(4)]
        if observed != stub:
            raise ValueError("live callback table differs from stock stub branch")
        result["live_snapshot"] = {
            "local_page": "0xc048b000",
            "sha256": hashlib.sha256(live_table).hexdigest(),
            "callbacks": [f"0x{x:08x}" for x in observed],
            "matches_stub_branch": True,
        }
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("flash", type=Path)
    parser.add_argument("--live-table", type=Path, help="read-only 4 KiB local RAM snapshot at c048b000")
    args = parser.parse_args()
    print(json.dumps(audit(args.flash.read_bytes(),
                           args.live_table.read_bytes() if args.live_table else None), indent=2))

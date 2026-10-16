#!/usr/bin/env python3
"""Check the accepted stock image's cache-control anchors without card access."""

import argparse
import hashlib
import json
from pathlib import Path
import struct

from analyze import analyze
from verify_full_dump import unpack


DATA_INVALIDATE = bytes.fromhex("021ee065")
DATA_INVALIDATE_G0 = bytes.fromhex("021e8065")
EXPECTED_SITES = (0x386C, 0x1185C, 0x2A42C, 0x402F8, 0x40B74)


def audit(flash: bytes) -> dict:
    boot = analyze(flash)
    if not boot["accepted_stock"]:
        raise ValueError("this audit requires the accepted 6.00-05 stock dump")
    runtime_info = boot["runtime"]
    region = next(r for r in boot["regions"] if r["selector"] == 2)
    start = runtime_info["flash_zip_offset"]
    end = region["offset"] + region["size"] - 0xA0
    runtime, _ = unpack(flash[start:end])
    if hashlib.sha256(runtime).hexdigest() != runtime_info["sha256"]:
        raise ValueError("expanded firmware digest changed")
    for offset in EXPECTED_SITES:
        if runtime[offset:offset + 4] != DATA_INVALIDATE:
            raise ValueError(f"D-cache invalidate changed at {offset:#x}")
    if runtime[0x404B4:0x404B8] != DATA_INVALIDATE_G0:
        raise ValueError("memory-test D-cache invalidate changed")
    if runtime[0x40404:0x40408] != bytes.fromhex("90449465"):
        raise ValueError("startup sysctl instruction changed")
    if runtime[0x403F0:0x403F4] != bytes.fromhex("0003808c"):
        raise ValueError("startup sysctl input changed")
    # The dispatcher subtracts ASCII '1' (0x31), not ASCII '0'.
    # The cache case is 'e' (0x65); the old audit mislabeled it 'd'.
    if runtime[0x3694:0x369C] != bytes.fromhex("0034a58ccfffffff"):
        raise ValueError("debug-menu index instruction changed")
    menu_index = 0x65 - 0x31
    menu_entry = struct.unpack_from("<I", runtime, 0x36AC + menu_index * 4)[0]
    if menu_entry != 0xC001386C:
        raise ValueError("debug-menu cache case changed")
    return {
        "flash_sha256": boot["flash_sha256"],
        "runtime_sha256": runtime_info["sha256"],
        "debug_menu_case": {"input_code": "0x65", "input_character": "e",
                            "index_subtract": "0x31", "table_index": menu_index,
                            "table_entry": f"0x{menu_entry:08x}",
                            "instruction": "dcctl 2,0,g12"},
        "other_data_invalidate_offsets": [f"0x{x:x}" for x in EXPECTED_SITES[1:]]
                                         + ["0x404b4"],
        "startup_sysctl": {"file_offset": "0x40404", "g0": "0x300"},
        "execution_proven": False,
        "host_command_reaching_cache_invalidation_proven": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("flash", type=Path, help="accepted 1 MiB rawflash-0/data.bin")
    args = parser.parse_args()
    print(json.dumps(audit(args.flash.read_bytes()), indent=2))

#!/usr/bin/env python3
"""Check the stock AcceleRAID 160 boot recovery anchors, without card I/O."""

import argparse
import hashlib
import json
from pathlib import Path


STOCK_SHA256 = "0a951782a7ccd1855746ffeb3a1b64563287bc56e0dce77d63b79c71ec3b502a"
BASE = 0xFEF00000

# Exact instruction bytes from the accepted flash. Addresses are i960 local
# addresses; this is an identity/route audit, not a firmware emulator.
ANCHORS = {
    "uart_probe_call": (0xFEFFC090, "70060009"),
    "uart_scratch_write": (0xFEFFC708, "00302082"),
    "uart_scratch_read": (0xFEFFC718, "00302080"),
    "uart_present_flag": (0xFEFFC728, "34008092"),
    "serial_rx_ready": (0xFEFFC0D0, "2c600130"),
    "serial_s": (0xFEFFC0E4, "5300208c"),
    "serial_s_branch": (0xFEFFC0E8, "24402132"),
    "serial_bang_mode": (0xFEFFC0EC, "021e805c"),
    "flash_control_read": (0xFEFFC0FC, "00302080"),
    "flash_control_bit1": (0xFEFFC104, "08200930"),
    "recovery_dispatch": (0xFEFFC8D8, "80e1013d"),
    "recovery_init": (0xFEFFCA58, "980d0009"),
    "recovery_mode2": (0xFEFFCA60, "20e0113a"),
    "copy_20k_source": (0xFEFFC5EC, "0030208c0000fffe"),
    "copy_20k_target": (0xFEFFC5F4, "0030288c000001c0"),
    "copy_20k_count": (0xFEFFC5FC, "0030308c00500000"),
    "recovery_entry": (0xFEFFCA74, "0030808c700101c0"),
    "program_flash_control": (0xFEFF18A0, "00309882000050e0"),
}


def audit(data: bytes) -> dict:
    digest = hashlib.sha256(data).hexdigest()
    matches = {name: data[address - BASE:address - BASE + len(bytes.fromhex(expected))]
               == bytes.fromhex(expected)
               for name, (address, expected) in ANCHORS.items()}
    return {
        "size": len(data),
        "sha256": digest,
        "accepted_stock": len(data) == 0x100000 and digest == STOCK_SHA256,
        "anchors": matches,
        "all_anchors_match": all(matches.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("flash", type=Path)
    args = parser.parse_args()
    result = audit(args.flash.read_bytes())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["accepted_stock"] and result["all_anchors_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

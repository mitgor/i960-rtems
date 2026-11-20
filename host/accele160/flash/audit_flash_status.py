#!/usr/bin/env python3
"""Pin the stock 6.00-05 code behind 'FLASHIMAGE returned host status 2'.

Offline only: reads a full 1 MiB stock dump, never a card. Each anchor is the
exact instruction bytes at a runtime address; see
docs/hardware/ACCELE160-FLASH-STATUS-2-INVESTIGATION.md for what they show.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "host/accele160/readimage"))
from verify_full_dump import unpack  # noqa: E402

BASE = 0xC0010000
RUNTIME_SHA = "09e84895223627edeff8f1a6902d2a9a573c2c3e7769a5ea16caaa32cf07e3db"
FREE_STAGING = 0xC0051040
ANCHORS = {
    # Completion: any non-zero internal status becomes 2 (or 0x0e02 + sense).
    "completion_load_status": (0xC004E978, "5620b488"),
    "completion_test_no_autosense": (0xC004E9B4, "50203537"),
    "completion_status_with_sense": (0xC004E9FC, "020ee88c"),
    "completion_status_plain_2": (0xC004EA04, "021ee85c"),
    "completion_store_status": (0xC004EA08, "5620e98a"),
    # Sense builder: byte 12 = 0x80 | code >> 8, byte 13 = code & 0xff.
    "sense_code_high": (0xC006935C, "080ca159"),
    "sense_set_bit7": (0xC0069364, "8709a558"),
    "sense_store_asc": (0xC006936C, "0c60a582"),
    "sense_store_ascq": (0xC0069374, "0d602582"),
    # FLASHIMAGE method: pointer check, writer call, the two failure codes.
    "flash_load_staged_pointer": (0xC00509F0, "0030a090f04c49c0"),
    "flash_status_0x105": (0xC0050A04, "0501908c"),
    "flash_call_writer": (0xC0050A78, "98490009"),
    "flash_status_22": (0xC0050A80, "161e905c"),
    # READIMAGE frees staging only when it allocated the buffer itself.
    "read_free_only_state_1": (0xC0050900, "08a0093d"),
    # Writer: erase results are OR-ed, the loop never stops early.
    "writer_or_erase_result": (0xC0055470, "85032c58"),
    # Erase: unbounded status poll, then VPP bit 3 and bit 4 checks.
    "erase_poll_bit7": (0xC0055278, "072f045a"),
    "erase_poll_loop": (0xC0055280, "f0ffff10"),
    "erase_fail_vpp_bit3": (0xC0055294, "0c601930"),
    "erase_fail_bit4": (0xC00552AC, "ec7f2137"),
}


def branch_sites(runtime: bytes, target: int) -> list[int]:
    """Addresses of b/call/bal instructions whose target is `target`."""
    sites = []
    for offset in range(0, len(runtime) - 3, 4):
        word, = struct.unpack_from("<I", runtime, offset)
        if word >> 24 not in (0x08, 0x09, 0x0B):
            continue
        displacement = word & 0xFFFFFC
        if displacement & 0x800000:
            displacement -= 0x1000000
        if BASE + offset + displacement == target:
            sites.append(BASE + offset)
    return sites


def audit(flash: bytes) -> dict:
    if len(flash) != 0x100000:
        raise ValueError("need a full 1 MiB flash dump")
    runtime, _ = unpack(flash[0x47000:0xC0000])
    if hashlib.sha256(runtime).hexdigest() != RUNTIME_SHA:
        raise ValueError("stock runtime differs from the audited 6.00-05")
    for name, (address, hex_bytes) in ANCHORS.items():
        expected = bytes.fromhex(hex_bytes)
        if runtime[address - BASE:address - BASE + len(expected)] != expected:
            raise ValueError(f"anchor {name} differs")
    frees = branch_sites(runtime, FREE_STAGING)
    # READIMAGE (two exits), FLASHIMAGE, and the 'WrongFl' method: nothing
    # else releases a staged image between STOREIMAGE and FLASHIMAGE.
    if frees != [0xC00508AC, 0xC0050904, 0xC0050A88, 0xC0050DB4]:
        raise ValueError("unexpected caller of the staging free routine")
    # The staged pointer is cleared in exactly one place, inside that routine.
    if runtime.count(bytes.fromhex("0030f092f04c49c0")) != 1:
        raise ValueError("staged pointer is cleared somewhere else")
    blocks = [flash[i << 16:(i + 1) << 16] for i in range(16)]
    return {
        "flash_sha256": hashlib.sha256(flash).hexdigest(),
        "runtime_sha256": RUNTIME_SHA,
        "anchors_matched": len(ANCHORS),
        "staging_free_callers": [f"0x{a:08x}" for a in frees],
        # Bit 7 clear here means array data cannot end the erase status poll.
        "block_first_bytes": [f"0x{b[0]:02x}" for b in blocks],
        "blank_blocks": [i for i, b in enumerate(blocks) if b == b"\xff" * 0x10000],
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit_flash_status.py STOCK_IMAGE")
    print(json.dumps(audit(Path(sys.argv[1]).read_bytes()), indent=2))

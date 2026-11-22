#!/usr/bin/env python3
"""Build an OFFLINE stock-reset-block RTEMS ROM prototype; never access a card."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "host/accele160/startup"))
from analyze import analyze

STOCK_SHA = "0a951782a7ccd1855746ffeb3a1b64563287bc56e0dce77d63b79c71ec3b502a"
SPARE_STOCK_SHA = "fadd2b0f6ed9bb88d7c846edd235e5e222cbe3a990b694115c5fa66170e7a816"
SECOND_SPARE_STOCK_SHA = "0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943"
SLOT5_LIVE_STOCK_SHA = "1ee91ea1c172069dd0c98ec68fdf7ebae45e7477466f90b94e36e160f20f3f65"
OCTOBER_HANDLER_CARD_STOCK_SHA = "93faf91f553822665cd4125d90b1066370c4bca0da76af8336daf98bc2dae094"
ACCEPTED_STOCK = {STOCK_SHA, SPARE_STOCK_SHA, SECOND_SPARE_STOCK_SHA,
                  SLOT5_LIVE_STOCK_SHA, OCTOBER_HANDLER_CARD_STOCK_SHA}
FLASH_SIZE = 0x100000
FW = 0x40000
FW_END = 0xc0000
TRAILER = FW_END - 0xa0
LOADER = 0x41000
LOADER_LEN = 0x6000
PAYLOAD = 0x47000
PAYLOAD_END = TRAILER
RAM_DEST = 0xc0010000
STAGE2_ENTRY = 0xc000a000
MAGIC = 0x31544e52


def fnv32(data):
    value = 2166136261
    for byte in data:
        value = ((value ^ byte) * 16777619) & 0xffffffff
    return value


def checksum_words(data):
    if len(data) & 3:
        raise ValueError("word checksum needs aligned length")
    return sum(struct.unpack(f"<{len(data) // 4}I", data)) & 0xffffffff


def build(stock, stage2, kernel):
    stock_sha = hashlib.sha256(stock).hexdigest()
    if stock_sha not in ACCEPTED_STOCK:
        raise ValueError("input must be the accepted full stock flash")
    original = analyze(stock)
    if (len(stock) != FLASH_SIZE or original["loader"]["flash_offset"] != LOADER
            or original["loader"]["size"] != LOADER_LEN
            or original["runtime"]["flash_zip_offset"] != PAYLOAD
            or original["runtime"]["destination"] != RAM_DEST):
        raise ValueError("unexpected stock boot layout")
    if not stage2 or len(stage2) > LOADER_LEN or len(stage2) & 3:
        raise ValueError("stage-two loader size/alignment")
    if not kernel or len(kernel) & 3 or len(kernel) > 0x70000:
        raise ValueError("RTEMS payload size/alignment")
    if 16 + len(kernel) > PAYLOAD_END - PAYLOAD:
        raise ValueError("RTEMS payload exceeds firmware region")

    image = bytearray(stock)
    image[LOADER:LOADER + LOADER_LEN] = stage2.ljust(LOADER_LEN, b"\xff")
    header = struct.pack("<4I", MAGIC, len(kernel), fnv32(kernel), 0)
    image[PAYLOAD:PAYLOAD_END] = (header + kernel).ljust(PAYLOAD_END - PAYLOAD, b"\xff")
    struct.pack_into("<I", image, TRAILER + 4, STAGE2_ENTRY)
    struct.pack_into("<I", image, TRAILER + 8, RAM_DEST)
    struct.pack_into("<I", image, TRAILER + 24,
                     checksum_words(image[LOADER:LOADER + LOADER_LEN]))
    struct.pack_into("<I", image, TRAILER + 124,
                     checksum_words(image[TRAILER:TRAILER + 124]))

    candidate = bytes(image)
    verify(candidate, stock, stage2, kernel)
    receipt = {
        "stock_sha256": stock_sha,
        "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
        "stage2_sha256": hashlib.sha256(stage2).hexdigest(),
        "rtems_sha256": hashlib.sha256(kernel).hexdigest(),
        "stage2_size": len(stage2), "rtems_size": len(kernel),
        "stock_reset_block_unchanged": True,
        "stock_x86_option_rom_unchanged": True,
        "stock_diagnostics_and_descriptor_unchanged": True,
        "physical_boot_tested": False,
        "safe_to_flash": False,
    }
    return candidate, receipt


def verify(candidate, stock, stage2, kernel):
    if len(candidate) != FLASH_SIZE or candidate[:FW] != stock[:FW] or candidate[FW_END:] != stock[FW_END:]:
        raise ValueError("change outside main firmware")
    if candidate[LOADER:LOADER + len(stage2)] != stage2:
        raise ValueError("stage-two mismatch")
    magic, size, digest, reserved = struct.unpack_from("<4I", candidate, PAYLOAD)
    if (magic, size, digest, reserved) != (MAGIC, len(kernel), fnv32(kernel), 0):
        raise ValueError("payload header mismatch")
    if candidate[PAYLOAD + 16:PAYLOAD + 16 + size] != kernel:
        raise ValueError("RTEMS payload mismatch")
    words = struct.unpack_from("<40I", candidate, TRAILER)
    if (words[1], words[2], words[3], words[4], words[5], words[7], words[8]) != (
            STAGE2_ENTRY, RAM_DEST, LOADER_LEN, 0x1000, 0xc000a000, 0x7000, RAM_DEST):
        raise ValueError("boot trailer geometry")
    if words[6] != checksum_words(candidate[LOADER:LOADER + LOADER_LEN]):
        raise ValueError("loader checksum")
    if words[31] != checksum_words(candidate[TRAILER:TRAILER + 124]):
        raise ValueError("trailer checksum")
    if candidate[0xfff30:0xfff50] != stock[0xfff30:0xfff50]:
        raise ValueError("reset record changed")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("stock", type=Path)
    p.add_argument("stage2", type=Path)
    p.add_argument("rtems", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError(a.output)
    candidate, receipt = build(a.stock.read_bytes(), a.stage2.read_bytes(), a.rtems.read_bytes())
    a.output.write_bytes(candidate)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()

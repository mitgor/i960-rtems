#!/usr/bin/env python3
"""Upload a RAM1 payload through BAR0; no flash erase or programming."""
import argparse
import ctypes
import fcntl
import json
import mmap
import os
from pathlib import Path
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "rtems/transport"))
sys.path.insert(0, str(ROOT / "rtems/accele160/ram_loader"))
from card_select import select, require_unbound_or_absent  # noqa: E402
from manifest import CHUNK_BYTES, describe  # noqa: E402

TARGET = "0000:37:09.1"
PEER = "0000:37:04.1"
DEVICE = Path("/sys/bus/pci/devices") / TARGET
DEFAULT = 0xC0000000
CONTROL = 0xC0804000
DATA = 0xC0806000
MAGIC = 0x314D4152
VERSION = 1
SID1 = 0x31444953


def decode_flash_identification(words):
    if len(words) != 5 or words[0] != SID1:
        raise RuntimeError("RAM1 flash identification record absent")
    manufacturer, device, master, locks = words[1:]
    return {"manufacturer": f"0x{manufacturer:02x}",
            "device": f"0x{device:02x}",
            "master_lock": master, "block_lock_mask": f"0x{locks:04x}",
            "expected_s3_unlocked": (manufacturer, device, master, locks)
            == (0x89, 0xa6, 0, 0)}


class Ram1:
    def __init__(self):
        self.config = None
        self.resource = None
        self.bar = None
        self.mapping = None
        self.sequence = None

    def config_word(self):
        return struct.unpack("<I", os.pread(self.config, 4, 0x44))[0]

    def map_page(self, value):
        if self.config_word() != value:
            if os.pwrite(self.config, struct.pack("<I", value), 0x44) != 4:
                raise RuntimeError("short PIATVR write")
        if self.config_word() != value:
            raise RuntimeError("PIATVR did not read back")
        self.mapping = value

    def word(self, index):
        return ctypes.c_uint32.from_buffer(self.bar, 4096 + index * 4).value

    def write_word(self, index, value):
        ctypes.c_uint32.from_buffer(self.bar, 4096 + index * 4).value = value

    def __enter__(self):
        self.config = os.open(DEVICE / "config", os.O_RDWR)
        try:
            if os.pread(self.config, 4, 0) != bytes.fromhex("69105000"):
                raise RuntimeError("target PCI identity changed")
            if self.config_word() != DEFAULT:
                raise RuntimeError("unexpected PIATVR baseline")
            self.mapping = DEFAULT
            self.resource = os.open(DEVICE / "resource0", os.O_RDWR | os.O_SYNC)
            self.bar = mmap.mmap(self.resource, 8192, access=mmap.ACCESS_WRITE)
            self.map_page(CONTROL)
            if self.word(0) != MAGIC or self.word(10) != VERSION:
                raise RuntimeError("RAM1 service absent")
            if self.word(1) != self.word(2) or self.word(8) != 0 or self.word(9) != 0:
                raise RuntimeError("RAM1 session is not idle")
            self.sequence = self.word(2)
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, exc_type, exc, tb):
        try:
            if self.bar is not None:
                self.bar.close()
            if self.resource is not None:
                os.close(self.resource)
        finally:
            if self.config is not None:
                if self.mapping is not None:
                    self.map_page(DEFAULT)
                restored = self.config_word()
                identity = os.pread(self.config, 4, 0)
                os.close(self.config)
                if restored != DEFAULT or identity != bytes.fromhex("69105000"):
                    raise RuntimeError("PIATVR or PCI identity not restored")

    def command(self, opcode, index=0, length=0, digest=0, timeout=30):
        self.map_page(CONTROL)
        if self.sequence is None or self.sequence >= 0xFFFFFFFF:
            raise RuntimeError("RAM1 sequence exhausted")
        if self.word(1) != self.sequence or self.word(2) != self.sequence:
            raise RuntimeError("RAM1 prior command pending")
        for offset, value in ((3, opcode), (4, index), (5, length), (6, digest)):
            self.write_word(offset, value)
        self.write_word(1, self.sequence + 1)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.word(2) == self.sequence + 1:
                self.sequence += 1
                status = self.word(7)
                if status:
                    raise RuntimeError(f"RAM1 opcode {opcode} status {status}")
                return self.word(8), self.word(9)
            time.sleep(0.05)
        raise TimeoutError(f"RAM1 opcode {opcode} acknowledgement uncertain")

    def upload(self, image, manifest, run, identify_flash=False):
        self.map_page(CONTROL)
        digest = bytes.fromhex(manifest["sha256"])
        for pos in range(0, 32, 4):
            self.write_word((128 + pos) // 4,
                            struct.unpack_from("<I", digest, pos)[0])
        self.write_word(11, manifest["entry_offset"])
        if self.command(1, length=len(image), timeout=60) != (1, 0):
            raise RuntimeError("RAM1 BEGIN state mismatch")
        for index in range(len(image) // CHUNK_BYTES):
            page = image[index * CHUNK_BYTES:(index + 1) * CHUNK_BYTES]
            self.map_page(DATA)
            self.bar[4096:8192] = page
            if self.bar[4096:8192] != page:
                raise RuntimeError(f"RAM1 data page {index} readback mismatch")
            if self.command(2, index=index, length=CHUNK_BYTES,
                            digest=int(manifest["chunks_fnv32"][index], 16)) != (1, index + 1):
                raise RuntimeError(f"RAM1 chunk {index} state mismatch")
        if self.command(3, timeout=60) != (2, len(image) // CHUNK_BYTES):
            raise RuntimeError("RAM1 SEAL state mismatch")
        result = {"sealed": True, "executed": False}
        if run:
            if self.command(4, timeout=30)[0] != 3:
                raise RuntimeError("RAM1 RUN state mismatch")
            result["executed"] = True
            result["return_word"] = f"0x{self.word(12):08x}"
            if identify_flash:
                result["flash_identification"] = decode_flash_identification(
                    [self.word(index) for index in range(13, 18)])
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--identify-flash", action="store_true",
                        help="capture SID1 ID and lock record from the identification payload")
    args = parser.parse_args()
    if (args.receipt.exists() or (args.run and not args.live) or
            (args.identify_flash and not args.run)):
        raise ValueError("receipt exists, RUN requires --live, or ID requires RUN")
    image = args.image.read_bytes()
    manifest = json.loads(args.manifest.read_text())
    if manifest != describe(image, manifest["entry_offset"]):
        raise ValueError("image and manifest differ")
    receipt = {"image_sha256": manifest["sha256"],
               "mode": "offline-review", "flash_writes": 0}
    if args.live:
        with open("/run/lock/i960-loadrun.lock", "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            card = select(TARGET, "accele160")
            peer = require_unbound_or_absent(PEER, "accele160")
            if card["driver"] is not None or peer["present"]:
                raise RuntimeError("single unbound Slot 5 card required")
            if list(DEVICE.glob("host*/target*/*/block/*")):
                raise RuntimeError("card exposes storage")
            with Ram1() as transport:
                result = transport.upload(image, manifest, args.run,
                                          args.identify_flash)
            receipt.update(result)
            receipt["mode"] = "live-ram1"
            receipt["boot_id"] = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
            receipt["card"] = card
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(args.receipt)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Stage and seal a native update over BAR0; never erase or program flash.

The currently installed passive image has no UPD1 service, so this tool must
reject it before its first BAR write. This is for a future updater build.
"""
import argparse
import ctypes
import fcntl
import hashlib
import json
import mmap
import os
from pathlib import Path
import struct
import subprocess
import sys
import time

from prepare_native_update import CHUNK_BYTES, IMAGE_BYTES, fnv32, prepare

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "rtems/transport"))
from card_select import select, require_unbound_or_absent  # noqa: E402

TARGET = "0000:37:09.1"
PEER = "0000:37:04.1"
MAGIC = 0x31445055
CONTROL_PIATVR = "c0800000"
DATA_PIATVR = "c0802000"
DEFAULT_PIATVR = "c0000000"
BAR_PAGE = 0x1000


class NativeStage:
    def __init__(self, bdf: str, require_idle: bool = True):
        self.bdf = bdf
        self.require_idle = require_idle
        self.fd = None
        self.bar = None
        self.current = None
        self.sequence = None

    def pci(self, register: str, value: str | None = None) -> str:
        spec = register if value is None else register + "=" + value
        return subprocess.check_output(["setpci", "-s", self.bdf, spec], text=True).strip().lower()

    def __enter__(self):
        initial = self.pci("44.l")
        allowed = (DEFAULT_PIATVR,) if self.require_idle else (
            DEFAULT_PIATVR, CONTROL_PIATVR, DATA_PIATVR)
        if initial not in allowed or self.pci("00.w") != "1069" or self.pci("02.w") != "0050":
            raise RuntimeError("unexpected card or PIATVR baseline")
        # Recovery may inherit a UPD1 mapping from a killed stage process.
        # Restore the normal mapping on every exit, including rejection.
        self.current = DEFAULT_PIATVR
        try:
            self.fd = os.open(f"/sys/bus/pci/devices/{self.bdf}/resource0", os.O_RDWR | os.O_SYNC)
            self.bar = mmap.mmap(self.fd, 8192, access=mmap.ACCESS_WRITE)
            self.map_page(CONTROL_PIATVR)
            if self.read_word(0) != MAGIC or self.read_word(10) != 2:
                raise RuntimeError("UPD1 service absent; no BAR writes made")
            sequence, acknowledged = self.read_word(1), self.read_word(2)
            if sequence != acknowledged:
                raise RuntimeError("UPD1 command is pending or its result is uncertain")
            if self.require_idle and (self.read_word(8), self.read_word(9)) != (0, 0):
                raise RuntimeError("UPD1 session is not idle; abort it explicitly")
            self.sequence = acknowledged
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, exc_type, exc, tb):
        try:
            if self.bar is not None:
                self.bar.close()
            if self.fd is not None:
                os.close(self.fd)
        finally:
            if self.current is not None and self.pci("44.l") != self.current:
                self.pci("44.l", self.current)
            if self.current is not None and self.pci("44.l") != self.current:
                raise RuntimeError("PIATVR restoration failed")

    def map_page(self, value: str):
        if self.pci("44.l") != value:
            self.pci("44.l", value)
        if self.pci("44.l") != value:
            raise RuntimeError("PIATVR remap failed")

    def read_word(self, index: int) -> int:
        return ctypes.c_uint32.from_buffer(self.bar, BAR_PAGE + index * 4).value

    def write_word(self, index: int, value: int):
        ctypes.c_uint32.from_buffer(self.bar, BAR_PAGE + index * 4).value = value

    def command(self, seq: int, cmd: int, index: int = 0,
                length: int = 0, digest: int = 0, timeout: float = 30.0):
        if self.sequence is None or self.sequence >= 0xffffffff or seq != self.sequence + 1:
            raise RuntimeError("UPD1 command sequence is invalid or exhausted")
        self.map_page(CONTROL_PIATVR)
        if self.read_word(1) != self.sequence or self.read_word(2) != self.sequence:
            raise RuntimeError("UPD1 command is pending or its result is uncertain")
        self.write_word(3, cmd)
        self.write_word(4, index)
        self.write_word(5, length)
        self.write_word(6, digest)
        self.write_word(1, seq)  # publish command last
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.read_word(2) == seq:
                self.sequence = seq
                result = self.read_word(7)
                if result:
                    if cmd == 5:
                        writer = self.read_word(12)
                        status = self.read_word(13)
                        offset = self.read_word(14)
                        raise RuntimeError(
                            f"UPD1 APPLY returned {result}; writer={writer}, "
                            f"S3 status=0x{status:02x}, flash offset=0x{offset:05x}")
                    raise RuntimeError(f"UPD1 command {cmd} at chunk {index} returned {result}")
                return self.read_word(8), self.read_word(9)
            time.sleep(0.05)
        raise TimeoutError(f"UPD1 command {cmd} at chunk {index} timed out")

    def abort(self):
        self.map_page(CONTROL_PIATVR)
        if self.read_word(1) != self.sequence or self.read_word(2) != self.sequence:
            raise RuntimeError("UPD1 command is pending or its result is uncertain")
        if self.read_word(8) == 4:
            raise RuntimeError("UPD1 reports a partial flash write; abort refused")
        state, next_chunk = self.command(self.sequence + 1, 4)
        if (state, next_chunk) != (0, 0):
            raise RuntimeError("UPD1 abort returned an unexpected state")
        return state, next_chunk

    def apply(self, manifest: dict):
        """Request the separately qualified writer after exact sealed-image checks.

        A caller must independently qualify the physical backend and pin the
        boot/card before calling this method. A timeout leaves the outcome
        uncertain; it must never be retried in the same boot.
        """
        self.map_page(CONTROL_PIATVR)
        if self.read_word(11) & 1 != 1:
            raise RuntimeError("UPD1 has no linked flash writer")
        if (self.read_word(8), self.read_word(9)) != (2, 256):
            raise RuntimeError("UPD1 target is not sealed")
        if self.read_word(1) != self.sequence or self.read_word(2) != self.sequence:
            raise RuntimeError("UPD1 command is pending or uncertain")
        for start, key in ((128, "base_sha256"), (160, "target_sha256")):
            got = b"".join(struct.pack("<I", self.read_word((start + pos) // 4))
                           for pos in range(0, 32, 4))
            if got.hex() != manifest[key]:
                raise RuntimeError(f"UPD1 {key} differs from reviewed manifest")
        state, next_chunk = self.command(self.sequence + 1, 5, timeout=900)
        if (state, next_chunk) != (3, 256):
            raise RuntimeError("UPD1 apply returned an unexpected state")
        return state, next_chunk

    def stage(self, target: bytes, manifest: dict):
        if len(target) != IMAGE_BYTES or hashlib.sha256(target).hexdigest() != manifest["target_sha256"]:
            raise RuntimeError("target differs from reviewed manifest")
        self.map_page(CONTROL_PIATVR)
        for start, digest in ((128, manifest["base_sha256"]),
                              (160, manifest["target_sha256"])):
            raw = bytes.fromhex(digest)
            for pos in range(0, 32, 4):
                self.write_word((start + pos) // 4, struct.unpack_from("<I", raw, pos)[0])
        state, next_chunk = self.command(self.sequence + 1, 1, timeout=60)
        if (state, next_chunk) != (1, 0):
            raise RuntimeError("unexpected UPD1 begin state")
        for index in range(IMAGE_BYTES // CHUNK_BYTES):
            chunk = target[index * CHUNK_BYTES:(index + 1) * CHUNK_BYTES]
            digest = fnv32(chunk)
            if f"0x{digest:08x}" != manifest["chunks_fnv32"][index]:
                raise RuntimeError("manifest chunk digest mismatch")
            self.map_page(DATA_PIATVR)
            for pos in range(0, CHUNK_BYTES, 4):
                self.write_word(pos // 4, struct.unpack_from("<I", chunk, pos)[0])
            uploaded = bytearray(CHUNK_BYTES)
            for pos in range(0, CHUNK_BYTES, 4):
                struct.pack_into("<I", uploaded, pos, self.read_word(pos // 4))
            if uploaded != chunk:
                first = next(i for i, (a, b) in enumerate(zip(uploaded, chunk)) if a != b)
                raise RuntimeError(f"BAR data page differs at chunk {index} byte {first}: "
                                   f"read={uploaded[:16].hex()} expected={chunk[:16].hex()}")
            state, next_chunk = self.command(self.sequence + 1, 2, index, CHUNK_BYTES, digest)
            if (state, next_chunk) != (1, index + 1):
                raise RuntimeError("unexpected UPD1 chunk state")
        state, next_chunk = self.command(self.sequence + 1, 3, timeout=90)
        if (state, next_chunk) != (2, 256):
            raise RuntimeError("unexpected UPD1 seal state")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--live", action="store_true", help="perform RAM staging on a UPD1 card")
    args = parser.parse_args()
    if args.receipt.exists():
        raise FileExistsError(args.receipt)
    base, target = args.base.read_bytes(), args.target.read_bytes()
    expected = prepare(base, target)
    manifest = json.loads(args.manifest.read_text())
    if manifest != expected:
        raise RuntimeError("manifest does not match base and target bytes")
    receipt = {"target_sha256": expected["target_sha256"],
               "base_sha256": expected["base_sha256"], "mode": "offline-review",
               "flash_programmed": False}
    if args.live:
        lock = open("/run/lock/i960-loadrun.lock", "w")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        card = select(TARGET, "accele160")
        peer = require_unbound_or_absent(PEER, "accele160")
        if card["driver"] is not None or peer["present"]:
            raise RuntimeError("single unbound Slot 5 card required")
        with NativeStage(TARGET) as stage:
            stage.stage(target, manifest)
        receipt["mode"] = "live-ram-staged-and-sealed"
        receipt["boot_id"] = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        receipt["card"] = card
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(args.receipt)


if __name__ == "__main__":
    main()

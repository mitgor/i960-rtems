#!/usr/bin/env python3
"""Verify the shared x86 option ROM executes under QEMU/SeaBIOS.

This deliberately uses QEMU's generic -option-rom loader. It does not model
the RAID card's PCI configuration, BAR, mailbox, or i960 behavior.
"""
import argparse
import hashlib
import re
import struct
import subprocess
import tempfile
from pathlib import Path

ROM_OFFSET = 0x30000
ROM_SIZE = 0x7000


def extract(image: Path) -> bytes:
    flash = image.read_bytes()
    if len(flash) != 0x100000:
        raise ValueError(f"{image}: expected 1 MiB flash")
    rom = flash[ROM_OFFSET:ROM_OFFSET + ROM_SIZE]
    if rom[:2] != b"\x55\xaa" or rom[2] * 512 != len(rom) or sum(rom) & 255:
        raise ValueError(f"{image}: invalid x86 option ROM header/checksum")
    pcir = struct.unpack_from("<H", rom, 0x18)[0]
    if rom[pcir:pcir + 4] != b"PCIR":
        raise ValueError(f"{image}: missing PCIR header")
    vendor, device = struct.unpack_from("<HH", rom, pcir + 4)
    if (vendor, device) != (0x1069, 0x0050):
        raise ValueError(f"{image}: unexpected PCI identity")
    return rom


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stock", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--qemu", default="qemu-system-x86_64")
    args = parser.parse_args()
    stock = extract(args.stock)
    candidate = extract(args.candidate)
    if stock != candidate:
        raise ValueError("stock and candidate x86 option ROMs differ")
    with tempfile.TemporaryDirectory(prefix="accele160-rom-qemu-") as tmp:
        rom_path = Path(tmp) / "accele160.rom"
        trace_path = Path(tmp) / "qemu.log"
        rom_path.write_bytes(stock)
        command = [args.qemu, "-machine", "pc,accel=tcg", "-m", "64",
                   "-display", "none", "-serial", "none", "-monitor", "none",
                   "-no-reboot", "-option-rom", str(rom_path),
                   "-d", "in_asm,guest_errors", "-D", str(trace_path)]
        try:
            subprocess.run(command, stdout=subprocess.DEVNULL,
                           stderr=subprocess.PIPE, timeout=6, check=False)
        except subprocess.TimeoutExpired:
            pass  # SeaBIOS has no boot disk; execution is bounded by design.
        trace = trace_path.read_text(errors="replace") if trace_path.exists() else ""
        executed = bool(re.search(r"0x0*c0003:\s", trace, re.IGNORECASE))
    print(f"option_rom_sha256={hashlib.sha256(stock).hexdigest()}")
    print(f"option_rom_bytes={len(stock)} pcir=1069:0050 checksum=pass")
    print(f"qemu_entry_executed={int(executed)}")
    if not executed:
        raise RuntimeError("QEMU did not execute the option ROM entry")


if __name__ == "__main__":
    main()

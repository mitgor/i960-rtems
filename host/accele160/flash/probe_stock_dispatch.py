#!/usr/bin/env python3
"""Read the stock 0x8f dispatch word through BAR0; restore PIATVR on exit."""

import fcntl
import hashlib
import json
import mmap
import os
from pathlib import Path
import struct

BDF = "0000:37:09.1"
DEVICE = Path("/sys/bus/pci/devices") / BDF
PEER = Path("/sys/bus/pci/devices/0000:37:04.1")
BASELINE = 0xC0000000
TABLE_PAGE = 0xC0023000
TABLE_WORD_OFFSET = 0x4FC
STOCK_8F = 0xC0023790
LOADER_PAGE = 0xC000F000
CAVE_PAGE = 0xC000E000


def read32(fd, offset):
    return struct.unpack("<I", os.pread(fd, 4, offset))[0]


def main():
    if os.geteuid() != 0:
        raise PermissionError("root required")
    with open("/run/lock/i960-loadrun.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if ((DEVICE / "vendor").read_text().strip() != "0x1069" or
                (DEVICE / "device").read_text().strip() != "0x0050" or
                (DEVICE / "subsystem_vendor").read_text().strip() != "0x1069" or
                (DEVICE / "subsystem_device").read_text().strip() != "0x0054" or
                not (DEVICE / "driver").resolve().name == "myrsread" or
                PEER.exists() or
                list(DEVICE.glob("host*/target*/*/block/*"))):
            raise RuntimeError("single stock card preflight failed")
        host, = DEVICE.glob("host*/scsi_host/host*")
        if (host / "stock_descriptor").read_text().strip() != "state=0 status=0 residual=0":
            raise RuntimeError("stock descriptor not idle")
        cfg = os.open(DEVICE / "config", os.O_RDWR)
        barfd = None
        bar = None
        remapped = False
        try:
            if os.pread(cfg, 4, 0) != bytes.fromhex("69105000") or read32(cfg, 0x44) != BASELINE:
                raise RuntimeError("PCI identity or PIATVR baseline differs")
            barfd = os.open(DEVICE / "resource0", os.O_RDWR | os.O_SYNC)
            bar = mmap.mmap(barfd, 8192, access=mmap.ACCESS_WRITE)
            default_before = bytes(bar[4096:8192])
            if os.pwrite(cfg, struct.pack("<I", TABLE_PAGE), 0x44) != 4:
                raise RuntimeError("PIATVR remap was short")
            remapped = True
            if read32(cfg, 0x44) != TABLE_PAGE:
                raise RuntimeError("PIATVR remap did not read back")
            table = bytes(bar[4096:8192])
            word = struct.unpack_from("<I", table, TABLE_WORD_OFFSET)[0]
            if os.pwrite(cfg, struct.pack("<I", CAVE_PAGE), 0x44) != 4:
                raise RuntimeError("cave PIATVR remap was short")
            if read32(cfg, 0x44) != CAVE_PAGE:
                raise RuntimeError("cave PIATVR remap did not read back")
            cave_window = bytes(bar[4096:8192])
            if os.pwrite(cfg, struct.pack("<I", LOADER_PAGE), 0x44) != 4:
                raise RuntimeError("loader PIATVR remap was short")
            if read32(cfg, 0x44) != LOADER_PAGE:
                raise RuntimeError("loader PIATVR remap did not read back")
            loader = bytes(bar[4096:8192])
            result = {
                "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
                "bdf": BDF,
                "table_word": f"0x{word:08x}",
                "stock_unsupported_expected": word == STOCK_8F,
                "table_page_sha256": hashlib.sha256(table).hexdigest(),
                "loader_page_sha256": hashlib.sha256(loader).hexdigest(),
                "loader_page_all_ff": loader == b"\xff" * 4096,
                "even_window_aliases_loader": cave_window == loader,
                "even_handler_page_host_visible": False,
                "flash_commands": 0,
                "ram_payload_executed": False,
            }
        finally:
            if remapped:
                os.pwrite(cfg, struct.pack("<I", BASELINE), 0x44)
                if read32(cfg, 0x44) != BASELINE:
                    raise RuntimeError("PIATVR restore failed")
            if bar is not None:
                default_after = bytes(bar[4096:8192])
                bar.close()
            if barfd is not None:
                os.close(barfd)
            os.close(cfg)
        if default_before != default_after:
            raise RuntimeError("default BAR page changed")
        result["default_page_restored"] = True
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

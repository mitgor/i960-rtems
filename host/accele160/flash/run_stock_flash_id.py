#!/usr/bin/env python3
"""One-shot stock-RAM Intel ID/lock diagnostic after a separate cold boot."""

import argparse
import fcntl
import hashlib
import json
import mmap
import os
from pathlib import Path
import struct
import subprocess
import time

BDF = "0000:37:09.1"
DEV = Path("/sys/bus/pci/devices") / BDF
PEER = Path("/sys/bus/pci/devices/0000:37:04.1")
DEBUG = Path("/sys/kernel/debug/accele-pingprobe")
BASE = 0xC0000000
TABLE = 0xC0023000
CODE = 0xC000F000
STOCK = 0xC0023790
ENTRY = 0xC000F900
MAGIC = 0x31444953
STOCK_SHA = "0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943"
PAYLOAD_SHA = "f2d1352e01e7d69f9277623bb8d89047970df27312330121cb4b9b89f4809623"
MODULE_SHA = "e0c72c756efd6222bbcd6a74d21b1fe14b6621225c84670eb3534bc42df1cef1"
PREVIOUS_PROBE_BOOT = "9f2952ee-924f-4d27-af7e-83598ae24ba5"
USED = Path("/run/i960-stock-8f-called")  # tmpfs: one 0x8f call per boot


def sha(data):
    return hashlib.sha256(data).hexdigest()


def need(value, message):
    if not value:
        raise RuntimeError(message)


def fields(path):
    return dict(piece.split("=", 1) for piece in path.read_text().split())


def read32(fd, offset):
    return struct.unpack("<I", os.pread(fd, 4, offset))[0]


def check_read(path, boot):
    request = json.loads((path / "request.json").read_text())
    result = json.loads((path / "result.json").read_text())
    status = fields(path / "status.txt")
    need(request["boot_id"] == boot and request["selector"] == 9 and
         request["length"] == 1048576 and result["sha256"] == STOCK_SHA and
         sha((path / "data.bin").read_bytes()) == STOCK_SHA and
         all(status.get(k) == "0" for k in ("status", "residual", "guard_changes")),
         "same-boot stock read is incomplete")


def decode_flash_id(words):
    identification = dict(zip(("magic", "manufacturer", "device",
        "master_lock", "all_block_locks", "array_byte",
        "return_code", "gate_before", "gate_after"), words))
    qualified = (words[:7] == (MAGIC, 0x89, 0xA6, 0, 0, 0x50, 0)
                 and words[7] == words[8])
    return {"identification": identification,
            "expected_id_and_locks": qualified}, qualified


def main(payload_sha=PAYLOAD_SHA, timeout=5, decode=decode_flash_id,
         description=__doc__):
    parser = argparse.ArgumentParser(description=description)
    for name in ("module", "payload", "read0", "read1", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--cold-power-cycle-observed", action="store_true")
    args = parser.parse_args()
    need(os.geteuid() == 0, "root required")
    with open("/run/lock/i960-loadrun.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        need(args.cold_power_cycle_observed and boot != PREVIOUS_PROBE_BOOT,
             "cold power cycle required after the first flash-ID probe")
        check_read(args.read0, boot)
        check_read(args.read1, boot)
        need(args.read0 != args.read1, "reads must be independent")
        marker = args.payload.read_bytes()
        need(sha(marker) == payload_sha and len(marker) <= 0x600,
             "wrong pinned RAM payload")
        need(not USED.exists(),
             "0x8f already called on this boot; cold power cycle first")
        need(sha(args.module.read_bytes()) == MODULE_SHA and
             args.module.name == "ping_probe.ko", "wrong command module")
        need(not PEER.exists() and
             (DEV / "driver").resolve().name == "myrsread" and
             not list(DEV.glob("host*/target*/*/block/*")) and
             not DEBUG.exists() and not Path("/sys/module/ping_probe").exists(),
             "card or command module preflight failed")
        host, = DEV.glob("host*/scsi_host/host*")
        need((host / "stock_descriptor").read_text().strip() ==
             "state=0 status=0 residual=0", "descriptor not idle")
        need(not args.out.exists(), "output exists")
        args.out.mkdir(parents=True)
        (args.out / "preflight.json").write_text(json.dumps({
            "boot_id": boot, "bdf": BDF, "stock_sha256": STOCK_SHA,
            "flash_id_payload_sha256": payload_sha, "module_sha256": MODULE_SHA,
            "flash_program_erase_commands": 0,
        }, indent=2) + "\n")

        cfg = os.open(DEV / "config", os.O_RDWR)
        resource = os.open(DEV / "resource0", os.O_RDWR | os.O_SYNC)
        bar = mmap.mmap(resource, 8192, access=mmap.ACCESS_WRITE)
        command_started = False
        command_completed = False
        table_written = False
        code_written = False
        module_loaded = False
        def map_page(page):
            need(os.pwrite(cfg, struct.pack("<I", page), 0x44) == 4 and
                 read32(cfg, 0x44) == page, "PIATVR remap failed")
        def page_bytes():
            return bytes(bar[4096:8192])
        def put(offset, data):
            bar[4096 + offset:4096 + offset + len(data)] = data
            need(bytes(bar[4096 + offset:4096 + offset + len(data)]) == data,
                 "RAM MMIO write/readback failed")
        try:
            need(os.pread(cfg, 4, 0) == bytes.fromhex("69105000") and
                 read32(cfg, 0x44) == BASE, "PCI identity or PIATVR changed")
            baseline = page_bytes()
            map_page(TABLE)
            table_before = page_bytes()
            need(struct.unpack_from("<I", table_before, 0x4FC)[0] == STOCK,
                 "stock dispatch pointer changed")
            map_page(CODE)
            code_before = page_bytes()
            need(code_before == b"\xff" * 4096,
                 "loader page is not blank; no RAM patch")
            (args.out / "table-before.bin").write_bytes(table_before)
            (args.out / "loader-before.bin").write_bytes(code_before)

            code_written = True
            put(0x900, marker)
            map_page(TABLE)
            table_written = True
            put(0x4FC, struct.pack("<I", ENTRY))
            map_page(BASE)
            need(page_bytes() == baseline, "default BAR page drift")
            subprocess.run(["insmod", str(args.module), "bdf=" + BDF], check=True)
            module_loaded = True
            need(fields(DEBUG / "status").get("started") == "0",
                 "command module already started")
            USED.touch()
            started_at = time.monotonic()
            (DEBUG / "start").write_text("ping\n")
            command_started = True
            deadline = started_at + timeout
            while time.monotonic() < deadline:
                status = fields(DEBUG / "status")
                if status.get("done") == "1":
                    command_completed = True
                    seconds = round(time.monotonic() - started_at, 2)
                    break
                time.sleep(0.02)
            (args.out / "status.txt").write_text((DEBUG / "status").read_text())
            need(command_completed, "command uncertain; RAM hook retained for cold reset")
            map_page(CODE)
            code_after = page_bytes()
            (args.out / "loader-after-call.bin").write_bytes(code_after)
            record, qualified = decode(
                struct.unpack_from("<9I", code_after, 0x834))
            (args.out / "result.json").write_text(json.dumps({
                "boot_id": boot, "status": status, **record,
                "command_seconds": seconds,
                "flash_program_erase_commands": 0,
            }, indent=2) + "\n")
        finally:
            # A pending command may still execute the RAM stub. Leave both
            # its code and pointer intact; cold reset is the recovery path.
            if not command_started or command_completed:
                if table_written:
                    map_page(TABLE)
                    put(0x4FC, table_before[0x4FC:0x500])
                    need(page_bytes() == table_before, "dispatch table restore drift")
                if code_written:
                    map_page(CODE)
                    put(0x900, code_before[0x900:0x900 + len(marker)])
                    if command_completed:
                        put(0x800, code_before[0x800:0x858])
                    need(page_bytes() == code_before, "loader page restore drift")
            map_page(BASE)
            need(page_bytes() == baseline, "default BAR page not restored")
            bar.close()
            os.close(resource)
            os.close(cfg)
            if module_loaded and command_completed:
                (DEBUG / "release").write_text("release\n")
                subprocess.run(["rmmod", "ping_probe"], check=True)
            elif module_loaded and not command_started:
                subprocess.run(["rmmod", "ping_probe"], check=True)
        need(status["status"] == "2" and status["residual"] == "0" and
             qualified, "RAM diagnostic or stock fallback differed")


if __name__ == "__main__":
    main()

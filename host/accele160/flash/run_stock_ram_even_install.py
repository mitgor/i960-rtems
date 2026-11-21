#!/usr/bin/env python3
"""Install and ping the proven AcceleRAID handler in volatile card RAM only.

The host BAR can access c000f000, but not the preceding even page. A tiny
i960 stub copies the first 3624 handler bytes to that page. The second stub
call checks the full handler and changes the dispatch pointer from the card.
The installed handler stays resident until a cold reset; no flash command is
issued. On uncertain completion leave RAM and module pinned until reset.
"""
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
BASE, TABLE, LOADER = 0xC0000000, 0xC0023000, 0xC000E000
STUB_ENTRY, HANDLER_ENTRY, STOCK_ENTRY = 0xC000FE40, 0xC000E1EC, 0xC0023790
FIRST, SECOND = 0xE28, 0x2BC
STOCK_SHA = "0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943"
HANDLER_SHA = "8d8c79c3b8c206608ef7221000991c0d75eb101ce06581fedc2a74522648ad34"
STUB_SHA = "b53589120254d24f1a4e69b1cbe1acb7813f2e8acc031a952221c9f6e521eedd"
MODULE_SHA = "e0c72c756efd6222bbcd6a74d21b1fe14b6621225c84670eb3534bc42df1cef1"


def need(ok, why):
    if not ok:
        raise RuntimeError(why)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fields(path):
    return dict(part.split("=", 1) for part in path.read_text().split())


def check_read(path, boot):
    request = json.loads((path / "request.json").read_text())
    result = json.loads((path / "result.json").read_text())
    status = fields(path / "status.txt")
    data = (path / "data.bin").read_bytes()
    need(request["boot_id"] == boot and request["selector"] == 9 and
         request["length"] == len(data) == 1048576 and
         result["sha256"] == sha(data) == STOCK_SHA and
         all(status.get(x) == "0" for x in ("status", "residual", "guard_changes")),
         f"same-boot stock read incomplete: {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("handler", "stub", "module", "read0", "read1", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    a = parser.parse_args()
    need(os.geteuid() == 0, "root required")
    with open("/run/lock/i960-loadrun.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        need(a.read0 != a.read1, "reads must be independent")
        check_read(a.read0, boot)
        check_read(a.read1, boot)
        handler, stub = a.handler.read_bytes(), a.stub.read_bytes()
        need(len(handler) == FIRST + SECOND == 4324 and
             sha(handler) == HANDLER_SHA, "reviewed handler mismatch")
        need(len(stub) <= 0x1C0 and sha(stub) == STUB_SHA,
             "copy stub mismatch")
        need(a.module.name == "ping_probe.ko" and
             sha(a.module.read_bytes()) == MODULE_SHA, "ping module mismatch")
        need(not PEER.exists() and
             (DEV / "driver").resolve().name == "myrsread" and
             not list(DEV.glob("host*/target*/*/block/*")) and
             not DEBUG.exists() and not Path("/sys/module/ping_probe").exists(),
             "single stock card/module preflight failed")
        host, = DEV.glob("host*/scsi_host/host*")
        need((host / "stock_descriptor").read_text().strip() ==
             "state=0 status=0 residual=0", "descriptor not idle")
        need(not a.out.exists(), "output directory exists")
        a.out.mkdir(parents=True)
        (a.out / "preflight.json").write_text(json.dumps({
            "boot_id": boot, "bdf": BDF, "stock_sha256": STOCK_SHA,
            "handler_sha256": HANDLER_SHA, "stub_sha256": STUB_SHA,
            "module_sha256": MODULE_SHA, "flash_commands": 0,
        }, indent=2) + "\n")

        cfg = os.open(DEV / "config", os.O_RDWR)
        resource = os.open(DEV / "resource0", os.O_RDWR | os.O_SYNC)
        bar = mmap.mmap(resource, 8192, access=mmap.ACCESS_WRITE)
        command_started = False
        command_completed = False
        command_ever_started = False
        stage = "preflight"
        default_before = None
        modified = False

        def map_page(value):
            packed = struct.pack("<I", value)
            need(os.pwrite(cfg, packed, 0x44) == 4 and
                 os.pread(cfg, 4, 0x44) == packed,
                 "PIATVR mapping/readback failed")

        def page():
            return bytes(bar[4096:8192])

        def put(offset, data):
            bar[4096 + offset:4096 + offset + len(data)] = data
            need(bytes(bar[4096 + offset:4096 + offset + len(data)]) == data,
                 "RAM MMIO write/readback failed")

        def word(offset):
            return struct.unpack_from("<I", bar, 4096 + offset)[0]

        def ping(label, expected_status):
            nonlocal command_started, command_completed, command_ever_started
            need(not DEBUG.exists(), "previous command module retained")
            subprocess.run(["insmod", str(a.module), "bdf=" + BDF], check=True)
            need(fields(DEBUG / "status").get("started") == "0",
                 "ping module already started")
            (DEBUG / "start").write_text("ping\n")
            command_started = True
            command_ever_started = True
            command_completed = False
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                status = fields(DEBUG / "status")
                if status.get("done") == "1":
                    command_completed = True
                    break
                time.sleep(0.02)
            (a.out / f"{label}-status.txt").write_text((DEBUG / "status").read_text())
            need(command_completed, f"{label} uncertain; leave module and RAM for reset")
            need(status.get("status") == str(expected_status) and
                 status.get("residual") == "0", f"{label} status differed")
            (DEBUG / "release").write_text("release\n")
            subprocess.run(["rmmod", "ping_probe"], check=True)
            command_started = False
            return status

        try:
            need(os.pread(cfg, 4, 0) == bytes.fromhex("69105000") and
                 os.pread(cfg, 4, 0x44) == struct.pack("<I", BASE),
                 "PCI identity or PIATVR baseline changed")
            default_before = page()
            map_page(TABLE)
            table_before = page()
            need(struct.unpack_from("<I", table_before, 0x4FC)[0] == STOCK_ENTRY,
                 "stock dispatch entry changed")
            map_page(LOADER)
            loader_before = page()
            need(loader_before == b"\xff" * 4096,
                 "host-visible loader page not blank")
            (a.out / "table-before.bin").write_bytes(table_before)
            (a.out / "loader-before.bin").write_bytes(loader_before)

            # c000e000 itself is not host-visible. The first-stage code
            # compares every copied word from the i960 side before reporting.
            modified = True
            put(0, handler[:FIRST])
            put(0xE40, stub)
            need(page()[:FIRST] == handler[:FIRST] and
                 page()[0xE40:0xE40 + len(stub)] == stub,
                 "staging page changed")
            map_page(TABLE)
            put(0x4FC, struct.pack("<I", STUB_ENTRY))
            stage = "first-staged"
            map_page(BASE)
            need(page() == default_before, "default BAR page changed")
            ping("copy-even", 2)
            stage = "first-complete"
            map_page(LOADER)
            need(word(0xE30) == 0x31435059 and word(0xE38) == 0,
                 "i960 copy/compare report failed")
            (a.out / "after-copy-page.bin").write_bytes(page())
            map_page(TABLE)
            need(word(0x4FC) == STUB_ENTRY, "first phase changed dispatch")

            map_page(LOADER)
            put(0, b"\xff" * FIRST)
            put(0, handler[FIRST:])
            put(0xE34, struct.pack("<I", 2))
            need(page()[:SECOND] == handler[FIRST:] and
                 page()[SECOND:FIRST] == b"\xff" * (FIRST - SECOND),
                 "handler tail staging drift")
            (a.out / "after-tail-page.bin").write_bytes(page())
            stage = "second-staged"
            map_page(BASE)
            ping("install-dispatch", 2)
            stage = "second-complete"
            map_page(LOADER)
            need(word(0xE30) == 0x32435059 and word(0xE38) == 0,
                 "i960 full-handler checksum/dispatch report failed")
            map_page(TABLE)
            need(word(0x4FC) == HANDLER_ENTRY,
                 "i960 handler dispatch not installed")
            map_page(BASE)
            ping("handler-ping", 0)
            stage = "handler-accepted"
            (a.out / "result.json").write_text(json.dumps({
                "boot_id": boot, "stage": stage,
                "volatile_handler_entry": f"0x{HANDLER_ENTRY:08x}",
                "flash_commands": 0, "cold_reset_required_to_remove_handler": True,
            }, indent=2) + "\n")
        finally:
            # Once a command has started, firmware may still be executing
            # this RAM. Never remove it or force-unload an uncertain module.
            if not command_ever_started and modified:
                map_page(TABLE)
                put(0x4FC, table_before[0x4FC:0x500])
                map_page(LOADER)
                put(0, loader_before)
                if DEBUG.exists():
                    subprocess.run(["rmmod", "ping_probe"], check=True)
            if default_before is not None:
                map_page(BASE)
                need(page() == default_before, "default BAR page not restored")
            bar.close()
            os.close(resource)
            os.close(cfg)
            (a.out / "last-stage.txt").write_text(stage + "\n")


if __name__ == "__main__":
    main()

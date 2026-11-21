#!/usr/bin/env python3
"""One-shot auto-sense check using stock unsupported IOCTL 0x8f; no flash write."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

BDF = "0000:37:09.1"
DEV = Path("/sys/bus/pci/devices") / BDF
PEER = Path("/sys/bus/pci/devices/0000:37:04.1")
DEBUG = Path("/sys/kernel/debug/accele-senseprobe")
STOCK_SHA = "0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943"
MODULE_SHA = "4ce5a04f03e1aaac521896f0d94573f40e40ab9af2522a016e879c25604d1e67"
READER_SHA = "e199134ddf539ed8c651393494278ed23be29a9fbd922445270f91f4cc6515a1"
PREVIOUS_HOOK_BOOT = "e56a1655-ee74-45d3-b844-07d66b52640b"


def fields(path):
    return dict(piece.split("=", 1) for piece in path.read_text().split())


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def check_stock_read(path, boot):
    request = json.loads((path / "request.json").read_text())
    result = json.loads((path / "result.json").read_text())
    status = fields(path / "status.txt")
    data = (path / "data.bin").read_bytes()
    card = request.get("card", {})
    require(request.get("boot_id") == boot and request.get("selector") == 9 and
            request.get("module_sha256") == READER_SHA and
            card.get("bdf") == BDF and card.get("driver") == "myrsread" and
            result.get("card_after") == card and
            request.get("length") == 1048576 and result.get("sha256") == STOCK_SHA and
            len(data) == 1048576 and hashlib.sha256(data).hexdigest() == STOCK_SHA and
            all(status.get(k) == "0" for k in ("status", "residual", "guard_changes")),
            "fresh stock READIMAGE proof failed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("module", "read0", "read1", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--cold-power-cycle-observed", action="store_true")
    args = parser.parse_args()
    require(os.geteuid() == 0, "root required")
    with open("/run/lock/i960-loadrun.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        require(args.cold_power_cycle_observed and boot != PREVIOUS_HOOK_BOOT,
                "separate cold boot required after RAM dispatch probe")
        require(args.read0.resolve() != args.read1.resolve(), "independent reads required")
        check_stock_read(args.read0, boot)
        check_stock_read(args.read1, boot)
        require(args.module.name == "sense_probe.ko" and
                hashlib.sha256(args.module.read_bytes()).hexdigest() == MODULE_SHA,
                "unexpected sense-probe module")
        require(not PEER.exists() and (DEV / "driver").resolve().name == "myrsread" and
                Path("/sys/module/myrsread/parameters/read_bdf").read_text().strip() == BDF and
                not DEBUG.exists() and not Path("/sys/module/sense_probe").exists() and
                not Path("/sys/kernel/debug/accele-flashimage").exists() and
                not Path("/sys/kernel/debug/accele-stageimage").exists() and
                not list(DEV.glob("host*/target*/*/block/*")),
                "card or command-module preflight failed")
        host, = DEV.glob("host*/scsi_host/host*")
        require((host / "stock_descriptor").read_text().strip() ==
                "state=0 status=0 residual=0", "descriptor not idle")
        args.out.mkdir(parents=True, exist_ok=False)
        (args.out / "preflight.json").write_text(json.dumps({
            "boot_id": boot, "bdf": BDF, "stock_sha256": STOCK_SHA,
            "module_sha256": MODULE_SHA, "ioctl": "0x8f",
            "flash_program_erase_commands": 0,
        }, indent=2) + "\n")
        subprocess.run(["insmod", str(args.module), "bdf=" + BDF], check=True)
        require(fields(DEBUG / "status").get("started") == "0",
                "sense probe started unexpectedly")
        (DEBUG / "start").write_text("SENSEPROBE unsupported\n")
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            status = fields(DEBUG / "status")
            if status.get("done") == "1":
                break
            time.sleep(0.02)
        (args.out / "status.txt").write_text((DEBUG / "status").read_text())
        require(status.get("done") == "1", "command pending; keep module pinned")
        sense = status.get("sense", "")
        require(status.get("status") == "2" and status.get("residual") == "0" and
                int(status.get("sense_len", "0")) >= 14 and len(sense) == 28 and
                sense.endswith("8104"),
                "auto-sense differed; retain module and stop before FLASHIMAGE")
        (DEBUG / "release").write_text("release\n")
        subprocess.run(["rmmod", "sense_probe"], check=True)
        (args.out / "result.json").write_text(json.dumps({
            "boot_id": boot, "sense": sense, "internal_status": "0x104",
            "module_released": True, "flash_program_erase_commands": 0,
        }, indent=2) + "\n")


if __name__ == "__main__":
    main()

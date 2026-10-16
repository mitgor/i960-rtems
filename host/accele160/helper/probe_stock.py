#!/usr/bin/env python3
"""One-shot zero-DMA stock 0x8f test on the explicitly selected new card.

Run as root on the Linux host only after myrs8f is bound. A timeout retains
the module and command storage; it never attempts cancellation or unload.
"""
import argparse
import fcntl
import json
from pathlib import Path
import time


NEW_BDF = "0000:37:09.1"
OLD_BDF = "0000:37:04.1"
SYSFS = Path("/sys/bus/pci/devices")


def driver(bdf):
    link = SYSFS / bdf / "driver"
    return link.resolve().name if link.exists() else None


def identity():
    card = SYSFS / NEW_BDF
    values = {name: (card / name).read_text().strip()
              for name in ("vendor", "device", "subsystem_vendor", "subsystem_device")}
    if values != {"vendor": "0x1069", "device": "0x0050",
                  "subsystem_vendor": "0x1069", "subsystem_device": "0x0054"}:
        raise RuntimeError("unexpected new-card identity: " + str(values))
    if driver(NEW_BDF) != "myrs8f" or driver(OLD_BDF) is not None:
        raise RuntimeError("wrong driver ownership")
    if list(card.glob("host*/target*/*/block/*")):
        raise RuntimeError("new card has block devices")
    if Path("/sys/module/companion").exists() or Path("/sys/module/rawreader").exists():
        raise RuntimeError("retained reader module present")
    return values


def parse_status(raw):
    lines = raw.strip().splitlines()
    fields = dict(x.split("=", 1) for x in lines[0].split())
    if "mailbox=" in raw:
        fields["mailbox"] = next(line.split("=", 1)[1] for line in lines
                                 if line.startswith("mailbox="))
    return fields


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError("output exists")
    lock = open("/run/lock/i960-loadrun.lock", "w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    before = identity()
    host, = (SYSFS / NEW_BDF).glob("host*/scsi_host/host*")
    attr = host / "stock_unsupported"
    if parse_status(attr.read_text())["state"] != "0":
        raise RuntimeError("previous command still owned")
    boot_id = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    started = time.monotonic()
    attr.write_text("probe")
    while True:
        status = parse_status(attr.read_text())
        if status["state"] == "2" or time.monotonic() - started > 10:
            break
        time.sleep(0.05)
    result = {"boot_id": boot_id, "new_bdf": NEW_BDF, "old_bdf": OLD_BDF,
              "identity": before, "elapsed_seconds": time.monotonic() - started,
              "status": status, "new_driver_after": driver(NEW_BDF),
              "old_driver_after": driver(OLD_BDF)}
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    if status["state"] != "2":
        raise RuntimeError("command pending: module and command storage retained")
    mailbox = bytes.fromhex(status["mailbox"])
    expected = bytearray(64)
    expected[0] = 1  # MYRS_DCMD_TAG
    expected[2] = 0x20  # IOCTL
    expected[3] = 0x40  # no_autosense; no DMA direction
    expected[21] = 0x8f
    if mailbox != expected:
        raise RuntimeError("unexpected submitted mailbox; retain evidence")
    if status["status"] == "0" or status["residual"] != "0":
        raise RuntimeError("stock unsupported completion was not observed")
    if identity() != before:
        raise RuntimeError("card identity changed")
    attr.write_text("clear")
    if parse_status(attr.read_text())["state"] != "0":
        raise RuntimeError("completed command did not release")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

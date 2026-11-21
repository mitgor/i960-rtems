#!/usr/bin/env python3
"""Capture the installed AcceleRAID 160 spare, preserving the original card."""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "rtems/transport"))
from card_select import select, require_unbound_or_absent

SPARE = "0000:37:04.1"
ORIGINAL = "0000:37:09.1"
READER_SHA = "e199134ddf539ed8c651393494278ed23be29a9fbd922445270f91f4cc6515a1"
DRIVER_SHA = "7bf5ae04045de781c2233e14a947adcdc8d7ff81059f9913fa90226cb2020edf"
DRIVER_MODULE = Path("/home/mit/i960-dma-refusal-20261019/bundle/inputs/myrsread.ko")
FLASH_BYTES = 1048576
DEBUG = Path("/sys/kernel/debug/accele-rawreadimage")


def fields(value):
    return dict(part.split("=", 1) for part in value.split())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--spare-bdf", choices=("0000:37:04.1", "0000:37:09.1"), default=SPARE)
    args = parser.parse_args()
    spare_bdf = args.spare_bdf
    peer_bdf = ORIGINAL if spare_bdf == SPARE else SPARE
    lock = open("/run/lock/i960-loadrun.lock", "w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if args.module.name != "rawreader.ko" or hashlib.sha256(args.module.read_bytes()).hexdigest() != READER_SHA:
        raise ValueError("not the previously tested full-flash reader")
    if hashlib.sha256(DRIVER_MODULE.read_bytes()).hexdigest() != DRIVER_SHA:
        raise ValueError("not the reviewed BDF-limited driver")
    spare = select(spare_bdf, "accele160", driver="myrsread")
    original = require_unbound_or_absent(peer_bdf, "accele160")
    if original["driver"] is not None:
        raise ValueError("original card is bound")
    if Path("/sys/module/myrsread/parameters/read_bdf").read_text().strip() != spare_bdf:
        raise ValueError("read driver is not restricted to the spare")
    if DEBUG.exists() or Path("/sys/module/rawreader").exists():
        raise ValueError("previous full-flash reader is present")
    for bdf in (spare_bdf, peer_bdf):
        dev = Path("/sys/bus/pci/devices") / bdf
        if list(dev.glob("host*/target*/*/block/*")):
            raise ValueError(f"{bdf} exposes storage")
    dev = Path("/sys/bus/pci/devices") / spare_bdf
    host, = dev.glob("host*/scsi_host/host*")
    if not (host / "stock_descriptor").read_text().startswith("state=0 "):
        raise ValueError("descriptor job is not idle")
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "request.json").write_text(json.dumps({
        "card": spare, "original_card": original,
        "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        "module_sha256": READER_SHA, "selector": 9, "length": FLASH_BYTES,
    }, indent=2) + "\n")
    subprocess.run(["insmod", str(args.module), "bdf=" + spare_bdf,
                    "selector=9", "length=" + str(FLASH_BYTES)], check=True)
    start = time.monotonic()
    while True:
        status_text = (DEBUG / "status").read_text()
        status = fields(status_text)
        if status.get("done") == "1" or time.monotonic() - start > 20:
            break
        time.sleep(0.05)
    (args.out / "status.txt").write_text(status_text)
    if status.get("done") != "1":
        raise RuntimeError("READIMAGE pending; keep the module and DMA allocation pinned")
    data = (DEBUG / "data.bin").read_bytes()
    (args.out / "data.bin").write_bytes(data)
    if (len(data) != FLASH_BYTES or
            any(status.get(k) != v for k, v in {
                "status": "0", "residual": "0", "selector": "9",
                "length": str(FLASH_BYTES), "guard_changes": "0",
                "released": "0"}.items())):
        raise RuntimeError("READIMAGE failed or guard changed; keep module pinned")
    after = select(spare_bdf, "accele160", driver="myrsread")
    peer_after = require_unbound_or_absent(peer_bdf, "accele160")
    if after != spare or peer_after != original:
        raise RuntimeError("card state changed; keep module pinned")
    (DEBUG / "release").write_text("release\n")
    subprocess.run(["rmmod", "rawreader"], check=True)
    (args.out / "result.json").write_text(json.dumps({
        "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
        "elapsed_s": time.monotonic() - start, "card_after": after,
        "original_after": peer_after,
    }, indent=2) + "\n")
    print(args.out / "result.json")


if __name__ == "__main__":
    main()

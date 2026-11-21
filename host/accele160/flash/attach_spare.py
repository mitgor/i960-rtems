#!/usr/bin/env python3
"""First-bind the verified AcceleRAID spare on a cold boot; never flash it."""
import argparse
import fcntl
import hashlib
import json
import mmap
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "rtems/transport"))
from card_select import select, require_unbound_or_absent

SLOTS = ("0000:37:04.1", "0000:37:09.1")
DRIVER_SHA = "7bf5ae04045de781c2233e14a947adcdc8d7ff81059f9913fa90226cb2020edf"


def idb_byte(dev):
    fd = os.open(dev / "resource0", os.O_RDONLY | os.O_SYNC)
    try:
        mapping = mmap.mmap(fd, 4096, access=mmap.ACCESS_READ)
        try:
            return mapping[0x20]
        finally:
            mapping.close()
    finally:
        os.close(fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spare-bdf", choices=SLOTS, required=True)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    lock = open("/run/lock/i960-loadrun.lock", "w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    spare_bdf = args.spare_bdf
    peer_bdf = SLOTS[0] if spare_bdf == SLOTS[1] else SLOTS[1]
    if args.module.name != "myrsread.ko" or hashlib.sha256(args.module.read_bytes()).hexdigest() != DRIVER_SHA:
        raise ValueError("unreviewed parent driver")
    spare = select(spare_bdf, "accele160")
    peer = require_unbound_or_absent(peer_bdf, "accele160")
    if spare["driver"] is not None or Path("/sys/module/myrsread").exists() or Path("/sys/module/myrs").exists():
        raise ValueError("driver already present; cold first-bind only")
    for bdf in SLOTS:
        if list((Path("/sys/bus/pci/devices") / bdf).glob("host*/target*/*/block/*")):
            raise ValueError(f"{bdf} exposes storage")
    dev = Path("/sys/bus/pci/devices") / spare_bdf
    bridge = dev.parent / (spare_bdf[:-1] + "0")
    config = (bridge / "config").read_bytes()
    if len(config) < 0x42:
        raise RuntimeError("bridge PCI configuration is incomplete")
    ebcr = int.from_bytes(config[0x40:0x42], "little")
    status = idb_byte(dev)
    if ebcr & 4 or status != 0:
        raise RuntimeError(f"controller not ready: EBCR={ebcr:#06x}, LP IDB={status:#04x}; cold power cycle, do not retry")
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "before.json").write_text(json.dumps({
        "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        "spare": spare, "peer": peer, "bridge_ebcr": ebcr,
        "lp_idb": status, "module_sha256": DRIVER_SHA,
    }, indent=2) + "\n")
    subprocess.run(["modprobe", "raid_class"], check=True)
    result = subprocess.run(["insmod", str(args.module), "read_bdf=" + spare_bdf], check=False)
    after = select(spare_bdf, "accele160")
    peer_after = require_unbound_or_absent(peer_bdf, "accele160")
    hosts = list(dev.glob("host*/scsi_host/host*"))
    passed = (result.returncode == 0 and after["driver"] == "myrsread" and
              peer_after == peer and
              Path("/sys/module/myrsread/parameters/read_bdf").read_text().strip() == spare_bdf and
              len(hosts) == 1 and
              (hosts[0] / "stock_descriptor").read_text().startswith("state=0 ")) if after["driver"] == "myrsread" else False
    (args.out / "result.json").write_text(json.dumps({
        "passed": passed, "insmod_exit": result.returncode,
        "spare_after": after, "peer_after": peer_after,
        "lp_idb_after": idb_byte(dev),
    }, indent=2) + "\n")
    if not passed:
        raise RuntimeError("spare first-bind failed; no read or flash command issued; preserve this boot")
    print(args.out / "result.json")


if __name__ == "__main__":
    main()

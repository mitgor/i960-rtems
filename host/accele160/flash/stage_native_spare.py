#!/usr/bin/env python3
"""Stage exact native-ROM spare image in controller RAM; never program flash."""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "rtems/transport"))
sys.path.insert(0, str(ROOT / "rtems/accele160/native_rom"))
from card_select import select, require_unbound_or_absent
from preflight import verify_pair, FLASH_SIZE

SPARE = "0000:37:04.1"
ORIGINAL = "0000:37:09.1"
MODULE_SHA = "6ec76357ca5b22635d63d07a88c9f2675f01903684dbf5bd17c4e407a22dd3b8"
DEBUG = Path("/sys/kernel/debug/accele-stageimage")


def fields(path):
    return dict(item.split("=", 1) for item in path.read_text().split())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--read0", type=Path, required=True)
    parser.add_argument("--read1", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--spare-bdf", choices=("0000:37:04.1", "0000:37:09.1"), default=SPARE)
    args = parser.parse_args()
    spare_bdf = args.spare_bdf
    peer_bdf = ORIGINAL if spare_bdf == SPARE else SPARE
    lock = open("/run/lock/i960-loadrun.lock", "w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if args.module.name != "stage_image.ko" or hashlib.sha256(args.module.read_bytes()).hexdigest() != MODULE_SHA:
        raise ValueError("wrong STOREIMAGE module")
    image = args.image.read_bytes()
    boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    proof = verify_pair(image, (args.read0, args.read1), spare_bdf, boot)
    spare = select(spare_bdf, "accele160", driver="myrsread")
    original = require_unbound_or_absent(peer_bdf, "accele160")
    if spare != proof["card"] or original["driver"] is not None:
        raise ValueError("live card identity changed")
    if Path("/sys/module/myrsread/parameters/read_bdf").read_text().strip() != spare_bdf:
        raise ValueError("read driver is not restricted to spare")
    if DEBUG.exists() or Path("/sys/module/stage_image").exists():
        raise ValueError("previous stage command present")
    if (Path("/sys/kernel/debug/accele-senseprobe").exists() or
            Path("/sys/module/sense_probe").exists()):
        raise ValueError("sense probe still present")
    for name in ("accele-readimage", "accele-rawreadimage"):
        if (Path("/sys/kernel/debug") / name).exists():
            raise ValueError("reader command still present")
    dev = Path("/sys/bus/pci/devices") / spare_bdf
    for bdf in (spare_bdf, peer_bdf):
        if list((Path("/sys/bus/pci/devices") / bdf).glob("host*/target*/*/block/*")):
            raise ValueError(f"{bdf} exposes storage")
    host, = dev.glob("host*/scsi_host/host*")
    if not (host / "stock_descriptor").read_text().startswith("state=0 "):
        raise ValueError("descriptor job is not idle")
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "request.json").write_text(json.dumps({
        "boot_id": boot, "card": spare, "original_card": original,
        "candidate_sha256": proof["candidate_sha256"], "module_sha256": MODULE_SHA,
        "stock_preflight": proof, "command": "STOREIMAGE 0x2c",
        "selector": 9, "offset_kib": 0, "bytes": FLASH_SIZE,
    }, indent=2) + "\n")
    subprocess.run(["insmod", str(args.module), "bdf=" + spare_bdf], check=True)
    with (DEBUG / "image.bin").open("wb") as output:
        output.write(image)
    if (DEBUG / "image.bin").read_bytes() != image or fields(DEBUG / "status").get("written") != str(FLASH_SIZE):
        raise RuntimeError("host DMA allocation differs; retain module for inspection")
    (DEBUG / "start").write_text("stage\n")
    started = time.monotonic()
    while True:
        status = fields(DEBUG / "status")
        if status.get("done") == "1" or time.monotonic() - started > 20:
            break
        time.sleep(0.05)
    (args.out / "status.txt").write_text((DEBUG / "status").read_text())
    if status.get("done") != "1":
        raise RuntimeError("STOREIMAGE pending; retain module and DMA allocation")
    if any(status.get(k) != "0" for k in ("status", "residual", "guard_changes")):
        raise RuntimeError("STOREIMAGE failed; retain module and DMA allocation")
    if select(spare_bdf, "accele160", driver="myrsread") != spare or require_unbound_or_absent(peer_bdf, "accele160") != original:
        raise RuntimeError("card identity changed; retain module")
    (DEBUG / "release").write_text("release\n")
    subprocess.run(["rmmod", "stage_image"], check=True)
    (args.out / "result.json").write_text(json.dumps({
        "stage_completed": True, "flash_command_issued": False,
        "elapsed_s": time.monotonic() - started,
        "card_after": spare, "original_after": original,
    }, indent=2) + "\n")
    print(args.out / "result.json")


if __name__ == "__main__":
    main()

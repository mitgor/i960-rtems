#!/usr/bin/env python3
"""Stage the exact audited allocator-probe image; never issue FLASHIMAGE."""

import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "rtems/transport"))
from card_select import select


CANDIDATE_SHA256 = "0124657ded5618f1a00737d4917a500bccbbeea951e3f1e33cee6d84799dd5d0"
BDF = "0000:37:09.1"
OLD_BDF = "0000:37:04.1"
DEBUG = Path("/sys/kernel/debug/accele-stageimage")


def fields(path: Path) -> dict[str, str]:
    return dict(part.split("=", 1) for part in path.read_text().split())


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--module", type=Path, required=True)
    p.add_argument("--image", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    image = a.image.read_bytes()
    if len(image) != 1048576 or hashlib.sha256(image).hexdigest() != CANDIDATE_SHA256:
        raise ValueError("not the exact reviewed allocator-probe 1 MiB image")
    lock = open("/run/lock/i960-loadrun.lock", "w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    new = select(BDF, "accele160", driver="myrsread")
    if select(OLD_BDF, "dac960pg")["driver"] is not None:
        raise ValueError("old card must remain unbound")
    if DEBUG.exists() or Path("/sys/module/stage_image").exists():
        raise ValueError("previous stage job still present")
    for other in ("accele-readimage", "accele-rawreadimage"):
        status = Path("/sys/kernel/debug") / other / "status"
        if status.exists() and fields(status).get("done") != "1":
            raise ValueError("another image command is pending")
    dev = Path("/sys/bus/pci/devices") / BDF
    if list(dev.glob("host*/target*/*/block/*")):
        raise ValueError("card has block devices")
    host, = dev.glob("host*/scsi_host/host*")
    if not (host / "stock_descriptor").read_text().startswith("state=0 "):
        raise ValueError("driver descriptor job active")
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / "request.json").write_text(json.dumps({
        "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        "card": new, "old_card": select(OLD_BDF, "dac960pg"),
        "module_sha256": hashlib.sha256(a.module.read_bytes()).hexdigest(),
        "image_sha256": CANDIDATE_SHA256, "command": "STOREIMAGE 0x2c",
        "selector": 9, "offset_kib": 0, "bytes": len(image),
    }, indent=2) + "\n")
    subprocess.run(["insmod", str(a.module), "bdf=" + BDF], check=True)
    # No card command runs until all bytes are copied back and compared.
    with (DEBUG / "image.bin").open("wb") as f:
        f.write(image)
    returned = (DEBUG / "image.bin").read_bytes()
    if returned != image or fields(DEBUG / "status").get("written") != str(len(image)):
        raise RuntimeError("host DMA allocation differs; leave module loaded for inspection")
    (DEBUG / "start").write_text("stage\n")
    started = time.monotonic()
    while True:
        state = fields(DEBUG / "status")
        if state.get("done") == "1" or time.monotonic() - started > 20:
            break
        time.sleep(0.05)
    (a.out / "status.txt").write_text((DEBUG / "status").read_text())
    if state.get("done") != "1":
        raise RuntimeError("STOREIMAGE pending: module/DMA retained; do not unload or unbind")
    if any(state.get(key) != "0" for key in ("status", "residual", "guard_changes")):
        raise RuntimeError("STOREIMAGE failed: module/DMA retained for inspection")
    (DEBUG / "release").write_text("release\n")
    subprocess.run(["rmmod", "stage_image"], check=True)
    (a.out / "result.json").write_text(json.dumps({
        "elapsed_s": time.monotonic() - started,
        "stage_completed": True, "flash_command_issued": False,
        "card_after": select(BDF, "accele160"),
        "old_after": select(OLD_BDF, "dac960pg"),
    }, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""One-shot vector gate FLASHIMAGE after exact same-boot staging/readback."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "rtems/transport"))
from card_select import select


BDF = "0000:37:09.1"
OLD_BDF = "0000:37:04.1"
FLASH_MODULE_SHA256 = "bf7352f069a3dec363743a4c92b1e093e849c5a6525ec607c04338c308deca90"
IMAGE_SHA256 = "93faf91f553822665cd4125d90b1066370c4bca0da76af8336daf98bc2dae094"
DEBUG = Path("/sys/kernel/debug/accele-flashimage")


def parse_status(path: Path) -> dict[str, str]:
    return dict(part.split("=", 1) for part in path.read_text().split())


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--module", type=Path, required=True)
    p.add_argument("--stage-dir", type=Path, required=True)
    p.add_argument("--readback-dir", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    lock = open("/run/lock/i960-loadrun.lock", "w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if hashlib.sha256(a.module.read_bytes()).hexdigest() != FLASH_MODULE_SHA256:
        raise ValueError("wrong flash module")
    boot_id = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    card = select(BDF, "accele160", driver="myrsread")
    old = select(OLD_BDF, "dac960pg")
    if old["driver"] is not None:
        raise ValueError("old card must remain unbound")
    if DEBUG.exists() or Path("/sys/module/flash_image").exists():
        raise ValueError("previous flash job still present")
    for other in ("accele-readimage", "accele-rawreadimage", "accele-stageimage"):
        path = Path("/sys/kernel/debug") / other
        if path.exists():
            raise ValueError(f"other image job still present: {path}")
    dev = Path("/sys/bus/pci/devices") / BDF
    if list(dev.glob("host*/target*/*/block/*")):
        raise ValueError("card has block devices")
    host, = dev.glob("host*/scsi_host/host*")
    if not (host / "stock_descriptor").read_text().startswith("state=0 "):
        raise ValueError("driver descriptor job active")
    stage = json.loads((a.stage_dir / "request.json").read_text())
    stage_result = json.loads((a.stage_dir / "result.json").read_text())
    stage_status = parse_status(a.stage_dir / "status.txt")
    read_request = json.loads((a.readback_dir / "request.json").read_text())
    read_result = json.loads((a.readback_dir / "result.json").read_text())
    read_status = parse_status(a.readback_dir / "status.txt")
    readback = (a.readback_dir / "data.bin").read_bytes()
    if (stage.get("boot_id") != boot_id or read_request.get("boot_id") != boot_id or
            stage.get("image_sha256") != IMAGE_SHA256 or
            stage.get("command") != "STOREIMAGE 0x2c" or
            stage.get("selector") != 9 or stage.get("offset_kib") != 0 or
            stage.get("bytes") != 1048576 or
            not stage_result.get("stage_completed") or
            stage_result.get("flash_command_issued") is not False or
            stage_result.get("card_after") != card or
            stage_result.get("old_after") != old or
            any(stage_status.get(k) != "0" for k in
                ("status", "residual", "guard_changes")) or
            read_request.get("selector") != 9 or
            read_request.get("length") != 1048576 or
            read_result.get("bytes") != 1048576 or
            read_result.get("sha256") != IMAGE_SHA256 or
            read_result.get("card_after") != card or
            read_result.get("old_after") != old or
            any(read_status.get(k) != "0" for k in
                ("status", "residual", "guard_changes")) or
            len(readback) != 1048576 or
            hashlib.sha256(readback).hexdigest() != IMAGE_SHA256):
        raise ValueError("same-boot candidate stage/readback proof is incomplete")
    a.out.mkdir(parents=True, exist_ok=False)
    record = {
        "boot_id": boot_id, "card": card, "old_card": old,
        "image_sha256": IMAGE_SHA256,
        "module_sha256": hashlib.sha256(a.module.read_bytes()).hexdigest(),
        "stage_dir": str(a.stage_dir), "readback_dir": str(a.readback_dir),
        "command": "FLASHIMAGE 0x2e selector 9 zero DMA",
    }
    with (a.out / "preflight.json").open("w") as f:
        json.dump(record, f, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    subprocess.run(["insmod", str(a.module), "bdf=" + BDF], check=True)
    if parse_status(DEBUG / "status").get("started") != "0":
        raise RuntimeError("unexpected FLASHIMAGE module state; no command issued")
    (DEBUG / "start").write_text("FLASHIMAGE selector=9\n")
    started = time.monotonic()
    while True:
        state = parse_status(DEBUG / "status")
        if state.get("done") == "1" or time.monotonic() - started > 120:
            break
        time.sleep(0.1)
    (a.out / "status.txt").write_text((DEBUG / "status").read_text())
    if state.get("done") != "1":
        raise RuntimeError("FLASHIMAGE pending: keep driver/module loaded; do not free command")
    if state.get("status") != "0" or state.get("residual") != "0":
        raise RuntimeError("FLASHIMAGE failed: retain module and inspect before reboot")
    (DEBUG / "release").write_text("release\n")
    subprocess.run(["rmmod", "flash_image"], check=True)
    (a.out / "result.json").write_text(json.dumps({
        "command_completed": True, "elapsed_s": time.monotonic() - started,
        "status": state, "card_after": select(BDF, "accele160"),
        "old_after": select(OLD_BDF, "dac960pg"),
        "post_reboot_full_flash_readback_required": True,
    }, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

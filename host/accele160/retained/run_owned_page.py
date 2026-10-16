#!/usr/bin/env python3
"""Run one fixed 512 KiB owned-page upload and reserve/release proof after paired flash audits."""

import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "rtems/transport"))
from card_select import select

BDF = "0000:37:09.1"
OLD_BDF = "0000:37:04.1"
IMAGE_SHA = "e7a3a7c5b4dcbbd933813155f03544cc691dac7e7b63fade79255d2452d6ffc0"
RESERVE_SHA = "d5dc1cf2dddba559ea4ff5ebf7bac1ae32f462f27dd968b8964f0cd20b47c945"
RELEASE_SHA = "bbfbe079b86ba1503efcfcce4c0c7ee5e1ad2fc662ded669766bdb7d38a3ecfa"
SESSION_SHA = "175159029de307cca43fc7c8cbd9c31ed48333bd8b24afb7c35ecc1a29932034"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fields(path: Path) -> dict[str, str]:
    return dict(item.split("=", 1) for item in path.read_text().split())


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("reserve_module", "release_module", "session", "image",
                 "readback0", "readback1", "out"):
        p.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    a = p.parse_args()
    lock = open("/run/lock/i960-loadrun.lock", "w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if (sha(a.image), sha(a.reserve_module), sha(a.release_module), sha(a.session)) != \
            (IMAGE_SHA, RESERVE_SHA, RELEASE_SHA, SESSION_SHA):
        raise ValueError("image or executable differs from reviewed binary")
    for name in ("reserve", "release"):
        if (Path("/sys/kernel/debug") / f"accele-{name}").exists() or \
                (Path("/sys/module") / f"{name}_command").exists():
            raise ValueError("previous retained-grant companion still present")
    card = select(BDF, "accele160", driver="myrsread")
    old = select(OLD_BDF, "dac960pg")
    if old["driver"] is not None:
        raise ValueError("old card must remain unbound")
    dev = Path("/sys/bus/pci/devices") / BDF
    if list(dev.glob("host*/target*/*/block/*")):
        raise ValueError("new card has block devices")
    host, = dev.glob("host*/scsi_host/host*")
    if not (host / "stock_descriptor").read_text().startswith("state=0 "):
        raise ValueError("driver descriptor job active")
    boot_id = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    for path in (a.readback0, a.readback1):
        req = json.loads((path / "request.json").read_text())
        result = json.loads((path / "result.json").read_text())
        state = fields(path / "status.txt")
        if (req["boot_id"] != boot_id or result["sha256"] != IMAGE_SHA or
                result["bytes"] != 1048576 or result["card_after"] != card or
                result["old_after"] != old or sha(path / "data.bin") != IMAGE_SHA or
                any(state.get(k) != "0" for k in ("status", "residual", "guard_changes"))):
            raise ValueError(f"paired same-boot flash audit failed: {path}")
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / "preflight.json").write_text(json.dumps(dict(
        boot_id=boot_id, card=card, old_card=old, image_sha256=IMAGE_SHA,
        reserve_module_sha256=RESERVE_SHA, release_module_sha256=RELEASE_SHA,
        session_sha256=SESSION_SHA, readbacks=[str(a.readback0), str(a.readback1)]
    ), indent=2) + "\n")
    subprocess.run(["insmod", str(a.reserve_module), "bdf=" + BDF], check=True)
    subprocess.run(["insmod", str(a.release_module), "bdf=" + BDF], check=True)
    for name in ("reserve", "release"):
        if fields(Path("/sys/kernel/debug") / f"accele-{name}" / "status").get("started") != "0":
            raise RuntimeError("companion started before session; retain for inspection")
    with (a.out / "session.txt").open("w") as log:
        run = subprocess.run([str(a.session), str(a.out)], stdout=log,
                             stderr=subprocess.STDOUT)
    states = {name: fields(Path("/sys/kernel/debug") / f"accele-{name}" / "status")
              for name in ("reserve", "release")}
    if run.returncode or any(state.get("done") != "1" or state.get("released") != "1"
                             for state in states.values()):
        raise RuntimeError("reserve/release uncertain: retain both modules and RAM")
    subprocess.run(["rmmod", "release_command"], check=True)
    subprocess.run(["rmmod", "reserve_command"], check=True)
    (a.out / "result.json").write_text(json.dumps(dict(
        returncode=run.returncode, commands=states,
        card_after=select(BDF, "accele160"),
        old_after=select(OLD_BDF, "dac960pg"),
    ), indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

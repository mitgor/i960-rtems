#!/usr/bin/env python3
"""Run one exact bounded RAM probe on the new card after paired flash audits."""

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
CANDIDATE_SHA = "1f13799b880d7e3de2c2037c44fff7e78c0a8f3f391cd05df4a67c41f36c4aaf"
PROBE_SHA = "5d86878199ddcdd7f7ea950699a8e047f4189eb264c1dcff860ee6f83e0e740c"
MODULE_SHA = "1b98c11cf4a1b667aebefdfdffa354208a0031cb5477b7b354b238cc6f4d0899"
SESSION_SHA = "4331140c7058061b1eed4b59611e6799b3f2e5ab71a225d6058417b351c161a9"
DEBUG = Path("/sys/kernel/debug/accele-ramprobe")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fields(path: Path) -> dict[str, str]:
    return dict(item.split("=", 1) for item in path.read_text().split())


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("module", "session", "probe", "image", "readback0", "readback1", "out"):
        p.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    a = p.parse_args()
    lock = open("/run/lock/i960-loadrun.lock", "w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if DEBUG.exists() or Path("/sys/module/ram_probe_command").exists():
        raise ValueError("prior RAM-probe command still present")
    card = select(BDF, "accele160", driver="myrsread")
    old = select(OLD_BDF, "dac960pg")
    if old["driver"] is not None:
        raise ValueError("old card must remain unbound")
    if list((Path("/sys/bus/pci/devices") / BDF).glob("host*/target*/*/block/*")):
        raise ValueError("new card has block devices")
    if (sha(a.image) != CANDIDATE_SHA or sha(a.probe) != PROBE_SHA or
            sha(a.module) != MODULE_SHA or sha(a.session) != SESSION_SHA):
        raise ValueError("candidate, probe, module or session differs from reviewed binary")
    boot_id = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    for path in (a.readback0, a.readback1):
        req = json.loads((path / "request.json").read_text())
        result = json.loads((path / "result.json").read_text())
        status = fields(path / "status.txt")
        if (req["boot_id"] != boot_id or result["sha256"] != CANDIDATE_SHA or
                result["bytes"] != 1048576 or result["card_after"] != card or
                result["old_after"] != old or
                any(status.get(k) != "0" for k in ("status", "residual", "guard_changes")) or
                sha(path / "data.bin") != CANDIDATE_SHA):
            raise ValueError(f"same-boot full flash audit failed: {path}")
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / "preflight.json").write_text(json.dumps(dict(
        boot_id=boot_id, card=card, old_card=old, candidate_sha256=CANDIDATE_SHA,
        probe_sha256=PROBE_SHA, module_sha256=MODULE_SHA,
        session_sha256=SESSION_SHA, readbacks=[str(a.readback0), str(a.readback1)]
    ), indent=2) + "\n")
    subprocess.run(["insmod", str(a.module), "bdf=" + BDF], check=True)
    if fields(DEBUG / "status").get("started") != "0":
        raise RuntimeError("unexpected command module state; no command submitted")
    with (a.out / "session.txt").open("w") as log:
        run = subprocess.run([str(a.session), str(a.probe),
                              str(a.out / "page-before.bin"),
                              str(a.out / "page-after-call.bin")],
                             stdout=log, stderr=subprocess.STDOUT)
    state = fields(DEBUG / "status")
    (a.out / "command-status.txt").write_text((DEBUG / "status").read_text())
    if state.get("done") != "1" or state.get("released") != "1":
        raise RuntimeError("uncertain command: retain module and RAM until diagnosed")
    subprocess.run(["rmmod", "ram_probe_command"], check=True)
    result = dict(returncode=run.returncode, card_after=select(BDF, "accele160"),
                  old_after=select(OLD_BDF, "dac960pg"), command=state)
    (a.out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    if run.returncode:
        raise RuntimeError("bounded command completed but result validation failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

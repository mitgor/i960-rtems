#!/usr/bin/env python3
"""Run one exact bounded allocator probe on the new card after paired flash audits."""

import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "rtems/transport"))
from card_select import select
from verify_live import verify

BDF = "0000:37:09.1"
OLD_BDF = "0000:37:04.1"
CANDIDATE_SHA = "0124657ded5618f1a00737d4917a500bccbbeea951e3f1e33cee6d84799dd5d0"
MODULE_SHA = "0a0d0e223ac2b2b092e5375ca4f81a08f0fb5eaab61e135ea079f15056a1d85e"
SESSION_SHA = "f8d842bcfcd043f1597aafe28ac8796630368226404cf85bbcc7aeb61c96d1d5"
DEBUG = Path("/sys/kernel/debug/accele-allocprobe")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fields(path: Path) -> dict[str, str]:
    return dict(item.split("=", 1) for item in path.read_text().split())


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("module", "session", "image", "readback0", "readback1", "out"):
        p.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    a = p.parse_args()
    lock = open("/run/lock/i960-loadrun.lock", "w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if DEBUG.exists() or Path("/sys/module/allocator_command").exists():
        raise ValueError("prior allocator-probe command still present")
    card = select(BDF, "accele160", driver="myrsread")
    old = select(OLD_BDF, "dac960pg")
    if old["driver"] is not None:
        raise ValueError("old card must remain unbound")
    if list((Path("/sys/bus/pci/devices") / BDF).glob("host*/target*/*/block/*")):
        raise ValueError("new card has block devices")
    if (sha(a.image) != CANDIDATE_SHA or sha(a.module) != MODULE_SHA or sha(a.session) != SESSION_SHA):
        raise ValueError("candidate, module or session differs from reviewed binary")
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
        module_sha256=MODULE_SHA,
        session_sha256=SESSION_SHA, readbacks=[str(a.readback0), str(a.readback1)]
    ), indent=2) + "\n")
    subprocess.run(["insmod", str(a.module), "bdf=" + BDF], check=True)
    if fields(DEBUG / "status").get("started") != "0":
        raise RuntimeError("unexpected command module state; no command submitted")
    with (a.out / "session.txt").open("w") as log:
        run = subprocess.run([str(a.session), str(a.out / "page-before.bin"),
                              str(a.out / "page-after-call.bin"),
                              str(a.out / "table-before.bin"),
                              str(a.out / "table-after.bin")],
                             stdout=log, stderr=subprocess.STDOUT)
    state = fields(DEBUG / "status")
    (a.out / "command-status.txt").write_text((DEBUG / "status").read_text())
    if state.get("done") != "1" or state.get("released") != "1":
        raise RuntimeError("uncertain command: retain module and RAM until diagnosed")
    subprocess.run(["rmmod", "allocator_command"], check=True)
    result = dict(returncode=run.returncode, card_after=select(BDF, "accele160"),
                  old_after=select(OLD_BDF, "dac960pg"), command=state)
    (a.out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    if run.returncode:
        raise RuntimeError("bounded command completed but result validation failed")
    (a.out / "replay.json").write_text(json.dumps(verify(a.out), indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

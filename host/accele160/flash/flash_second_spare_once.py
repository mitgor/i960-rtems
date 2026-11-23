#!/usr/bin/env python3
"""One explicitly authorized stock FLASHIMAGE attempt on spare 10112504772.

The card's stock writer failed twice before. This wrapper does not fix it;
it pins this new candidate and records one attempt, including auto-sense.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "rtems/transport"))
sys.path.insert(0, str(ROOT / "rtems/accele160/native_rom"))
from card_select import select, require_unbound_or_absent
from preflight import (verify_pair, FLASH_SIZE, SECOND_SPARE_STOCK_SHA,
                       SECOND_SPARE_CORRECTED_WRITER_SHA)

BDF = "0000:37:09.1"
PEER = "0000:37:04.1"
FLASH_MODULE_SHA = "1ba32738d7d055349db23d4bb17257364cd279f3ed048800f0b4c7c7b6d59bd3"
STAGE_MODULE_SHA = "6ec76357ca5b22635d63d07a88c9f2675f01903684dbf5bd17c4e407a22dd3b8"
READER_MODULE_SHA = "e199134ddf539ed8c651393494278ed23be29a9fbd922445270f91f4cc6515a1"
DEBUG = Path("/sys/kernel/debug/accele-flashimage")
ATTEMPT = Path("/home/mit/i960-second-native-flash-attempt-20261123.json")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fields(path):
    return dict(part.split("=", 1) for part in path.read_text().split())


def need(ok, why):
    if not ok:
        raise RuntimeError(why)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("module", "image", "stock0", "stock1", "stage", "readback", "out"):
        p.add_argument("--" + key, type=Path, required=True)
    p.add_argument("--execute", action="store_true",
                   help="issue the one destructive FLASHIMAGE command")
    a = p.parse_args()
    with open("/run/lock/i960-loadrun.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        image = a.image.read_bytes()
        need(len(image) == FLASH_SIZE and sha(image) == SECOND_SPARE_CORRECTED_WRITER_SHA,
             "wrong card-specific candidate")
        need(a.module.name == "flash_image.ko" and sha(a.module.read_bytes()) == FLASH_MODULE_SHA,
             "wrong auto-sense FLASHIMAGE module")
        proof = verify_pair(image, (a.stock0, a.stock1), BDF, boot)
        need(proof["stock_sha256"] == SECOND_SPARE_STOCK_SHA and
             proof["candidate_sha256"] == SECOND_SPARE_CORRECTED_WRITER_SHA,
             "wrong stock/candidate pair")
        card = select(BDF, "accele160", driver="myrsread")
        peer = require_unbound_or_absent(PEER, "accele160")
        need(card == proof["card"] and peer["present"] is False and
             Path("/sys/module/myrsread/parameters/read_bdf").read_text().strip() == BDF,
             "card, peer or driver identity changed")
        dev = Path("/sys/bus/pci/devices") / BDF
        host, = dev.glob("host*/scsi_host/host*")
        need((host / "stock_descriptor").read_text().strip() ==
             "state=0 status=0 residual=0", "descriptor not idle")
        need(not list(dev.glob("host*/target*/*/block/*")), "card exposes storage")
        for path in (DEBUG, Path("/sys/module/flash_image"),
                     Path("/sys/kernel/debug/accele-stageimage"),
                     Path("/sys/kernel/debug/accele-rawreadimage"),
                     Path("/sys/kernel/debug/accele-readimage"),
                     Path("/sys/kernel/debug/accele-senseprobe")):
            need(not path.exists(), f"command already present: {path}")
        need(not ATTEMPT.exists(), "this spare already has a one-shot attempt marker")
        sr = json.loads((a.stage / "request.json").read_text())
        so = json.loads((a.stage / "result.json").read_text())
        ss = fields(a.stage / "status.txt")
        rr = json.loads((a.readback / "request.json").read_text())
        ro = json.loads((a.readback / "result.json").read_text())
        rs = fields(a.readback / "status.txt")
        read_data = (a.readback / "data.bin").read_bytes()
        need(sr.get("boot_id") == boot and sr.get("card") == card and
             sr.get("original_card") == peer and
             sr.get("candidate_sha256") == SECOND_SPARE_CORRECTED_WRITER_SHA and
             sr.get("module_sha256") == STAGE_MODULE_SHA and
             sr.get("stock_preflight") == proof and
             sr.get("command") == "STOREIMAGE 0x2c" and
             sr.get("selector") == 9 and sr.get("offset_kib") == 0 and
             sr.get("bytes") == FLASH_SIZE and
             so.get("stage_completed") is True and
             so.get("flash_command_issued") is False and
             so.get("card_after") == card and so.get("original_after") == peer and
             all(ss.get(k) == v for k, v in {
                 "written": str(FLASH_SIZE), "started": "1", "done": "1",
                 "status": "0", "residual": "0", "guard_changes": "0"}.items()) and
             rr.get("boot_id") == boot and rr.get("card") == card and
             rr.get("original_card") == peer and
             rr.get("module_sha256") == READER_MODULE_SHA and
             rr.get("selector") == 9 and rr.get("length") == FLASH_SIZE and
             ro.get("bytes") == FLASH_SIZE and
             ro.get("sha256") == SECOND_SPARE_CORRECTED_WRITER_SHA and
             ro.get("card_after") == card and ro.get("original_after") == peer and
             all(rs.get(k) == v for k, v in {
                 "done": "1", "status": "0", "residual": "0",
                 "guard_changes": "0", "selector": "9",
                 "length": str(FLASH_SIZE)}.items()) and
             read_data == image,
             "same-boot STOREIMAGE and full staged readback differ")
        record = {"boot_id": boot, "card": card, "peer": peer,
                  "stock_sha256": SECOND_SPARE_STOCK_SHA,
                  "candidate_sha256": SECOND_SPARE_CORRECTED_WRITER_SHA,
                  "module_sha256": FLASH_MODULE_SHA,
                  "prior_stock_flashimage_failures": 2,
                  "command": "FLASHIMAGE 0x2e selector 9 zero DMA",
                  "stage": str(a.stage), "readback": str(a.readback)}
        if not a.execute:
            print(json.dumps({**record, "preflight_only": True}, indent=2))
            return
        a.out.mkdir(parents=True, exist_ok=False)
        (a.out / "preflight.json").write_text(json.dumps(record, indent=2) + "\n")
        fd = os.open(ATTEMPT, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(record, f, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        subprocess.run(["insmod", str(a.module), "bdf=" + BDF], check=True)
        need(fields(DEBUG / "status").get("started") == "0",
             "unexpected module state; no flash command issued")
        (DEBUG / "start").write_text("FLASHIMAGE selector=9\n")
        started = time.monotonic()
        while True:
            state = fields(DEBUG / "status")
            if state.get("done") == "1" or time.monotonic() - started > 120:
                break
            time.sleep(0.1)
        (a.out / "status.txt").write_text((DEBUG / "status").read_text())
        result = {**record, "elapsed_s": time.monotonic() - started,
                  "done": state.get("done") == "1",
                  "status": state, "success": state.get("done") == "1" and
                  state.get("status") == "0" and state.get("residual") == "0"}
        (a.out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        need(result["done"], "FLASHIMAGE pending; retain module and driver")
        need(result["success"], "FLASHIMAGE failed; retain module and inspect sense")
        (DEBUG / "release").write_text("release\n")
        subprocess.run(["rmmod", "flash_image"], check=True)
        print(a.out / "result.json")


if __name__ == "__main__":
    main()

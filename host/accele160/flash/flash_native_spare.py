#!/usr/bin/env python3
"""One-shot FLASHIMAGE of the reviewed native-ROM candidate to the spare."""
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
from preflight import (verify_pair, SECOND_SPARE_PCI_RELEASE_SHA,
                       SLOT5_LIVE_PCI_RELEASE_SHA, RESTORED_SLOT5_UPDATER_SHA,
                       ORIGINAL_RAM_LOADER_SHA, SECOND_SPARE_RAM_LOADER_SHA,
                       SECOND_SPARE_WRITER_SHA, SECOND_SPARE_OCTOBER_HANDLER_SHA,
                       OCTOBER_CARD_INSTALLED_SHA, OCTOBER_CARD_CORRECTED_WRITER_SHA,
                       FLASH_SIZE)

SPARE = "0000:37:04.1"
ORIGINAL = "0000:37:09.1"
FLASH_MODULE_SHA = "bf7352f069a3dec363743a4c92b1e093e849c5a6525ec607c04338c308deca90"
DIAGNOSTIC_FLASH_MODULE_SHA = "1ba32738d7d055349db23d4bb17257364cd279f3ed048800f0b4c7c7b6d59bd3"
STAGE_MODULE_SHA = "6ec76357ca5b22635d63d07a88c9f2675f01903684dbf5bd17c4e407a22dd3b8"
READER_MODULE_SHA = "e199134ddf539ed8c651393494278ed23be29a9fbd922445270f91f4cc6515a1"
DEBUG = Path("/sys/kernel/debug/accele-flashimage")
# This exact stock card/image returned status 2 immediately after a verified
# STOREIMAGE and staged readback on 2026-11-20. A cold read showed no write.
# Do not issue the same destructive command again without a diagnosed change.
REJECTED_STOCK_SHA = "0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943"
LOCK_PROBE_BOOT = "e56a1655-ee74-45d3-b844-07d66b52640b"
LOCK_PROBE_PAYLOAD_SHA = "f2d1352e01e7d69f9277623bb8d89047970df27312330121cb4b9b89f4809623"
SENSE_PROBE_MODULE_SHA = "4ce5a04f03e1aaac521896f0d94573f40e40ab9af2522a016e879c25604d1e67"
OCTOBER_HANDLER_SHA = "8d8c79c3b8c206608ef7221000991c0d75eb101ce06581fedc2a74522648ad34"
OCTOBER_ACCEPTED_SHA = "1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd"
CURRENT_NATIVE_ATTEMPT = Path("/home/mit/i960-current-native-flash-attempt-20261123.json")


def verify_october_handler_test(directory, boot, stock_sha, candidate_sha):
    """One explicitly requested comparison against the October handler image."""
    audit = json.loads((directory / "audit.json").read_text())
    expected = {
        "stock_sha256": REJECTED_STOCK_SHA,
        "candidate_sha256": SECOND_SPARE_OCTOBER_HANDLER_SHA,
        "october_candidate_sha256": OCTOBER_ACCEPTED_SHA,
        "handler_sha256": OCTOBER_HANDLER_SHA,
        "changed_bytes": 4277,
        "loader_hook_offset": 276940,
        "handler_offset": 283096,
        "loader_checksum": "0x4436ed70",
        "trailer_checksum": "0x44440277",
        "serial_preserved": True,
        "only_serial_diff_from_october_candidate": True,
        "runtime_unchanged": True,
        "boot_block_unchanged": True,
        "known_checksums_pass": True,
        "flash_command_issued": False,
    }
    if (stock_sha != REJECTED_STOCK_SHA or
            candidate_sha != SECOND_SPARE_OCTOBER_HANDLER_SHA or
            audit != expected or
            hashlib.sha256((directory / "candidate.bin").read_bytes()).hexdigest()
            != candidate_sha or
            (directory / "october-handler-attempt.json").exists()):
        raise ValueError("October handler test image, audit, or one-attempt gate differs")
    return {"boot_id": boot, "candidate_sha256": candidate_sha,
            "october_accepted_sha256": OCTOBER_ACCEPTED_SHA,
            "same_handler_sha256": OCTOBER_HANDLER_SHA}


def verify_diagnostic_retry(directory, boot, stock_sha, candidate_sha):
    """Allow one new-boot sense diagnostic for this exact previously rejected card."""
    if (boot == LOCK_PROBE_BOOT or stock_sha != REJECTED_STOCK_SHA or
            candidate_sha != SECOND_SPARE_WRITER_SHA):
        raise ValueError("diagnostic retry card, image, or boot differs")
    preflight = json.loads((directory / "probe/preflight.json").read_text())
    result = json.loads((directory / "probe/result.json").read_text())
    probe_status = result.get("status", {})
    after_request = json.loads((directory / "read-after/request.json").read_text())
    after = json.loads((directory / "read-after/result.json").read_text())
    after_status = fields(directory / "read-after/status.txt")
    identity = result.get("identification", {})
    if (preflight.get("boot_id") != LOCK_PROBE_BOOT or
            preflight.get("bdf") != "0000:37:09.1" or
            preflight.get("stock_sha256") != REJECTED_STOCK_SHA or
            preflight.get("flash_id_payload_sha256") != LOCK_PROBE_PAYLOAD_SHA or
            preflight.get("flash_program_erase_commands") != 0 or
            result.get("boot_id") != LOCK_PROBE_BOOT or
            result.get("expected_id_and_locks") is not True or
            result.get("flash_program_erase_commands") != 0 or
            any(probe_status.get(k) != v for k, v in
                {"started": "1", "done": "1", "status": "2",
                 "residual": "0", "bad_signature": "0"}.items()) or
            identity.get("manufacturer") != 0x89 or
            identity.get("device") != 0xa6 or
            identity.get("master_lock") != 0 or
            identity.get("all_block_locks") != 0 or
            identity.get("return_code") != 0 or
            after_request.get("boot_id") != LOCK_PROBE_BOOT or
            after_request.get("selector") != 9 or
            after_request.get("length") != FLASH_SIZE or
            after.get("sha256") != REJECTED_STOCK_SHA or
            any(after_status.get(k) != "0" for k in
                ("status", "residual", "guard_changes"))):
        raise ValueError("all-block lock probe or stock readback is incomplete")
    if hashlib.sha256((directory / "read-after/data.bin").read_bytes()).hexdigest() != REJECTED_STOCK_SHA:
        raise ValueError("post-probe full flash bytes differ")
    return {"boot_id": LOCK_PROBE_BOOT,
            "all_block_locks": 0, "post_probe_stock_sha256": REJECTED_STOCK_SHA}


def fields(path):
    return dict(item.split("=", 1) for item in path.read_text().split())


def verify_sense_probe(directory, boot):
    preflight = json.loads((directory / "preflight.json").read_text())
    result = json.loads((directory / "result.json").read_text())
    status = fields(directory / "status.txt")
    sense = status.get("sense", "")
    if (preflight.get("boot_id") != boot or
            preflight.get("bdf") != "0000:37:09.1" or
            preflight.get("stock_sha256") != REJECTED_STOCK_SHA or
            preflight.get("module_sha256") != SENSE_PROBE_MODULE_SHA or
            preflight.get("ioctl") != "0x8f" or
            preflight.get("flash_program_erase_commands") != 0 or
            result.get("boot_id") != boot or
            result.get("sense") != sense or
            result.get("internal_status") != "0x104" or
            result.get("module_released") is not True or
            result.get("flash_program_erase_commands") != 0 or
            status.get("done") != "1" or status.get("status") != "2" or
            status.get("residual") != "0" or
            int(status.get("sense_len", "0")) < 14 or
            len(sense) != 28 or not sense.endswith("8104")):
        raise ValueError("same-boot auto-sense proof is incomplete")
    return {"boot_id": boot, "sense_probe_module_sha256": SENSE_PROBE_MODULE_SHA,
            "internal_status": "0x104"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("module", "image", "stock0", "stock1", "stage", "readback", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--diagnostic-retry-proof", type=Path)
    parser.add_argument("--october-handler-proof", type=Path)
    parser.add_argument("--sense-proof", type=Path)
    parser.add_argument("--spare-bdf", choices=("0000:37:04.1", "0000:37:09.1"), default=SPARE)
    args = parser.parse_args()
    spare_bdf = args.spare_bdf
    peer_bdf = ORIGINAL if spare_bdf == SPARE else SPARE
    lock = open("/run/lock/i960-loadrun.lock", "w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if args.diagnostic_retry_proof and args.october_handler_proof:
        raise ValueError("choose one experimental flash mode")
    expected_flash_module = (DIAGNOSTIC_FLASH_MODULE_SHA if
                             (args.diagnostic_retry_proof or args.october_handler_proof)
                             else FLASH_MODULE_SHA)
    if args.module.name != "flash_image.ko" or hashlib.sha256(args.module.read_bytes()).hexdigest() != expected_flash_module:
        raise ValueError("wrong FLASHIMAGE module")
    image = args.image.read_bytes()
    boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    proof = verify_pair(image, (args.stock0, args.stock1), spare_bdf, boot)
    diagnostic = None
    october_test = None
    if args.diagnostic_retry_proof:
        if args.sense_proof is None:
            raise ValueError("diagnostic retry requires same-boot sense proof")
        if spare_bdf != "0000:37:09.1":
            raise ValueError("diagnostic retry is restricted to Slot 5")
        diagnostic = verify_diagnostic_retry(args.diagnostic_retry_proof, boot,
                                             proof["stock_sha256"], proof["candidate_sha256"])
        diagnostic["sense_probe"] = verify_sense_probe(args.sense_proof, boot)
        if (args.diagnostic_retry_proof / "diagnostic-flash-attempt.json").exists():
            raise RuntimeError("diagnostic FLASHIMAGE was already attempted; no retry")
    elif args.october_handler_proof:
        if spare_bdf != "0000:37:09.1" or args.sense_proof is None:
            raise ValueError("October comparison requires Slot 5 and same-boot sense proof")
        october_test = verify_october_handler_test(
            args.october_handler_proof, boot,
            proof["stock_sha256"], proof["candidate_sha256"])
        october_test["sense_probe"] = verify_sense_probe(args.sense_proof, boot)
    elif args.sense_proof is not None:
        raise ValueError("sense proof requires an experimental flash mode")
    if proof["candidate_sha256"] not in (SECOND_SPARE_PCI_RELEASE_SHA,
                                          SLOT5_LIVE_PCI_RELEASE_SHA,
                                          RESTORED_SLOT5_UPDATER_SHA,
                                          ORIGINAL_RAM_LOADER_SHA,
                                          SECOND_SPARE_RAM_LOADER_SHA,
                                          SECOND_SPARE_WRITER_SHA,
                                          SECOND_SPARE_OCTOBER_HANDLER_SHA,
                                          OCTOBER_CARD_CORRECTED_WRITER_SHA):
        raise ValueError("this flash command accepts only a pinned candidate")
    current_native = proof["candidate_sha256"] == OCTOBER_CARD_CORRECTED_WRITER_SHA
    if current_native and (spare_bdf != "0000:37:09.1" or
                           proof["stock_sha256"] != OCTOBER_CARD_INSTALLED_SHA or
                           CURRENT_NATIVE_ATTEMPT.exists()):
        raise ValueError("current native attempt requires the exact FI1 card and unused marker")
    spare = select(spare_bdf, "accele160", driver="myrsread")
    original = require_unbound_or_absent(peer_bdf, "accele160")
    if spare != proof["card"] or original["driver"] is not None:
        raise ValueError("live card identity changed")
    if Path("/sys/module/myrsread/parameters/read_bdf").read_text().strip() != spare_bdf:
        raise ValueError("read driver is not restricted to the spare")
    if DEBUG.exists() or Path("/sys/module/flash_image").exists():
        raise ValueError("previous flash command present")
    if (Path("/sys/kernel/debug/accele-senseprobe").exists() or
            Path("/sys/module/sense_probe").exists()):
        raise ValueError("sense probe still present")
    for name in ("accele-readimage", "accele-rawreadimage", "accele-stageimage"):
        if (Path("/sys/kernel/debug") / name).exists():
            raise ValueError(f"other image command still present: {name}")
    for bdf in (spare_bdf, peer_bdf):
        if list((Path("/sys/bus/pci/devices") / bdf).glob("host*/target*/*/block/*")):
            raise ValueError(f"{bdf} exposes storage")
    host, = (Path("/sys/bus/pci/devices") / spare_bdf).glob("host*/scsi_host/host*")
    if not (host / "stock_descriptor").read_text().startswith("state=0 "):
        raise ValueError("descriptor job is not idle")
    stage_request = json.loads((args.stage / "request.json").read_text())
    stage_result = json.loads((args.stage / "result.json").read_text())
    stage_status = fields(args.stage / "status.txt")
    read_request = json.loads((args.readback / "request.json").read_text())
    read_result = json.loads((args.readback / "result.json").read_text())
    read_status = fields(args.readback / "status.txt")
    read_data = (args.readback / "data.bin").read_bytes()
    if (stage_request.get("boot_id") != boot or stage_request.get("card") != spare or
            stage_request.get("original_card") != original or
            stage_request.get("candidate_sha256") != proof["candidate_sha256"] or
            stage_request.get("module_sha256") != STAGE_MODULE_SHA or
            stage_request.get("stock_preflight") != proof or
            stage_request.get("command") != "STOREIMAGE 0x2c" or
            stage_request.get("selector") != 9 or stage_request.get("offset_kib") != 0 or
            stage_request.get("bytes") != FLASH_SIZE or
            stage_result.get("stage_completed") is not True or
            stage_result.get("flash_command_issued") is not False or
            stage_result.get("card_after") != spare or
            stage_result.get("original_after") != original or
            any(stage_status.get(k) != v for k, v in {
                "written": str(FLASH_SIZE), "started": "1", "done": "1",
                "status": "0", "residual": "0", "guard_changes": "0"}.items()) or
            read_request.get("boot_id") != boot or read_request.get("card") != spare or
            read_request.get("original_card") != original or
            read_request.get("module_sha256") != READER_MODULE_SHA or
            read_request.get("selector") != 9 or read_request.get("length") != FLASH_SIZE or
            read_result.get("bytes") != FLASH_SIZE or
            read_result.get("sha256") != proof["candidate_sha256"] or
            read_result.get("card_after") != spare or
            read_result.get("original_after") != original or
            any(read_status.get(k) != v for k, v in {
                "done": "1", "status": "0", "residual": "0",
                "guard_changes": "0", "selector": "9",
                "length": str(FLASH_SIZE)}.items()) or
            len(read_data) != FLASH_SIZE or read_data != image):
        raise ValueError("same-boot stage and independent readback proof incomplete")
    record = {
        "boot_id": boot, "card": spare, "original_card": original,
        "stock_sha256": proof["stock_sha256"],
        "candidate_sha256": proof["candidate_sha256"],
        "flash_module_sha256": expected_flash_module,
        "diagnostic_retry_proof": diagnostic,
        "october_handler_test": october_test,
        "current_native_one_shot": current_native,
        "stage_dir": str(args.stage), "readback_dir": str(args.readback),
        "command": "FLASHIMAGE 0x2e selector 9 zero DMA",
    }
    if args.preflight_only:
        print(json.dumps(record, indent=2))
        return
    if proof["stock_sha256"] == REJECTED_STOCK_SHA and diagnostic is None and october_test is None:
        raise RuntimeError(
            "FLASHIMAGE is quarantined for this stock card: the identical "
            "staged/readback-verified request returned immediate status 2 on "
            "2026-11-20; diagnose the card-specific rejection before retrying")
    attempt_marker = (args.diagnostic_retry_proof / "diagnostic-flash-attempt.json"
                      if diagnostic is not None else
                      args.october_handler_proof / "october-handler-attempt.json"
                      if october_test is not None else
                      CURRENT_NATIVE_ATTEMPT if current_native else None)
    args.out.mkdir(parents=True, exist_ok=False)
    with (args.out / "preflight.json").open("w") as output:
        json.dump(record, output, indent=2)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())
    if attempt_marker is not None:
        marker_fd = os.open(attempt_marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(marker_fd, "w") as marker:
            json.dump(record, marker, indent=2)
            marker.write("\n")
            marker.flush()
            os.fsync(marker.fileno())
    subprocess.run(["insmod", str(args.module), "bdf=" + spare_bdf], check=True)
    if fields(DEBUG / "status").get("started") != "0":
        raise RuntimeError("unexpected flash module state; no command issued")
    (DEBUG / "start").write_text("FLASHIMAGE selector=9\n")
    start = time.monotonic()
    while True:
        status = fields(DEBUG / "status")
        if status.get("done") == "1" or time.monotonic() - start > 120:
            break
        time.sleep(0.1)
    (args.out / "status.txt").write_text((DEBUG / "status").read_text())
    if status.get("done") != "1":
        raise RuntimeError("FLASHIMAGE pending; keep module and driver loaded")
    if status.get("status") != "0" or status.get("residual") != "0":
        raise RuntimeError("FLASHIMAGE failed; retain module for inspection")
    (DEBUG / "release").write_text("release\n")
    subprocess.run(["rmmod", "flash_image"], check=True)
    (args.out / "result.json").write_text(json.dumps({
        "command_completed": True, "elapsed_s": time.monotonic() - start,
        "status": status, "card_after": select(spare_bdf, "accele160"),
        "original_after": require_unbound_or_absent(peer_bdf, "accele160"),
        "post_cold_boot_full_readback_required": True,
    }, indent=2) + "\n")
    print(args.out / "result.json")


if __name__ == "__main__":
    main()

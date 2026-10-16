#!/usr/bin/env python3
"""Replay the compact post-boot AcceleRAID RAM-call evidence offline."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

CANDIDATE = "1f13799b880d7e3de2c2037c44fff7e78c0a8f3f391cd05df4a67c41f36c4aaf"
PROBE = "5d86878199ddcdd7f7ea950699a8e047f4189eb264c1dcff860ee6f83e0e740c"
RESULT = (0x444F4E45, 0x16102671, 496, 0x80114670)
CARD = {"bdf": "0000:37:09.1", "profile": "accele160",
        "ids": [4201, 80, 4201, 84], "driver": "myrsread"}
OLD = {"bdf": "0000:37:04.1", "profile": "dac960pg",
       "ids": [4201, 16, 4201, 16], "driver": None}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text())


def status(path):
    return dict(part.split("=", 1) for part in path.read_text().split())


def verify(root: Path, probe_path: Path):
    image = (root / "candidate.bin").read_bytes()
    probe = probe_path.read_bytes()
    require(len(image) == 1048576 and sha(image) == CANDIDATE, "candidate image")
    require(len(probe) == 80 and sha(probe) == PROBE, "probe image")
    live = root / "live"
    initial = (root / "loader-f000-before.bin").read_bytes()
    require(len(initial) == 4096 and initial == image[0x46000:0x47000],
            "loader page versus programmed image")
    boot = None
    for name in ("persistent-0", "persistent-1", "postcall-flash"):
        p = live / name
        req, result, s = load(p / "request.json"), load(p / "result.json"), status(p / "status.txt")
        require(req["card"] == CARD and req["selector"] == 9 and
                req["length"] == len(image), name + " request")
        if boot is None:
            boot = req["boot_id"]
        require(req["boot_id"] == boot, name + " boot")
        require(result["bytes"] == len(image) and result["sha256"] == CANDIDATE and
                result["card_after"] == CARD and result["old_after"] == OLD,
                name + " result")
        require(all(s.get(k) == "0" for k in ("status", "residual", "guard_changes")) and
                s.get("done") == "1" and s.get("length") == str(len(image)),
                name + " DMA status")
    for name, expected in (("ping-0.txt", "0"), ("ping-1.txt", "2")):
        s = status(live / "ping-pair" / name)
        require(s.get("started") == "1" and s.get("done") == "1" and
                s.get("status") == expected and s.get("residual") == "0",
                name + " PING status")
    for n in (0, 1):
        p = live / f"ram-call-{n}"
        pre, result, s = load(p / "preflight.json"), load(p / "result.json"), status(p / "command-status.txt")
        require(pre["boot_id"] == boot and pre["card"] == CARD and
                pre["old_card"] == OLD and pre["candidate_sha256"] == CANDIDATE and
                pre["probe_sha256"] == PROBE, f"call {n} preflight")
        require(result["returncode"] == 0 and result["card_after"] == CARD and
                result["old_after"] == OLD and result["command"] == s,
                f"call {n} result")
        require(all(s.get(k) == "1" for k in ("started", "done", "released")) and
                s.get("status") == "0" and s.get("residual") == "0",
                f"call {n} command status")
        before = (p / "page-before.bin").read_bytes()
        after = (p / "page-after-call.bin").read_bytes()
        require(before == initial and len(after) == len(initial), f"call {n} page preimage")
        require(after[0x900:0x950] == probe and
                struct.unpack_from("<4I", after, 0x800) == RESULT,
                f"call {n} code/result")
        require(all(a == b for i, (a, b) in enumerate(zip(before, after))
                    if not (0x800 <= i < 0x810 or 0x900 <= i < 0x950)),
                f"call {n} page outside slots")
        log = (p / "session.txt").read_text()
        require("command_status=0 residual=0" in log and
                "result=444f4e45,16102671,000001f0,80114670 verified=1" in log and
                "full_page_restored=1 PIATVR=c0000000 released=1" in log,
                f"call {n} session")
    require((live / "final-f000.bin").read_bytes() == initial,
            "independent final loader-page restoration")
    survey = live / "dram-survey-0"
    require((survey / "boot-id.txt").read_text().strip() == boot, "survey boot")
    recorded = {name: digest for digest, name in re.findall(
        r"^([a-f0-9]{64})\s+\S*/(c[0-9a-f]+-[01]\.bin)$",
        (survey / "sha256.txt").read_text(), re.M)}
    # The full hash list proves these are two rounds, while the retained runtime
    # sample supports independent byte-level replay without archiving zeros.
    for base in ("c0010000", "c0500000", "c0800000", "c0c00000", "c0f00000"):
        for n in (0, 1):
            require(f"{base}-{n}.bin" in recorded, "survey sample missing")
    runtime = (survey / "c0010000-0.bin").read_bytes()
    require(len(runtime) == 4096 and sha(runtime) == recorded["c0010000-0.bin"] and
            any(runtime), "runtime survey sample")
    zero_sha = sha(bytes(4096))
    require(all(recorded[f"{base}-{n}.bin"] == zero_sha
                for base in ("c0500000", "c0800000", "c0c00000", "c0f00000")
                for n in (0, 1)), "high survey hashes")
    return {"boot_id": boot, "full_flash_audits": 3, "normal_ram_calls": 2,
            "independent_final_page_match": True, "survey_pages": 10}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("probe", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.root, args.probe), indent=2))


if __name__ == "__main__":
    main()

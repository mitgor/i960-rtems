#!/usr/bin/env python3
"""Replay the exact patched-flash acceptance evidence without card access."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "helper"))
from export_late_ping import export_image


EXPECTED = "e708c1dadbc4813dd378e8ca8c6f0e929cc29064614b9f8a27210e5e2b23d3d0"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def status(path: Path) -> dict[str, str]:
    return dict(x.split("=", 1) for x in path.read_text().split())


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def require(condition: bool, description: str) -> None:
    if not condition:
        raise ValueError(f"flash acceptance failed: {description}")


def verify(root: Path, stock: Path, handler: Path, callsite: Path) -> dict:
    image, audit = export_image(stock.read_bytes(), handler.read_bytes(),
                                callsite.read_bytes())
    require(digest(image) == EXPECTED, "audited image hash")
    require((root / "candidate.bin").read_bytes() == image, "candidate bytes")
    stage = read_json(root / "live-stage/request.json")
    stage_result = read_json(root / "live-stage/result.json")
    stage_status = status(root / "live-stage/status.txt")
    flash = read_json(root / "live-flash/preflight.json")
    flash_result = read_json(root / "live-flash/result.json")
    flash_status = status(root / "live-flash/status.txt")
    require(stage["boot_id"] == flash["boot_id"], "stage/flash boot identity")
    require(stage["image_sha256"] == flash["image_sha256"] == EXPECTED,
            "stage/flash image identity")
    require(stage["selector"] == 9 and stage["offset_kib"] == 0 and
            stage["bytes"] == 1048576, "stage bounds")
    require(stage_result["stage_completed"] and
            stage_result["flash_command_issued"] is False, "stage completion")
    require(all(stage_status[k] == "0" for k in
                ("status", "residual", "guard_changes")), "stage audit")
    require(flash_result["command_completed"], "flash completion")
    require(all(flash_status[k] == "0" for k in ("status", "residual")),
            "flash result")
    require(flash["card"]["bdf"] == "0000:37:09.1" and
            flash["old_card"]["bdf"] == "0000:37:04.1" and
            flash["old_card"]["driver"] is None, "PCI ownership")
    reads = []
    for name in ("live-readback", "persistent-0", "persistent-1"):
        request = read_json(root / name / "request.json")
        result = read_json(root / name / "result.json")
        read_status = status(root / name / "status.txt")
        require(request["selector"] == 9 and request["length"] == 1048576,
                f"{name} bounds")
        require(result["bytes"] == 1048576 and result["sha256"] == EXPECTED,
                f"{name} hash")
        require(all(read_status[k] == "0" for k in
                    ("status", "residual", "guard_changes")), f"{name} audit")
        require(result["card_after"]["bdf"] == "0000:37:09.1" and
                result["old_after"]["driver"] is None, f"{name} ownership")
        if name != "live-readback":
            require((root / name / "data.bin").read_bytes() == image,
                    f"{name} full bytes")
        reads.append((name, request["boot_id"]))
    require(reads[0][1] == stage["boot_id"] and
            reads[1][1] == reads[2][1] != stage["boot_id"], "fresh-boot reads")
    ping = status(root / "ping-valid.txt")
    bad = status(root / "ping-bad-signature.txt")
    a, b = bytes.fromhex(ping["mailbox"]), bytes.fromhex(bad["mailbox"])
    require(len(a) == len(b) == 64, "PING mailbox lengths")
    require(ping["status"] == "0" and bad["status"] == "2" and
            ping["residual"] == bad["residual"] == "0", "PING status pair")
    require(ping["bad_signature"] == "0" and bad["bad_signature"] == "1",
            "PING test modes")
    require(a[:24] == b[:24] and a[24] == ord("I") and b[24] == ord("H") and
            a[25:] == b[25:], "PING single-byte mutation")
    require(a[2:4] == b"\x20\x40" and a[21:24] == b"\x8f\x01\x01" and
            a[28:32] != b"\x00" * 4 and a[32:] == b"\x00" * 32,
            "PING envelope")
    return {"image_sha256": EXPECTED,
            "changed_flash_bytes": audit["changed_flash_bytes"],
            "stage_boot_id": stage["boot_id"],
            "persistent_boot_id": reads[1][1],
            "paired_full_flash_equal": True,
            "paired_guard_changes": 0,
            "valid_ping_status": 0, "bad_signature_status": 2,
            "old_card_unbound": True}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    p.add_argument("stock", type=Path)
    p.add_argument("handler", type=Path)
    p.add_argument("callsite", type=Path)
    a = p.parse_args()
    print(json.dumps(verify(a.root, a.stock, a.handler, a.callsite), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Read-only integrity gate for a second-spare native diagnostic ROM package."""

import argparse
import hashlib
import json
from pathlib import Path

from pack import build


ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "artifacts/current"
FIRST = ART / "accele160-spare-rom-20261025"
SECOND = ART / "accele160-second-spare-20261026"
FIRST_STOCK_SHA = "fadd2b0f6ed9bb88d7c846edd235e5e222cbe3a990b694115c5fa66170e7a816"
FIRST_FAILED_SHA = "6f16d71310d75937b5f3961b1faae81eab3258a29371c8505d788c50c545e3bd"
SECOND_STOCK_SHA = "0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943"
FLASH_SIZE = 0x100000


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked(path, expected):
    data = path.read_bytes()
    actual = digest(data)
    if len(data) != FLASH_SIZE or actual != expected:
        raise ValueError(f"{path}: expected 1 MiB SHA-256 {expected}, got {len(data)} {actual}")
    return data


def identity(paths, expected):
    files = [checked(path, expected) for path in paths]
    if any(data != files[0] for data in files[1:]):
        raise ValueError("saved same-card reads disagree")
    return files[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--stage2", type=Path, required=True)
    parser.add_argument("--rtems", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source", type=Path, action="append", default=[],
                        help="additional source or tool path to hash in receipt")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)

    first_stock = identity([
        FIRST / "rawflash-0/data.bin", FIRST / "rawflash-1/data.bin",
        FIRST / "restore-first-spare-stock-1MiB.bin"], FIRST_STOCK_SHA)
    identity([
        FIRST / "native-rom-spare-prototype.bin",
        FIRST / "programmer-read-0.bin"], FIRST_FAILED_SHA)
    second_stock = identity([
        SECOND / "rawflash-0/data.bin", SECOND / "rawflash-1/data.bin"],
        SECOND_STOCK_SHA)
    if first_stock == second_stock:
        raise ValueError("first and second spare stock dumps unexpectedly identical")
    stock_delta = [i for i, (a, b) in enumerate(zip(first_stock, second_stock))
                   if a != b]
    if not stock_delta or any(not 0xe0000 <= i < 0xf0000 for i in stock_delta):
        raise ValueError("card-specific stock difference escaped descriptor region")

    stage2 = args.stage2.read_bytes()
    rtems = args.rtems.read_bytes()
    recomposed, pack_receipt = build(second_stock, stage2, rtems)
    candidate = args.candidate.read_bytes()
    if candidate != recomposed:
        raise ValueError("candidate is not byte-for-byte pack.build output")
    changed = [i for i, (a, b) in enumerate(zip(second_stock, candidate)) if a != b]
    if not changed or any(not 0x40000 <= i < 0xc0000 for i in changed):
        raise ValueError("candidate changes escape main firmware region")
    if candidate[0xe0000:0xf0000] != second_stock[0xe0000:0xf0000]:
        raise ValueError("second-spare descriptor changed")
    source_dir = Path(__file__).parent
    sources = [source_dir / name for name in (
        "verify_diagnostic_package.py", "pack.py", "build.sh", "app.c",
        "start.S", "stage2.c", "stage2_start.S", "host_startup.c",
        "host_mailbox.c", "controller_info.c", "link.ld", "stage2.ld")]
    sources.extend([ROOT / "rtems/sources.json",
                    ROOT / "artifacts/toolchain-20261011/linux-x86_64-installed.tar.xz"])
    sources.extend(args.source)
    manifest = {}
    for path in sources:
        resolved = path.resolve()
        manifest[str(resolved)] = digest(resolved.read_bytes())

    result = {
        "gate": "PASS", "scope": "offline package identity; no emulator or hardware test",
        "first_spare_recovery_sha256": FIRST_STOCK_SHA,
        "first_spare_failed_and_programmer_read_sha256": FIRST_FAILED_SHA,
        "first_spare_stock_bytes_differing_from_second": len(stock_delta),
        "second_spare_stock_sha256": SECOND_STOCK_SHA,
        "candidate_sha256": digest(candidate),
        "candidate_bytes_differing_from_second_stock": len(changed),
        "changed_first": min(changed), "changed_last": max(changed),
        "stock_reset_block_unchanged": candidate[0xf0000:] == second_stock[0xf0000:],
        "stock_x86_option_rom_unchanged": candidate[:0x40000] == second_stock[:0x40000],
        "second_spare_descriptor_unchanged": True,
        "packer": pack_receipt, "source_sha256": manifest,
        "physical_card_tested": False, "safe_to_flash": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print("diagnostic_package=PASS candidate=" + result["candidate_sha256"])


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Read-only audit of pinned first-spare recovery and second-spare images."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "artifacts/current"
FIRST = ART / "accele160-spare-rom-20261025"
SECOND = ART / "accele160-second-spare-20261026"
CANDIDATE = ART / "accele160-native-ioctl2d-20261116/native-five-replies-second-spare.bin"
FIRST_STOCK = "fadd2b0f6ed9bb88d7c846edd235e5e222cbe3a990b694115c5fa66170e7a816"
FIRST_FAILED = "6f16d71310d75937b5f3961b1faae81eab3258a29371c8505d788c50c545e3bd"
SECOND_STOCK = "0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943"
SECOND_CANDIDATE = "6432d1ff7647d74ff2e4b12fb8d3d40c7323bd5eff618c80be290206338a8f4e"
FLASH_BYTES = 1048576


def load(path, expected):
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if len(data) != FLASH_BYTES or digest != expected:
        raise ValueError(f"{path}: expected 1 MiB SHA-256 {expected}, got {len(data)} {digest}")
    return data


def differences(a, b):
    return [i for i, (x, y) in enumerate(zip(a, b)) if x != y]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    first0 = load(FIRST / "rawflash-0/data.bin", FIRST_STOCK)
    first1 = load(FIRST / "rawflash-1/data.bin", FIRST_STOCK)
    recovery = load(FIRST / "restore-first-spare-stock-1MiB.bin", FIRST_STOCK)
    failed = load(FIRST / "native-rom-spare-prototype.bin", FIRST_FAILED)
    programmer = load(FIRST / "programmer-read-0.bin", FIRST_FAILED)
    second0 = load(SECOND / "rawflash-0/data.bin", SECOND_STOCK)
    second1 = load(SECOND / "rawflash-1/data.bin", SECOND_STOCK)
    candidate = load(CANDIDATE, SECOND_CANDIDATE)
    if not (first0 == first1 == recovery and failed == programmer and
            second0 == second1):
        raise ValueError("duplicate read or recovery image differs")
    stock_delta = differences(first0, second0)
    candidate_delta = differences(second0, candidate)
    if (not stock_delta or not all(0xe0000 <= x < 0xf0000 for x in stock_delta) or
            not candidate_delta or not all(0x40000 <= x < 0xc0000 for x in candidate_delta)):
        raise ValueError("card descriptor or candidate region policy violated")
    result = {
        "gate": "PASS", "flash_bytes": FLASH_BYTES,
        "first_spare_stock_sha256": FIRST_STOCK,
        "first_spare_failed_sha256": FIRST_FAILED,
        "first_spare_programmer_read_matches_failed": True,
        "first_spare_recovery_matches_two_stock_reads": True,
        "second_spare_stock_sha256": SECOND_STOCK,
        "second_spare_two_stock_reads_match": True,
        "second_spare_candidate_sha256": SECOND_CANDIDATE,
        "stock_cards_differing_bytes": len(stock_delta),
        "stock_cards_difference_region": "0xe0000..0xeffff",
        "candidate_differing_bytes": len(candidate_delta),
        "candidate_difference_region": "0x40000..0xbffff",
        "programmer_profile_verified": False,
        "physical_restore_tested": False,
        "safe_to_flash": False,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"recovery_image_audit=PASS first_stock={FIRST_STOCK} second_stock={SECOND_STOCK}")


if __name__ == "__main__":
    main()

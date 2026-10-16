#!/usr/bin/env python3
"""Pin DACFL6's STOREIMAGE and FLASHIMAGE mailbox construction offline."""

import argparse
import hashlib
import json
from pathlib import Path


ANCHORS = {
    "store_entry": (0x9249, "c8580000"),
    "store_dma_size": (0x92CC, "668b46126626894704"),
    "store_selector": (0x92FC, "8a462226884714"),
    "store_subcommand_2c": (0x9306, "26c647152c"),
    "store_dma_addr": (0x930E, "668b460e6626894720"),
    "store_dma_count": (0x9326, "668b46126626894728"),
    "store_offset_word": (0x936B, "c45ef08b461626894710"),
    "flash_entry": (0x94EF, "c8580000"),
    "flash_zero_dma_size": (0x956F, "c45eec6626c7470400000000"),
    "flash_subcommand_2e": (0x95AC, "26c647152e"),
}


def audit(data: bytes, expected_sha: str) -> dict:
    digest = hashlib.sha256(data).hexdigest()
    checks = {name: data[at:at + len(bytes.fromhex(raw))] == bytes.fromhex(raw)
              for name, (at, raw) in ANCHORS.items()}
    return {"sha256": digest, "known_vendor_binary": digest == expected_sha,
            "anchors": checks, "all_anchors_match": all(checks.values())}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vendor_exe", type=Path)
    parser.add_argument("provenance", type=Path)
    args = parser.parse_args()
    expected = json.loads(args.provenance.read_text())["decoded_dacfl6_sha256"]
    result = audit(args.vendor_exe.read_bytes(), expected)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["known_vendor_binary"] and result["all_anchors_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

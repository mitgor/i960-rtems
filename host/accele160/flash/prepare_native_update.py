#!/usr/bin/env python3
"""Prepare a native-updater manifest from two complete local images; no PCI I/O."""
import argparse
import hashlib
import json
from pathlib import Path

IMAGE_BYTES = 0x100000
CHUNK_BYTES = 4096
MUTABLE_FIRST = 0x40000
MUTABLE_END = 0xC0000
BLOCK_BYTES = 0x10000


def fnv32(data: bytes) -> int:
    value = 2166136261
    for byte in data:
        value = ((value ^ byte) * 16777619) & 0xFFFFFFFF
    return value


def prepare(base: bytes, target: bytes) -> dict:
    if len(base) != IMAGE_BYTES or len(target) != IMAGE_BYTES:
        raise ValueError("base and target must each be exactly 1 MiB")
    if base[:MUTABLE_FIRST] != target[:MUTABLE_FIRST]:
        raise ValueError("reset and x86 ROM region changed")
    if base[MUTABLE_END:] != target[MUTABLE_END:]:
        raise ValueError("descriptor or other protected region changed")
    changed = [offset for offset in range(MUTABLE_FIRST, MUTABLE_END, BLOCK_BYTES)
               if base[offset:offset + BLOCK_BYTES] != target[offset:offset + BLOCK_BYTES]]
    return {
        "format": "accele160-native-update-v1",
        "image_bytes": IMAGE_BYTES,
        "chunk_bytes": CHUNK_BYTES,
        "base_sha256": hashlib.sha256(base).hexdigest(),
        "target_sha256": hashlib.sha256(target).hexdigest(),
        "changed_64k_blocks": [f"0x{offset:05x}" for offset in changed],
        "chunks_fnv32": [f"0x{fnv32(target[offset:offset + CHUNK_BYTES]):08x}"
                         for offset in range(0, IMAGE_BYTES, CHUNK_BYTES)],
        "hardware_write_qualified": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=Path, help="current card's exact 1 MiB image")
    parser.add_argument("target", type=Path, help="card-specific target image")
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    if args.manifest.exists():
        raise FileExistsError(args.manifest)
    manifest = prepare(args.base.read_bytes(), args.target.read_bytes())
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    print(args.manifest)


if __name__ == "__main__":
    main()

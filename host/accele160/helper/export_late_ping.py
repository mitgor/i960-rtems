#!/usr/bin/env python3
"""Export the exact audited AcceleRAID 160 candidate; never contact hardware."""

import argparse
import hashlib
import json
from pathlib import Path
import struct

from audit_late_ping import audit, CAVE, LOADER_BASE, LOADER_RETURN
from audit_dispatch_rehearsal import analyze


def export_image(flash: bytes, handler: bytes, callsite: bytes) -> tuple[bytes, dict]:
    receipt = audit(flash, handler, callsite)
    stock = analyze(flash)
    base = stock["loader"]["flash_offset"]
    size = stock["loader"]["size"]
    trailer = stock["trailer_offset"]
    site = base + LOADER_RETURN - LOADER_BASE
    cave = base + CAVE - LOADER_BASE
    candidate = bytearray(flash)
    candidate[site:site + len(callsite)] = callsite
    candidate[cave:cave + len(handler)] = handler
    checksum = sum(struct.unpack_from(f"<{size // 4}I", candidate, base)) & 0xFFFFFFFF
    struct.pack_into("<I", candidate, trailer + 24, checksum)
    trailer_sum = sum(struct.unpack_from("<31I", candidate, trailer)) & 0xFFFFFFFF
    struct.pack_into("<I", candidate, trailer + 124, trailer_sum)
    digest = hashlib.sha256(candidate).hexdigest()
    if (len(candidate) != 0x100000 or digest != receipt["in_memory_candidate_sha256"]
            or checksum != int(receipt["loader_checksum"], 16)
            or trailer_sum != int(receipt["trailer_checksum"], 16)):
        raise ValueError("export differs from audited candidate")
    return bytes(candidate), receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("flash", type=Path)
    parser.add_argument("handler", type=Path)
    parser.add_argument("callsite", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    image, receipt = export_image(args.flash.read_bytes(), args.handler.read_bytes(),
                                  args.callsite.read_bytes())
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.write_bytes(image)
    print(json.dumps({**receipt, "exported_path": str(args.output),
                      "image_written": True, "card_executed": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

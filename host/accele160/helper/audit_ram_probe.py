#!/usr/bin/env python3
"""Build/audit the exact AcceleRAID 160 RAM-call candidate offline."""

import argparse
import hashlib
import json
from pathlib import Path
import struct

from audit_dispatch_rehearsal import analyze
from audit_late_ping import audit as audit_original, CAVE, LOADER_BASE, LOADER_RETURN

ORIGINAL_SHA = "e708c1dadbc4813dd378e8ca8c6f0e929cc29064614b9f8a27210e5e2b23d3d0"
CANDIDATE_SHA = "1f13799b880d7e3de2c2037c44fff7e78c0a8f3f391cd05df4a67c41f36c4aaf"
HANDLER_SHA = "f4b9c126739878cf725ffe9ca0f58b5610c852efcc35c4adfa3cd8c87c4f5202"
PROBE_SHA = "5d86878199ddcdd7f7ea950699a8e047f4189eb264c1dcff860ee6f83e0e740c"
HANDLER_SIZE = 412
PROBE_OFFSET = 0x14c


def make(stock: bytes, original: bytes, old_handler: bytes, branch: bytes,
         new_handler: bytes, probe: bytes) -> tuple[bytes, dict]:
    audit_original(stock, old_handler, branch)
    if len(original) != 0x100000 or hashlib.sha256(original).hexdigest() != ORIGINAL_SHA:
        raise ValueError("requires the exact programmed late-PING image")
    if (len(new_handler) != HANDLER_SIZE or
            hashlib.sha256(new_handler).hexdigest() != HANDLER_SHA or
            hashlib.sha256(probe).hexdigest() != PROBE_SHA or
            len(probe) != 80 or
            new_handler[PROBE_OFFSET:PROBE_OFFSET + 80] != probe):
        raise ValueError("unreviewed RAM-call handler or executable probe")
    info = analyze(stock)
    base, size, trailer = (info["loader"]["flash_offset"],
                           info["loader"]["size"], info["trailer_offset"])
    site = base + LOADER_RETURN - LOADER_BASE
    cave = base + CAVE - LOADER_BASE
    if original[site:site + 4] != branch or original[cave:cave + len(old_handler)] != old_handler:
        raise ValueError("programmed image does not match the reviewed hook")
    if original[cave + len(old_handler):cave + len(new_handler)] != b"\xff" * (len(new_handler) - len(old_handler)):
        raise ValueError("extension overwrites occupied cave bytes")
    image = bytearray(original)
    image[cave:cave + len(new_handler)] = new_handler
    checksum = sum(struct.unpack_from(f"<{size // 4}I", image, base)) & 0xffffffff
    struct.pack_into("<I", image, trailer + 24, checksum)
    trailer_sum = sum(struct.unpack_from("<31I", image, trailer)) & 0xffffffff
    struct.pack_into("<I", image, trailer + 124, trailer_sum)
    checked = analyze(image)
    changed = {i for i, (a, b) in enumerate(zip(original, image)) if a != b}
    allowed = (set(range(cave, cave + len(new_handler))) |
               set(range(trailer + 24, trailer + 28)) |
               set(range(trailer + 124, trailer + 128)))
    if (not changed <= allowed or checked["runtime"] != info["runtime"] or
            not checked["loader"]["checksum_passed"] or
            not checked["trailer_checksum_passed"] or
            image[0xf0000:] != original[0xf0000:] or
            image[site:site + 4] != branch):
        raise ValueError("unexpected flash delta or invalid structure")
    if hashlib.sha256(image).hexdigest() != CANDIDATE_SHA:
        raise ValueError("candidate differs from the pinned image")
    return bytes(image), dict(
        original_sha256=ORIGINAL_SHA,
        candidate_sha256=hashlib.sha256(image).hexdigest(),
        handler_sha256=HANDLER_SHA,
        probe_sha256=PROBE_SHA,
        changed_bytes=len(changed),
        changed_offsets=[hex(min(changed)), hex(max(changed))],
        loader_checksum=f"0x{checksum:08x}",
        trailer_checksum=f"0x{trailer_sum:08x}",
        runtime_sha256=checked["runtime"]["sha256"],
        boot_block_unchanged=True,
        flash_written=False,
        card_executed=False,
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("stock", "original", "old_handler", "branch", "new_handler", "probe", "output"):
        p.add_argument(name, type=Path)
    a = p.parse_args()
    image, result = make(*(getattr(a, name).read_bytes() for name in
                           ("stock", "original", "old_handler", "branch", "new_handler", "probe")))
    if a.output.exists():
        raise FileExistsError(a.output)
    a.output.write_bytes(image)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

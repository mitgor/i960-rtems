#!/usr/bin/env python3
"""Audit one exact AcceleRAID allocator-probe firmware extension offline."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "helper"))
from audit_late_ping import CAVE, LOADER_BASE, LOADER_RETURN
from audit_dispatch_rehearsal import analyze

STOCK_SHA = "0a951782a7ccd1855746ffeb3a1b64563287bc56e0dce77d63b79c71ec3b502a"
CURRENT_SHA = "e7a3a7c5b4dcbbd933813155f03544cc691dac7e7b63fade79255d2452d6ffc0"
OLD_HANDLER_SHA = "f134acc17d63a0a9ab9008dca63afa7a7d00ce611a044b02de54d8c86d83572c"
HANDLER_SHA = "d4fb53c0f6cd8985e9373435424981b00d93364d52006e3baa015ccc0daad537"
PROBE_SHA = "5d86878199ddcdd7f7ea950699a8e047f4189eb264c1dcff860ee6f83e0e740c"
EXPECTED_CANDIDATE_SHA = "183eed37b6a3764961e8f66fc9bda73ed7ed3547a7686bf605bcb2b6cd197f4a"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def make(stock: bytes, current: bytes, old_handler: bytes, handler: bytes, probe: bytes):
    if len(stock) != 1048576 or len(current) != len(stock):
        raise ValueError("full flash size")
    if sha(stock) != STOCK_SHA or sha(current) != CURRENT_SHA or sha(old_handler) != OLD_HANDLER_SHA or \
            sha(handler) != HANDLER_SHA or sha(probe) != PROBE_SHA:
        raise ValueError("unreviewed image or handler input")
    if len(handler) != 1512 or len(old_handler) != 1108 or len(probe) != 80 or \
            handler.count(probe) != 1:
        raise ValueError("handler or embedded exact probe size")
    info = analyze(stock)
    current_info = analyze(current)
    if (current_info["runtime"] != info["runtime"] or
            current[0xf0000:] != stock[0xf0000:]):
        raise ValueError("current image runtime or boot-block identity")
    base, size, trailer = (info["loader"]["flash_offset"],
                           info["loader"]["size"], info["trailer_offset"])
    cave = base + CAVE - LOADER_BASE
    hook = base + LOADER_RETURN - LOADER_BASE
    if current[cave:cave + len(old_handler)] != old_handler or \
            current[cave + len(old_handler):cave + len(handler)] != b"\xff" * (len(handler) - len(old_handler)):
        raise ValueError("existing hook or cave preimage")
    image = bytearray(current)
    image[cave:cave + len(handler)] = handler
    loader_sum = sum(struct.unpack_from(f"<{size // 4}I", image, base)) & 0xffffffff
    struct.pack_into("<I", image, trailer + 24, loader_sum)
    trailer_sum = sum(struct.unpack_from("<31I", image, trailer)) & 0xffffffff
    struct.pack_into("<I", image, trailer + 124, trailer_sum)
    checked = analyze(image)
    changed = {i for i, (before, after) in enumerate(zip(current, image)) if before != after}
    allowed = set(range(cave, cave + len(handler))) | \
        set(range(trailer + 24, trailer + 28)) | \
        set(range(trailer + 124, trailer + 128))
    if (not changed <= allowed or checked["runtime"] != info["runtime"] or
            not checked["loader"]["checksum_passed"] or
            not checked["trailer_checksum_passed"] or
            image[0xf0000:] != stock[0xf0000:] or image[hook:hook + 4] != current[hook:hook + 4]):
        raise ValueError("candidate altered runtime, hook, boot block or unrelated bytes")
    digest = sha(image)
    if digest != EXPECTED_CANDIDATE_SHA:
        raise ValueError("candidate differs from reviewed hash")
    return bytes(image), dict(current_sha256=CURRENT_SHA, handler_sha256=HANDLER_SHA,
                              candidate_sha256=digest, handler_bytes=len(handler),
                              changed_bytes=len(changed), loader_checksum=f"0x{loader_sum:08x}",
                              trailer_checksum=f"0x{trailer_sum:08x}",
                              runtime_unchanged=True, boot_block_unchanged=True,
                              flash_written=False, allocator_called=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("stock", "current", "old_handler", "handler", "probe", "output"):
        p.add_argument(name, type=Path)
    a = p.parse_args()
    image, receipt = make(*(getattr(a, name).read_bytes() for name in
                            ("stock", "current", "old_handler", "handler", "probe")))
    if a.output.exists():
        raise FileExistsError(a.output)
    a.output.write_bytes(image)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()

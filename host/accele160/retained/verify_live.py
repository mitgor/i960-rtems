#!/usr/bin/env python3
"""Offline replay of a bounded 512 KiB reserve/release card capture."""

import argparse
import hashlib
import json
from pathlib import Path
import struct

OWNER = 0x96016004
SIZE = 0x80000


def words(blob: bytes, offset: int) -> tuple[int, int, int, int]:
    return struct.unpack_from("<4I", blob, offset)


def verify(path: Path) -> dict:
    names = ("page-before", "page-reserved", "page-after", "table-before",
             "table-reserved", "table-after")
    data = {name: (path / f"{name}.bin").read_bytes() for name in names}
    if any(len(blob) != 4096 for blob in data.values()):
        raise ValueError("capture size")
    before, reserved, after = (data[name] for name in names[:3])
    tb, tr, ta = (data[name] for name in names[3:])
    if before != b"\xff" * 4096:
        raise ValueError("loader page preimage")
    if words(reserved, 0x820)[0:2] != (0x4f4c4c41, 0x16161041) or \
            words(reserved, 0x820)[3] != SIZE:
        raise ValueError("reserve result")
    ptr = words(reserved, 0x820)[2]
    if ptr < 0xc0618000 or ptr > 0xc0710000 or ptr & 0x7fff:
        raise ValueError("grant outside expected pool")
    if words(reserved, 0x840) != (0x56525352, ptr, SIZE, OWNER):
        raise ValueError("owner record")
    if words(after, 0x820) != (0x45455246, 0x16161051, ptr, SIZE) or \
            after[0x840:0x850] != before[0x840:0x850]:
        raise ValueError("release result or owner-record restoration")
    for frame in (reserved, after):
        allowed = set(range(0x820, 0x830))
        if frame is reserved:
            allowed.update(range(0x840, 0x850))
        if any(a != b and i not in allowed for i, (a, b) in enumerate(zip(before, frame))):
            raise ValueError("loader write outside result or record")
    first = (ptr - 0xc0000000) // 0x8000
    for i in range(256):
        bc = struct.unpack_from("<I", tb, 0x2a0 + i * 4)[0]
        bo = struct.unpack_from("<I", tb, 0x6a0 + i * 4)[0]
        rc = struct.unpack_from("<I", tr, 0x2a0 + i * 4)[0]
        ro = struct.unpack_from("<I", tr, 0x6a0 + i * 4)[0]
        ac = struct.unpack_from("<I", ta, 0x2a0 + i * 4)[0]
        ao = struct.unpack_from("<I", ta, 0x6a0 + i * 4)[0]
        if (ac, ao) != (bc, bo):
            raise ValueError("allocator metadata did not restore")
        expected = (16, OWNER) if first <= i < first + 16 else (bc, bo)
        if first <= i < first + 16 and (bc or bo):
            raise ValueError("grant overlapped stock owner")
        if (rc, ro) != expected:
            raise ValueError("grant metadata mismatch")
    for name in ("reserve", "release"):
        status = dict(item.split("=", 1) for item in
                      (path / f"{name}-status.txt").read_text().split())
        if any(status.get(key) != value for key, value in
               (("started", "1"), ("done", "1"), ("status", "0"),
                ("residual", "0"))):
            raise ValueError(f"{name} command failed")
    digest = hashlib.sha256(tb[0x2a0:0xaa0]).hexdigest()
    return dict(pointer=f"0x{ptr:08x}", bytes=SIZE,
                blocks=16, metadata_sha256=digest,
                reserve_and_release_passed=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("capture", type=Path)
    print(json.dumps(verify(p.parse_args().capture), indent=2))

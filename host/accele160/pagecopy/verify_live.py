#!/usr/bin/env python3
"""Offline replay of an owned staging-page to even-page card copy."""

import argparse
import importlib.util
import json
from pathlib import Path
import struct

_retained_path = Path(__file__).resolve().parents[1] / "retained/verify_live.py"
_spec = importlib.util.spec_from_file_location("accele_retained_replay", _retained_path)
_retained = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_retained)
verify_grant = _retained.verify


def fnv(blob: bytes) -> int:
    value = 0x811c9dc5
    for byte in blob:
        value = ((value ^ byte) * 0x01000193) & 0xffffffff
    return value


def verify(path: Path) -> dict:
    result = verify_grant(path)
    before = (path / "staging-before.bin").read_bytes()
    pattern = (path / "staging-pattern.bin").read_bytes()
    readback = (path / "staging-readback.bin").read_bytes()
    restored = (path / "staging-restored.bin").read_bytes()
    page_before = (path / "page-before.bin").read_bytes()
    page_reserved = (path / "page-reserved.bin").read_bytes()
    page_copied = (path / "page-copied.bin").read_bytes()
    index = struct.unpack_from("<I", page_copied, 0x828)[0]
    if index > 126:
        raise ValueError("target index outside grant payload")
    expected = bytes(((i * 53 + 0x96 + index) ^ (i >> 3)) & 0xff for i in range(4096))
    if any(len(blob) != 4096 for blob in
           (before, pattern, readback, restored, page_before, page_reserved, page_copied)):
        raise ValueError("capture size")
    digest = fnv(pattern)
    if pattern != expected or readback != pattern or restored != before:
        raise ValueError("staging pattern, readback or restoration")
    if struct.unpack_from("<4I", page_copied, 0x820) != \
            (0x59504f43, 0x16161061, index, digest):
        raise ValueError("card-side copy result")
    if struct.unpack_from("<4I", page_copied, 0x860) != \
            (0x59504f43, 0x16161061, index, digest):
        raise ValueError("copy control record")
    expected_page = bytearray(page_reserved)
    expected_page[0x820:0x830] = page_copied[0x820:0x830]
    expected_page[0x860:0x870] = page_copied[0x860:0x870]
    if page_copied != expected_page or page_before[0x860:0x870] != b"\xff" * 16:
        raise ValueError("copy modified loader page outside result/control")
    status = dict(item.split("=", 1) for item in (path / "copy-status.txt").read_text().split())
    if any(status.get(k) != v for k, v in
           (("started", "1"), ("done", "1"), ("status", "0"), ("residual", "0"))):
        raise ValueError("copy command status")
    if index & 1:
        target_before = (path / "target-before.bin").read_bytes()
        target_after = (path / "target-after.bin").read_bytes()
        if len(target_before) != 4096 or target_after != pattern:
            raise ValueError("independent odd-target readback")
    result.update(staging_page=f"0x{int(result['pointer'], 16) + 0x7f000:08x}",
                  target_page=f"0x{int(result['pointer'], 16) + index * 4096:08x}",
                  target_index=index, copied_bytes=4096,
                  destination_fnv=f"0x{digest:08x}",
                  independent_odd_target_readback=bool(index & 1),
                  host_staging_restored=True)
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("capture", type=Path)
    print(json.dumps(verify(p.parse_args().capture), indent=2))

#!/usr/bin/env python3
"""Replay one owned odd-page write/read/restore inside the retained grant."""

import argparse
import json
from pathlib import Path

from verify_live import verify as verify_grant


def verify(path: Path) -> dict:
    grant = verify_grant(path)
    before = (path / "owned-before.bin").read_bytes()
    pattern = (path / "owned-pattern.bin").read_bytes()
    readback = (path / "owned-readback.bin").read_bytes()
    restored = (path / "owned-restored.bin").read_bytes()
    expected = bytes(((i * 37 + 0x5a) ^ (i >> 4)) & 0xff for i in range(4096))
    if any(len(blob) != 4096 for blob in (before, pattern, readback, restored)):
        raise ValueError("owned-page capture length")
    if pattern != expected or readback != pattern or restored != before:
        raise ValueError("owned-page pattern, readback or restoration")
    grant.update(local_page=f"0x{int(grant['pointer'], 16) + 0x1000:08x}",
                 uploaded_bytes=4096, restored_bytes=4096,
                 owned_page_restored=True)
    return grant


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("capture", type=Path)
    print(json.dumps(verify(p.parse_args().capture), indent=2))

#!/usr/bin/env python3
"""Verify the accepted capture and reject four materially altered records."""
import json
import shutil
import tempfile
from pathlib import Path

from verify_live import ART, verify


def reject(root, relative, mutate):
    path = root / relative
    original = path.read_bytes()
    try:
        path.write_bytes(mutate(original))
        try:
            verify(root)
        except ValueError:
            return
        raise AssertionError(f"accepted tampered {relative}")
    finally:
        path.write_bytes(original)


def flip(data):
    out = bytearray(data)
    out[-1] ^= 1
    return bytes(out)


def flip_at(data, offset):
    out = bytearray(data)
    out[offset] ^= 1
    return bytes(out)


def main():
    print("baseline:", verify())
    with tempfile.TemporaryDirectory(prefix="accele160-arena-replay-") as temp:
        root = Path(temp) / "capture"
        shutil.copytree(ART, root)
        reject(root, "fullbank/build/image.bin", flip)
        reject(root, "fullbank/post-1/result.json",
               lambda data: data.replace(b'"bytes": 1048576', b'"bytes": 4096'))
        reject(root, "fullbank/live-0/stop/page-after.bin",
               lambda data: flip_at(data, 0xb04))
        reject(root, "persistent/live-0/persist/quiescent-page.bin",
               lambda data: flip_at(data, 0xb54))
    print("four tampered captures rejected")


if __name__ == "__main__":
    main()

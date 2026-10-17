#!/usr/bin/env python3
"""Require offline replay to reject independent timer/DRAM/flash mutations."""
import shutil
import tempfile
from pathlib import Path
from verify_live import verify

ROOT = Path('artifacts/current/accele160-exclusive-timer-20261017')
PRIOR = Path('artifacts/current/accele160-occupied-probe-20261017')


def rejected(relative, offset):
    with tempfile.TemporaryDirectory() as temp:
        copy = Path(temp) / 'capture'
        shutil.copytree(ROOT, copy)
        path = copy / relative
        value = bytearray(path.read_bytes())
        value[offset] ^= 1
        path.write_bytes(value)
        try:
            verify(copy, PRIOR)
        except ValueError:
            return
        raise AssertionError('accepted tamper: ' + str(relative))


def main():
    verify(ROOT, PRIOR)
    for relative, offset in (
        ('build/image.bin', 0),
        ('live-0/stop/stock-held.bin', 0x80),
        ('live-0/timeout/page-after.bin', 0xa80),
        ('live-0/owner-after.bin', 0x2a0),
    ):
        rejected(relative, offset)
    print('baseline and four independent tamper rejections passed')


if __name__ == '__main__':
    main()

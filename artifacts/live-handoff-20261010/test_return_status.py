#!/usr/bin/env python3
"""Verify the fixed byte contract of the archived return-status callback."""
import argparse
import hashlib
from pathlib import Path

EXPECTED = bytes.fromhex(
    '7e01888c'      # lda 0x17e,g1
    '18208c8a'      # stos g1,0x18(g0)
    '0030888c'      # lda 0xc004bad0,g1
    'd0ba04c0'
    '00500484'      # bx (g1)
)


def validate(path):
    data = Path(path).read_bytes()
    if data != EXPECTED:
        raise ValueError(f'{path}: expected {EXPECTED.hex()}, got {data.hex()}')
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('binary', type=Path)
    args = p.parse_args()
    print(validate(args.binary))

#!/usr/bin/env python3
"""Replay exact bad-hash and bad-index rejection captures."""
import argparse
import json
from pathlib import Path
import struct
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_live import fnv, verify_grant


def verify(path: Path, mode: str) -> dict:
    if mode not in ('bad-hash', 'bad-index'):
        raise ValueError('mode')
    result = verify_grant(path)
    read = lambda name: (path / f'{name}.bin').read_bytes()
    before, reserved, rejected = read('page-before'), read('page-reserved'), read('page-rejected')
    stage_before, pattern = read('staging-before'), read('staging-pattern')
    if any(len(x) != 4096 for x in (before, reserved, rejected, stage_before, pattern)):
        raise ValueError('capture size')
    index = 1 if mode == 'bad-hash' else 127
    expected = bytes(((i * 53 + 0x96 + index) ^ (i >> 3)) & 0xff for i in range(4096))
    if pattern != expected or read('staging-readback') != pattern or read('staging-restored') != stage_before:
        raise ValueError('staging evidence')
    digest = fnv(pattern)
    control = (0x59504f43, 0x16161061, index, digest ^ (1 if mode == 'bad-hash' else 0))
    if struct.unpack_from('<4I', rejected, 0x820) != (0xa5a5a5a5,) * 4:
        raise ValueError('rejected command modified result')
    if struct.unpack_from('<4I', rejected, 0x860) != control:
        raise ValueError('control mismatch')
    expected_page = bytearray(reserved)
    expected_page[0x820:0x830] = bytes([0xa5]) * 16
    expected_page[0x860:0x870] = struct.pack('<4I', *control)
    if rejected != expected_page or before[0x860:0x870] != b'\xff' * 16:
        raise ValueError('loader page changed outside controls')
    status = dict(x.split('=', 1) for x in (path / 'copy-status.txt').read_text().split())
    if any(status.get(k) != v for k, v in [('started','1'),('done','1'),('status','2'),('residual','0')]):
        raise ValueError('unexpected command status')
    if mode == 'bad-hash' and read('target-before') != read('target-after'):
        raise ValueError('target modified on rejected hash')
    result.update(mode=mode, rejected=True, target_index=index, staging_fnv=f'0x{digest:08x}')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('capture', type=Path)
    p.add_argument('mode', choices=('bad-hash','bad-index'))
    a = p.parse_args()
    print(json.dumps(verify(a.capture, a.mode), indent=2))

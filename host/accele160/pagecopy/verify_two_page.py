#!/usr/bin/env python3
"""Replay two card-side copies inside a single retained grant."""
import argparse
import json
from pathlib import Path
import struct
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_live import fnv, verify_grant


def verify(path: Path) -> dict:
    base = verify_grant(path)
    read = lambda name: (path / f'{name}.bin').read_bytes()
    before, reserved = read('page-before'), read('page-reserved')
    if read('page-restored') != before or read('staging-restored') != read('staging-before'):
        raise ValueError('loader or staging restoration')
    digests = []
    for index in (0,126):
        pattern = bytes(((i*53+0x96+index)^(i>>3))&0xff for i in range(4096))
        if read(f'staging-{index}-readback') != pattern:
            raise ValueError('stage readback')
        digest = fnv(pattern)
        page = read(f'copy-{index}-page')
        if len(page) != 4096 or struct.unpack_from('<4I',page,0x820) != (0x59504f43,0x16161061,index,digest):
            raise ValueError('copy result')
        if struct.unpack_from('<4I',page,0x860) != (0x59504f43,0x16161061,index,digest):
            raise ValueError('copy control')
        expected = bytearray(reserved)
        expected[0x820:0x830]=page[0x820:0x830]
        expected[0x860:0x870]=page[0x860:0x870]
        if page != expected:
            raise ValueError('loader page changed outside copy records')
        status=dict(x.split('=',1) for x in (path/f'copy-{index}-status.txt').read_text().split())
        if any(status.get(k)!=v for k,v in [('started','1'),('done','1'),('status','0'),('residual','0')]):
            raise ValueError('copy command status')
        digests.append(f'0x{digest:08x}')
    result=json.loads((path/'result.json').read_text())
    if result['indexes'] != [0,126] or result['checksums'] != digests or not all(
            result[k] for k in ('metadata_restored','loader_page_restored','staging_restored')):
        raise ValueError('host result')
    base.update(indexes=[0,126],checksums=digests,two_page_session_passed=True)
    return base


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('capture',type=Path);a=p.parse_args()
    print(json.dumps(verify(a.capture),indent=2))

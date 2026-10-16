#!/usr/bin/env python3
"""Decode and verify the stock boot contract offline; never access hardware."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'readimage'))
from verify_full_dump import unpack

FLASH_SHA = '0a951782a7ccd1855746ffeb3a1b64563287bc56e0dce77d63b79c71ec3b502a'

def analyze(data):
    if len(data) != 0x100000:
        raise ValueError('expected 1 MiB flash')
    desc = data[0xe0000:0xe0400]
    if desc[:4] != b'XLYM':
        raise ValueError('descriptor signature')
    count = struct.unpack_from('<H', desc, 10)[0]
    if not 1 <= count <= 15:
        raise ValueError('descriptor bounds')
    regions = []
    for i in range(count):
        off, size = struct.unpack_from('<II', desc, 32 + 64*i)
        selector = desc[40 + 64*i]
        if size == 0 or off + size > len(data):
            raise ValueError('region bounds')
        regions.append(dict(selector=selector, offset=off, size=size))
    firmware, = [r for r in regions if r['selector'] == 2]
    base, size = firmware['offset'], firmware['size']
    trailer = data[base+size-0xa0:base+size]
    w = struct.unpack('<40I', trailer)
    if sum(w[:31]) & 0xffffffff != w[31]:
        raise ValueError('boot trailer checksum')
    loader_len, loader_off, loader_dst = w[3:6]
    if loader_len % 4 or loader_off + loader_len > size - 0xa0:
        raise ValueError('loader bounds')
    loader = data[base+loader_off:base+loader_off+loader_len]
    if sum(struct.unpack('<%dI' % (len(loader)//4), loader)) & 0xffffffff != w[6]:
        raise ValueError('loader checksum')
    if not loader_dst <= w[1] < loader_dst + loader_len:
        raise ValueError('loader entry outside copy')
    if not 0 <= w[7] < size - 0xa0:
        raise ValueError('compressed offset')
    runtime, zipped = unpack(data[base+w[7]:base+size-0xa0])
    if not w[8] <= w[2] < w[8]+len(runtime):
        raise ValueError('runtime entry outside decompression')
    ibr = struct.unpack_from('<8I', data, 0xfff30)
    if (ibr[4]+ibr[5]+ibr[6]) & 0xffffffff:
        raise ValueError('IBR checksum')
    return dict(flash_sha256=hashlib.sha256(data).hexdigest(),
        accepted_stock=hashlib.sha256(data).hexdigest()==FLASH_SHA,
        regions=regions, reset_entry=ibr[4], prcb=ibr[5],
        trailer_offset=base+size-0xa0, trailer_checksum_passed=True,
        loader=dict(flash_offset=base+loader_off, size=loader_len,
                    destination=loader_dst, entry=w[1], checksum_passed=True),
        runtime=dict(flash_zip_offset=base+w[7], destination=w[8],
                     entry=w[2], end_exclusive=w[8]+len(runtime), **zipped),
        live_execution_proven=False, scratch_ram_ownership_proven=False)

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('flash',type=Path)
    args=parser.parse_args()
    print(json.dumps(analyze(args.flash.read_bytes()),indent=2))

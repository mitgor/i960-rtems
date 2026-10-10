#!/usr/bin/env python3
"""Build an OFFLINE EXPERIMENTAL full-ROM candidate for the pinned installed image.
No device access, no vendor flashing container, no claim of hardware readiness.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

STOCK_SHA = '43d661af9dee28f531dcce525f8997e5fd11fc879d4a4e8bb07c5ac54a872a93'
BASE = 0xfef80000
CODE = 0x60000
META = 0x67f60
ENTRY = BASE + CODE
HOOK = 0xc004e844
HOOK_BYTES = bytes.fromhex('0ccfff090030808c00e804c0')


def word(data, offset):
    return struct.unpack_from('<I', data, offset)[0]


def checksum(data):
    if len(data) % 4:
        raise ValueError('unaligned checksum region')
    return sum(struct.unpack('<%dI' % (len(data)//4), data)) & 0xffffffff


def inspect_stock(stock):
    if len(stock) != 0x80000 or hashlib.sha256(stock).hexdigest() != STOCK_SHA:
        raise ValueError('requires exact archived 512 KiB stock image')
    if struct.unpack_from('<II', stock, 0x79c60) != (0x30000, 0x38000):
        raise ValueError('unexpected firmware descriptor')
    if struct.unpack_from('<3I', stock, META) != (1, 0xc000c460, 0xc004a2e0):
        raise ValueError('unexpected metadata handoff')
    if checksum(stock[META:META+0x7c]) != word(stock, META+0x7c):
        raise ValueError('metadata checksum mismatch')
    if checksum(stock[0x31000:0x37000]) != word(stock, META+0x18):
        raise ValueError('bootstrap checksum mismatch')
    if any(stock[CODE:CODE+0x1000]):
        raise ValueError('candidate code region is not zero padding')


def build(stock, code, unpacked):
    inspect_stock(stock)
    if not code or len(code) > 0x1000 or len(code) % 4:
        raise ValueError('code must be 1..4096 bytes and word aligned')
    if hashlib.sha256(unpacked).hexdigest() != '21f6c1d898a533d7023a53893f03547ed61631016d1b247d3ecbb97b9403c195':
        raise ValueError('requires verified unpacked 4.07-0-29 program')
    if unpacked[HOOK-0xc0010000:HOOK-0xc0010000+12] != HOOK_BYTES:
        raise ValueError('RAM hook instruction preimage mismatch')
    result = bytearray(stock)
    result[CODE:CODE+len(code)] = code
    struct.pack_into('<I', result, META+8, ENTRY)
    struct.pack_into('<I', result, META+0x7c, checksum(result[META:META+0x7c]))
    # Only padding, metadata entry, and its checksum may differ.
    allowed = set(range(CODE, CODE+len(code))) | set(range(META+8,META+12)) | set(range(META+0x7c,META+0x80))
    changes = [i for i,(a,b) in enumerate(zip(stock,result)) if a != b]
    if any(i not in allowed for i in changes) or result[0x7c000:] != stock[0x7c000:]:
        raise ValueError('unexpected change outside allowed regions')
    return bytes(result), {'experimental': True, 'hardware_validated': False,
        'flash_ready': False, 'stock_sha256': STOCK_SHA,
        'output_sha256': hashlib.sha256(result).hexdigest(),
        'loader_sha256': hashlib.sha256(code).hexdigest(),
        'loader_offset': CODE, 'entry_address': ENTRY, 'ram_hook_address': HOOK,
        'metadata_checksum': word(result,META+0x7c), 'changed_bytes': len(changes),
        'bootblock_unchanged': True, 'compressed_program_unchanged': True,
        'outstanding': ['PCI/BIOS behavior at hook', 'DMA and interrupt quiescence',
                        'exclusive DRAM window and inherited stack',
                        'watchdog behavior', 'custom flashing and independent recovery']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock', required=True); p.add_argument('--code', required=True)
    p.add_argument('--unpacked', required=True); p.add_argument('--out', required=True)
    a=p.parse_args()
    out=Path(a.out); report=out.with_suffix(out.suffix+'.json')
    if out.exists() or report.exists(): p.error('output or report already exists')
    try:
        image,manifest=build(Path(a.stock).read_bytes(),Path(a.code).read_bytes(),Path(a.unpacked).read_bytes())
    except (OSError,ValueError) as e: p.error(str(e))
    with out.open('xb') as f: f.write(image)
    with report.open('x') as f: json.dump(manifest,f,indent=2); f.write('\n')
    print(json.dumps(manifest,indent=2))
if __name__=='__main__': main()

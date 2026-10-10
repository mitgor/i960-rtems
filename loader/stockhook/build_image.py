#!/usr/bin/env python3
"""Create an offline 512 KiB stock-preserving opcode-0x6f candidate.

The result is not a programming container or a flash-ready image. Input
identity, boot metadata, dispatcher preimage, and allowed output bytes are
checked before any output is written.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

STOCK_SHA = '43d661af9dee28f531dcce525f8997e5fd11fc879d4a4e8bb07c5ac54a872a93'
UNPACKED_SHA = '21f6c1d898a533d7023a53893f03547ed61631016d1b247d3ecbb97b9403c195'
HOOK_SHA = '2a96bc45edd69b665dbd42b4dd17bd6594817ba64b34525c2e88e4e1faf0d16a'
BASE = 0xfef80000
CODE_OFFSET = 0x60000
META_OFFSET = 0x67f60
ENTRY = BASE + CODE_OFFSET
TABLE_SLOT = 0xc001f9bc
ORIGINAL_HANDLER = 0xc001fe98
NEW_HANDLER = 0xc0120000
PING_OPCODE = 0x6f


def word(data, offset):
    return struct.unpack_from('<I', data, offset)[0]


def checksum(data):
    if len(data) % 4:
        raise ValueError('unaligned checksum region')
    return sum(struct.unpack('<%dI' % (len(data) // 4), data)) & 0xffffffff


def inspect_stock(stock, unpacked):
    if len(stock) != 0x80000 or hashlib.sha256(stock).hexdigest() != STOCK_SHA:
        raise ValueError('requires the exact archived 512 KiB stock image')
    if hashlib.sha256(unpacked).hexdigest() != UNPACKED_SHA:
        raise ValueError('requires the exact verified unpacked program')
    if struct.unpack_from('<II', stock, 0x79c60) != (0x30000, 0x38000):
        raise ValueError('unexpected firmware descriptor')
    if struct.unpack_from('<3I', stock, META_OFFSET) != (1, 0xc000c460, 0xc004a2e0):
        raise ValueError('unexpected boot handoff')
    if checksum(stock[META_OFFSET:META_OFFSET + 0x7c]) != word(stock, META_OFFSET + 0x7c):
        raise ValueError('invalid original metadata checksum')
    if checksum(stock[0x31000:0x37000]) != word(stock, META_OFFSET + 0x18):
        raise ValueError('invalid original bootstrap checksum')
    if any(stock[CODE_OFFSET:CODE_OFFSET + 0x1000]):
        raise ValueError('hook placement is not zero padding')
    if TABLE_SLOT != 0xc001f804 + ((PING_OPCODE & 0x7f) - 1) * 4:
        raise ValueError('opcode/table mapping changed')
    if word(unpacked, TABLE_SLOT - 0xc0010000) != ORIGINAL_HANDLER:
        raise ValueError('opcode 0x6f no longer maps to unsupported handler')
    if unpacked[0x3a2e0:0x3a2e4] != bytes.fromhex('061e805c'):
        raise ValueError('stock entry preimage changed')


def inspect_hook(code):
    # Pin the inspected target build, including the instruction sequence and
    # relocation-resolved addresses. These checks also explain its contract.
    if len(code) != 84 or hashlib.sha256(code).hexdigest() != HOOK_SHA:
        raise ValueError('requires the inspected 84-byte target build')
    if code[-20:] != bytes.fromhex('7e01888c18208c8a0030888cd0ba04c000500484'):
        raise ValueError('handler does not return via pinned stock completion')
    for needle in (struct.pack('<I', TABLE_SLOT), struct.pack('<I', NEW_HANDLER),
                   struct.pack('<I', 0xc004a2e0), bytes.fromhex('821d8065')):
        if needle not in code[:-20]:
            raise ValueError('missing dispatch patch, resume branch, or I-cache invalidation')


def build(stock, unpacked, code):
    inspect_stock(stock, unpacked)
    inspect_hook(code)
    result = bytearray(stock)
    result[CODE_OFFSET:CODE_OFFSET + len(code)] = code
    struct.pack_into('<I', result, META_OFFSET + 8, ENTRY)
    struct.pack_into('<I', result, META_OFFSET + 0x7c,
                     checksum(result[META_OFFSET:META_OFFSET + 0x7c]))
    allowed = set(range(CODE_OFFSET, CODE_OFFSET + len(code)))
    allowed.update(range(META_OFFSET + 8, META_OFFSET + 12))
    allowed.update(range(META_OFFSET + 0x7c, META_OFFSET + 0x80))
    changes = [i for i, (a, b) in enumerate(zip(stock, result)) if a != b]
    if any(i not in allowed for i in changes):
        raise ValueError('unexpected output change')
    if result[0x30000:CODE_OFFSET] != stock[0x30000:CODE_OFFSET] or result[0x7c000:] != stock[0x7c000:]:
        raise ValueError('stock program or boot block changed')
    return bytes(result), {
        'experimental': True, 'hardware_validated': False, 'flash_ready': False,
        'stock_sha256': STOCK_SHA, 'unpacked_sha256': UNPACKED_SHA,
        'output_sha256': hashlib.sha256(result).hexdigest(),
        'hook_sha256': hashlib.sha256(code).hexdigest(), 'changed_bytes': len(changes),
        'metadata_entry': f'{ENTRY:08x}', 'metadata_checksum': f'{word(result, META_OFFSET + 0x7c):08x}',
        'opcode': f'{PING_OPCODE:02x}', 'table_slot': f'{TABLE_SLOT:08x}',
        'old_handler': f'{ORIGINAL_HANDLER:08x}', 'new_handler': f'{NEW_HANDLER:08x}',
        'stock_entry': 'c004a2e0', 'handler_completion_status': '017e',
        'boot_block_unchanged': True, 'compressed_program_unchanged': True,
        'outstanding': ['prove exclusive DRAM ownership through stock firmware lifetime',
                        'validate cache behavior on hardware', 'validate serial recovery',
                        'validate packaging and programming route']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock', required=True, type=Path)
    p.add_argument('--unpacked', required=True, type=Path)
    p.add_argument('--hook', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    a = p.parse_args()
    report = a.out.with_suffix(a.out.suffix + '.json')
    if a.out.exists() or report.exists():
        p.error('output or report already exists')
    try:
        result, manifest = build(a.stock.read_bytes(), a.unpacked.read_bytes(), a.hook.read_bytes())
    except (OSError, ValueError) as e:
        p.error(str(e))
    with a.out.open('xb') as f:
        f.write(result)
    with report.open('x') as f:
        json.dump(manifest, f, indent=2)
        f.write('\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()

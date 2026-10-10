#!/usr/bin/env python3
"""Independent byte-layout audit of the exact offline ROM-handler candidate."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

STOCK_SHA = '43d661af9dee28f531dcce525f8997e5fd11fc879d4a4e8bb07c5ac54a872a93'
HOOK_SHA = '91b445806f67b20ac0b90d4ec72cca63ad56a097759a0f60534f8ecdcb7b821d'
CANDIDATE_SHA = 'a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def word(data, offset):
    return struct.unpack_from('<I', data, offset)[0]


def audit(stock, candidate, hook):
    if len(stock) != len(candidate) or len(stock) != 0x80000 or len(hook) != 48:
        raise ValueError('wrong image or hook size')
    if (sha(stock), sha(candidate), sha(hook)) != (STOCK_SHA, CANDIDATE_SHA, HOOK_SHA):
        raise ValueError('unrecognized image or target hook')
    if any(stock[0x60000:0x61000]) or candidate[0x60000:0x60030] != hook:
        raise ValueError('wrong flash padding placement')
    if word(stock, 0x67f68) != 0xc004a2e0 or word(candidate, 0x67f68) != 0xfefe0000:
        raise ValueError('wrong metadata handoff')
    words = struct.unpack_from('<31I', candidate, 0x67f60)
    if sum(words) & 0xffffffff != word(candidate, 0x67fdc):
        raise ValueError('bad metadata sum')
    if word(hook, 4) != 0xfefe001c or hook[-4:] != bytes.fromhex('00500484'):
        raise ValueError('wrong ROM handler or tail branch')
    if struct.pack('<I', 0xc0120000) in hook:
        raise ValueError('old DRAM handler address present')
    changed = [i for i, (old, new) in enumerate(zip(stock, candidate)) if old != new]
    allowed = set(range(0x60000, 0x60030)) | set(range(0x67f68, 0x67f6c)) | set(range(0x67fdc, 0x67fe0))
    if len(changed) != 48 or any(i not in allowed for i in changed):
        raise ValueError('unexpected changed bytes')
    preserved = {
        'boot_block': (0x7c000, 0x80000),
        'pci_bios': (0x28000, 0x30000),
        'descriptor': (0x79c00, 0x79d60),
        'bootstrap': (0x31000, 0x37000),
        'compressed_program': (0x37000, 0x60000),
    }
    if any(stock[a:b] != candidate[a:b] for a, b in preserved.values()):
        raise ValueError('stock component changed')
    return {
        'candidate_sha256': sha(candidate), 'hook_sha256': sha(hook),
        'changed_bytes': len(changed), 'rom_handler': 'fefe001c',
        'metadata_sum_valid': True,
        'preserved_components': list(preserved),
        'no_dram_handler_address': True,
        'hardware_validated': False, 'flash_ready': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--hook', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(audit(args.stock.read_bytes(), args.candidate.read_bytes(),
                               args.hook.read_bytes()), indent=2))
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()

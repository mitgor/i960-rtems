#!/usr/bin/env python3
"""Audit the stock ROM interrupt table against accepted live IMAP values."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

STOCK_SHA = '0a951782a7ccd1855746ffeb3a1b64563287bc56e0dce77d63b79c71ec3b502a'
CANDIDATE_SHA = '9d5d4da2c283d10e1dee9c71ceb477f36e389cd0d0548764a3cc5f8a41a24c49'
FLASH_BASE = 0xfef00000
PRCB = 0xfeffdd20
TABLE = 0xfeffd910

def word(image, address):
    offset = address - FLASH_BASE
    if offset < 0 or offset + 4 > len(image):
        raise ValueError(f'address outside ROM: {address:08x}')
    return struct.unpack_from('<I', image, offset)[0]

def audit(stock, candidate, live):
    if len(stock) != 1048576 or len(candidate) != 1048576:
        raise ValueError('flash size')
    if hashlib.sha256(stock).hexdigest() != STOCK_SHA or \
       hashlib.sha256(candidate).hexdigest() != CANDIDATE_SHA:
        raise ValueError('flash identity')
    for image in (stock, candidate):
        if word(image, 0xfeffff44) != PRCB or word(image, PRCB + 16) != TABLE:
            raise ValueError('IBR/PRCB pointer')
    if stock[PRCB-FLASH_BASE:PRCB-FLASH_BASE+40] != \
       candidate[PRCB-FLASH_BASE:PRCB-FLASH_BASE+40] or \
       stock[TABLE-FLASH_BASE:TABLE-FLASH_BASE+1028] != \
       candidate[TABLE-FLASH_BASE:TABLE-FLASH_BASE+1028]:
        raise ValueError('stock PRCB/table drift')
    runs = [live['inventory_run']['report']] + live['inventory_repeat']['runs']
    maps = []
    for run in runs:
        reg = run['registers']
        if reg['0xff008700'] != f'0x{PRCB:08x}':
            raise ValueError('live PRCB pointer')
        maps.append(tuple(int(reg[f'0x{address:08x}'],16)
                          for address in (0xff008510,0xff008520,0xff008524,0xff008528)))
    if len(set(maps)) != 1:
        raise ValueError('unstable interrupt mapping')
    icon, imap0, imap1, imap2 = maps[0]
    fields = [(f'XINT{i}', (imap0 >> (4*i)) & 15) for i in range(4)]
    fields += [(f'XINT{i+4}', (imap1 >> (4*i)) & 15) for i in range(4)]
    fields += [('TINT0', (imap2 >> 16) & 15), ('TINT1', (imap2 >> 20) & 15)]
    selected = [18, 66, 82, 98, 114, 130, 242, 248]
    vectors = {str(n): f'0x{word(stock, TABLE + 4*(n+1)):08x}' for n in selected}
    return {
        'stock_sha256': STOCK_SHA, 'current_sha256': CANDIDATE_SHA,
        'stock_prcb': f'0x{PRCB:08x}', 'stock_interrupt_table': f'0x{TABLE:08x}',
        'live_icon': f'0x{icon:08x}', 'vector_cache_enabled': bool(icon & (1<<13)),
        'live_mappings': [{'source': source, 'field': field,
                           'vector': ((field << 4)|2) if field else None}
                          for source,field in fields],
        'stock_rom_selected_vectors': vectors,
        'vector_18_cached_word_address': '0x00000004',
        'limit': 'ROM vector 18 is zero but ICON enables internal vector caching; live cached word 0x04 was not read',
    }

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('stock', type=Path)
    p.add_argument('candidate', type=Path)
    p.add_argument('inventory_artifact', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    live = {
        'inventory_run': {'report': json.loads((a.inventory_artifact/'live/inventory-run/run-0-recovery.json').read_text())['report']},
        'inventory_repeat': json.loads((a.inventory_artifact/'live/inventory-repeat/result.json').read_text()),
    }
    result = audit(a.stock.read_bytes(), a.candidate.read_bytes(), live)
    a.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__': main()

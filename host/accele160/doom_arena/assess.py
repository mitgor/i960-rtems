#!/usr/bin/env python3
"""Offline, fail-closed admission check for the proposed 8 MiB Doom arena."""
import hashlib
import json
import struct
import sys
from pathlib import Path

FLASH_SHA = '1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
ZERO_SHA = hashlib.sha256(bytes(4096)).hexdigest()
START, END = 0xc0800000, 0xc1000000
BLOCK = 32768


def need(value, description):
    if not value:
        raise ValueError(description)


def assess(capture, firmware):
    survey = capture / 'upper-1'
    boot = (survey / 'boot-id.txt').read_text().strip()
    need(boot and (survey / 'descriptor-before.txt').read_text().strip() ==
         (survey / 'descriptor-after.txt').read_text().strip() ==
         'state=0 status=0 residual=0', 'idle stock descriptor')
    bases = ('c0384000', 'c0800000', 'c0810000', 'c0854000', 'c08b0000',
             'c08e0000', 'c0900000', 'c0a00000', 'c0b00000', 'c0c00000',
             'c0d00000', 'c0e00000', 'c0f00000', 'c0ffe000')
    pages = {}
    for base in bases:
        first = (survey / f'{base}-0.bin').read_bytes()
        second = (survey / f'{base}-1.bin').read_bytes()
        need(len(first) == len(second) == 4096, f'full page {base}')
        if base == 'c0384000':
            need(first[0x2a0:0xaa0] == second[0x2a0:0xaa0],
                 'stable allocator count/owner words')
        else:
            need(first == second, f'stable upper page {base}')
        pages[base] = first
    counts = struct.unpack_from('<256I', pages['c0384000'], 0x2a0)
    owners = struct.unpack_from('<256I', pages['c0384000'], 0x6a0)
    need(all((count == 0) == (owner == 0) for count, owner in
             zip(counts, owners)), 'allocator count/owner consistency')
    free_runs = []
    for lo, hi in ((152, 192), (192, 256)):
        start = None
        for i in range(lo, hi + 1):
            free = i < hi and counts[i] == owners[i] == 0
            if free and start is None:
                start = i
            if not free and start is not None:
                free_runs.append({'start': f'0x{0xc0000000+start*BLOCK:08x}',
                                  'bytes': (i-start)*BLOCK})
                start = None
    maximum = max((r['bytes'] for r in free_runs), default=0)
    need(maximum < END-START and len(free_runs) > 0,
         'unexpected stock free-run admission')
    flash = firmware.read_bytes()
    need(len(flash) == 1048576 and hashlib.sha256(flash).hexdigest() == FLASH_SHA,
         'exact current firmware image')
    refs = [{'flash_offset': f'0x{off:05x}', 'literal': f'0x{value:08x}'}
            for off in range(0, len(flash)-3, 4)
            if START <= (value := struct.unpack_from('<I', flash, off)[0]) < END
            and value % 4096 == 0]
    for index in (0, 1):
        folder = capture / f'post-survey-{index}'
        request = json.loads((folder / 'request.json').read_text())
        result = json.loads((folder / 'result.json').read_text())
        status = dict(field.split('=', 1) for field in
                      (folder / 'status.txt').read_text().split())
        need(request['boot_id'] == boot and request['selector'] == 9 and
             request['length'] == 1048576 and
             request['card']['bdf'] == '0000:37:09.1' and
             result['sha256'] == FLASH_SHA and result['bytes'] == 1048576 and
             result['old_after']['driver'] is None and
             all(status.get(k) == v for k, v in
                 (('done', '1'), ('status', '0'), ('residual', '0'),
                  ('guard_changes', '0'))), f'full flash read {index}')
    allocator_start = 0xc0000000
    allocator_end = allocator_start + len(counts)*BLOCK
    covers_candidate = allocator_start <= START and END <= allocator_end
    return {
        'boot_id': boot, 'candidate': ['0xc0800000', '0xc1000000'],
        'required_bytes': END-START, 'stock_allocator_largest_free_bytes': maximum,
        'stock_allocator_total_free_bytes': sum(r['bytes'] for r in free_runs),
        'stock_allocator_covers_candidate': covers_candidate,
        'sample_count': len(bases)-1,
        'sampled_upper_pages_zero': all(hashlib.sha256(pages[base]).hexdigest() ==
                                         ZERO_SHA for base in bases[1:]),
        'firmware_upper_page_literals': refs,
        'full_flash_reads_after': 2,
        'admitted': False,
        'reason': 'No owner for upper 8 MiB; zero samples and literals cannot authorize writes.'
    }


if __name__ == '__main__':
    capture = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        'artifacts/current/accele160-doom-arena-20261017')
    firmware = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(
        'artifacts/current/accele160-preempt-20261017/live/after-accept0-flash-0/data.bin')
    print(json.dumps(assess(capture, firmware), indent=2))

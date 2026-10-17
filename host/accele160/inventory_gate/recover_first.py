#!/usr/bin/env python3
"""Finish the completed first inventory after an overbroad owner-page check."""
import json
import mmap
from pathlib import Path
import struct
import subprocess
from run_inventory import BDF, DEBUG, DEVICE, FIRST, LAST, decode, fields, need

ROOT = Path('/home/mit/i960-accele160-inventory-20261017/live/inventory-run')
before = (ROOT / 'page-before.bin').read_bytes()
owner = (ROOT / 'owner-before.bin').read_bytes()
page = (ROOT / 'run-0-page.bin').read_bytes()
after_owner = (ROOT / 'run-0-owner.bin').read_bytes()
need(len(before) == len(owner) == len(page) == len(after_owner) == 4096, 'capture sizes')
need(fields(DEBUG / 'status').get('done') == '1' and
     fields(DEBUG / 'status').get('status') == '0', 'command not complete')
need(page[:FIRST] == before[:FIRST] and page[LAST:] == before[LAST:], 'loader page drift')
need(owner[0x2a0:0xaa0] == after_owner[0x2a0:0xaa0], 'allocator owner record drift')
diff = [i for i in range(4096) if owner[i] != after_owner[i]]
need(diff == [0xaa0, 0xaa1], 'unclassified owner-page drift')
decoded = decode(page)

cfg = (DEVICE / 'config').open('r+b', buffering=0)
res = (DEVICE / 'resource0').open('r+b', buffering=0)
bar = mmap.mmap(res.fileno(), 8192)
cfg.seek(0x44); original = struct.unpack('<I', cfg.read(4))[0]
need(original == 0xc0000000, 'PIATVR')
try:
    cfg.seek(0x44); cfg.write(struct.pack('<I', 0xc000e000))
    live = bytes(bar[4096:8192])
    need(live == page, 'live page differs from captured completed command')
    bar[4096 + FIRST:4096 + LAST] = before[FIRST:LAST]
    need(bytes(bar[4096:8192]) == before, 'loader page restoration')
    cfg.seek(0x44); cfg.write(struct.pack('<I', 0xc0384000))
    new_owner = bytes(bar[4096:8192])
    need(new_owner[0x2a0:0xaa0] == owner[0x2a0:0xaa0], 'owner words after restoration')
    (ROOT / 'run-0-owner-after-recovery.bin').write_bytes(new_owner)
finally:
    cfg.seek(0x44); cfg.write(struct.pack('<I', original))
    bar.close(); res.close(); cfg.close()
(DEBUG / 'release').write_text('release\n')
need(fields(DEBUG / 'status').get('released') == '1', 'command release failed')
subprocess.run(['rmmod', 'inventory_command'], check=True)
(ROOT / 'run-0-recovery.json').write_text(json.dumps({
    'report': decoded, 'owner_record_unchanged': True,
    'changed_bytes_outside_owner_records': diff,
    'loader_page_restored': True, 'module_released': True}, indent=2) + '\n')
print(json.dumps(decoded, indent=2))

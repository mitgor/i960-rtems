#!/usr/bin/env python3
"""Snapshot the retained control page under the card lock; issue no card command."""
import argparse
import fcntl
import json
import mmap
from pathlib import Path
import struct
import sys
import time

ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'rtems/transport'))
from card_select import select

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
lock=open('/run/lock/i960-loadrun.lock','w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
card=select('0000:37:09.1','accele160',driver='myrsread')
old=select('0000:37:04.1','dac960pg');assert old['driver'] is None
dev=Path('/sys/bus/pci/devices')/card['bdf']
with (dev/'config').open('r+b',buffering=0) as cfg,(dev/'resource0').open('r+b',buffering=0) as resource:
    bar=mmap.mmap(resource.fileno(),8192)
    cfg.seek(0x44);original=cfg.read(4)
    try:
        cfg.seek(0x44);cfg.write(struct.pack('<I',0xc000e000));cfg.seek(0x44)
        assert cfg.read(4)==struct.pack('<I',0xc000e000)
        first=bytes(bar[4096:8192]);time.sleep(.25);second=bytes(bar[4096:8192])
    finally:
        cfg.seek(0x44);cfg.write(original);cfg.seek(0x44);assert cfg.read(4)==original
        bar.close()
report=dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
    card=card,old=old,original_piatvr=f'0x{struct.unpack("<I",original)[0]:08x}',
    piatvr_restored=True,card_commands_issued=0,card_ram_writes=0,
    control=[f'0x{x:08x}' for x in struct.unpack_from('<16I',second,0xa40)],
    claim=[f'0x{x:08x}' for x in struct.unpack_from('<16I',second,0xb40)],
    dma=[f'0x{x:08x}' for x in struct.unpack_from('<32I',second,0xd80)],
    heartbeat_first=struct.unpack_from('<I',first,0xb50)[0],
    heartbeat_second=struct.unpack_from('<I',second,0xb50)[0])
a.out.mkdir(parents=True,exist_ok=False)
(a.out/'control-page.bin').write_bytes(second)
(a.out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

#!/usr/bin/env python3
"""Prove the selected LMT has no overlap and changes only the owned bank."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'game/doom/runtime/cache_bench'))
from verify import decode
stock=(0,0xc0000002,0xffc00001,0xc0400002,0xffe00001)
owned=(0,0xc0000002,0xffc00001,0xc0800002,0xff800001)
for addr in (0xc000fa40,0xc0710000,0xc078b000,0xc07fffff,
             0xc0800000,0xc0f7b850,0xc0ffffff,0xc1000000):
 before=decode(0x8221,addr,stock)
 after=decode(0x8221,addr,owned)
 assert after['template_matches']<=1
 expected=before['effective_cache_enabled']
 if 0xc0400000<=addr<0xc0600000:expected=False
 if 0xc0800000<=addr<0xc1000000:expected=True
 assert after['effective_cache_enabled']==expected,(hex(addr),before,after)
print('PASS: exclusive upper 8 MiB cached; control, WAD and kernel grants unchanged; no template overlap')

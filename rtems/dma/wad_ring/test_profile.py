#!/usr/bin/env python3
"""Timing trailer validation does not waive zero-padding or existing frame checks."""
import struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'residentnet'))
from presentation_profile import decode
b=bytearray(65536)
struct.pack_into('<16I',b,64768,0x31524650,1,1,2,100,60,30,10,20,0,0,100,0,0,10,0)
struct.pack_into('<16I',b,64960,0x31435057,1,100,20,10,0,2,2,2,0,131072,200,4,1,256,10)
assert decode(b,1,options={'wad_profile':True})['wad_cache'][10]==131072
for offset in (64832,64960,64964,64968,64984,65020,65024,65535):
 c=bytearray(b);c[offset]^=1
 try:decode(c,1,options={'wad_profile':True});raise RuntimeError('accepted mutation '+str(offset))
 except AssertionError:pass
try:decode(b,1);raise RuntimeError('unadvertised trailer accepted')
except AssertionError:pass
print('PASS WAD profile trailer: exact schema, counters, time scale, gap/tail padding and explicit opt-in; 9 refusals')

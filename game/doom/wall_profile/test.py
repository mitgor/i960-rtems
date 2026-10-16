#!/usr/bin/env python3
"""Reject invalid nesting, stale identity, conflicts and nonzero padding."""
import struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'rtems/residentnet'))
from presentation_profile import decode,preflight
b=bytearray(65536)
struct.pack_into('<16I',b,64768,0x31524650,1,1,2,100,60,30,10,20,0,0,100,0,0,10,0)
struct.pack_into('<16I',b,65024,0x314c4157,1,1,4,4166700,1,0,0,1,1000,8,900,5,800,4,700)
assert decode(b,1,options={'wall_profile':True})['wall_regions']['counts']==[1,8,5,4]
for offset,value in [(0,0),(4,2),(8,2),(12,5),(16,1),(24,1),(28,1),(32,2),(36,800),(40,0),(56,6),(60,900),(64,1),(508,1),(20,250000000),(32,0)]:
 c=bytearray(b);struct.pack_into('<I',c,65024+offset,value)
 try:decode(c,1,options={'wall_profile':True})
 except AssertionError:pass
 else:raise AssertionError(('mutation accepted',offset))
for opts in ({},{'wall_profile':True,'input_trace':True},{'wall_profile':True,'fixed_div_profile':True}):
 try:decode(b,1,options=opts)
 except AssertionError:pass
 else:raise AssertionError('unadvertised/conflicting trailer')
for opts in ({'wall_profile':True},{'wall_profile':True,'frame_profile':True,'double_buffer':True,'input_trace':True}):
 try:preflight(opts,True,True,True)
 except AssertionError:pass
 else:raise AssertionError('invalid admission')
print('PASS wall trailer validation: 21 malformed/conflicting cases refused')

#!/usr/bin/env python3
"""Timing metadata is validated independently of transport ownership/audits."""
import struct
from presentation_profile import decode,fnv,OFFSET
b=bytearray(65536);b[:64000]=bytes(i%251 for i in range(64000))
w=[0x31524650,1,1,1,60,20,30,10,10,20,30,100,fnv(b[:64000]),fnv(b[64000:64768]),10,0]
struct.pack_into('<16I',b,OFFSET,*w);assert decode(b,1,True)['render_ms']==60
for index in (0,1,2,3,4,5,6,7,12,13,14,15):
 c=bytearray(b);v=struct.unpack_from('<I',c,OFFSET+4*index)[0];struct.pack_into('<I',c,OFFSET+4*index,v^1)
 try:decode(c,1,True);raise RuntimeError(('accepted mutation',index))
 except AssertionError:pass
c=bytearray(b);c[OFFSET+64]=1
try:decode(c,1);raise RuntimeError('accepted nonzero reserved padding')
except AssertionError:pass
w[2]=29;w[3]=2;w[12]=w[13]=0;struct.pack_into('<16I',b,OFFSET,*w);assert decode(b,29,True)['pixel_fnv']==0
# No checksum means no claim of arbitrary in-bounds pixel integrity.
b[19]^=1;decode(b,29,True)
print('PASS timing schema, mode/sequence, sums, reserved bytes, FNV recomputation; disabled mode makes no pixel-integrity claim')

from presentation_profile import preflight
m=dict(frame_profile=True,double_buffer=True,presentation_test=True)
preflight(m,True,True,False)
for args in ((False,True,False),(True,False,False),(True,True,True)):
 try:preflight(m,*args);raise RuntimeError('bad profile admitted')
 except AssertionError:pass
preflight({},False,False,False)
preflight(dict(no_fnv=True,direct_frame=True,double_buffer=True),True,False,False)
print('PASS profile preflight rejects incompatible launch before opening card')

#!/usr/bin/env python3
"""Fault evidence stays negative, including truncated or wrong-owner captures."""
import struct
from decode_frame_fault import decode

def packed(w):
    return struct.pack('<100I', *w)

w=[0]*100
w[:4]=[0x31464446,42,96,0]
w[4:8]=[0x31464d4e,42,1,0xc0241000]
w[68:72]=[0x314d4446,1,12,0x101000]
w[84:92]=[7,100,0,0xc0f4eb40,0,0,1,6]
r=decode(packed(w))
assert r['terminal_identity_verified'] and not r['accepted_transfer']
assert r['dma']['generation']==12 and r['dma']['stage']==7
assert r['dma']['pci_command']=='0x0006'
for count in (0,1,2,63,64,87):
    p=w.copy();p[2:4]=[count,1];r=decode(packed(p))
    assert not r['accepted_transfer'] and 'dma' not in r
for index in (4,5):
    p=w.copy();p[index]^=1
    assert not decode(packed(p))['terminal_identity_verified']
for index,value in ((0,0),(1,0),(1,65536),(2,97),(3,5)):
    p=w.copy();p[index]=value
    try:decode(packed(p))
    except ValueError:pass
    else:raise AssertionError((index,value))
for n in (0,399,401):
    try:decode(bytes(n))
    except ValueError:pass
    else:raise AssertionError(n)
print('PASS terminal decoder: exact fields, partial counts, wrong identity, invalid metadata; never accepts transfer')

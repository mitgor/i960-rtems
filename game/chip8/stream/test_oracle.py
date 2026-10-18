"""Replay real player output against unchanged C8G1 core; reject tampering."""
from host import demo_rom
from native import Player
from oracle import Oracle
import struct
rom=demo_rom();p=Player(rom,500,0xfffffff0);o=Oracle(rom)
frames=0
for i in range(6001):
    if i%40==1:
        for e in (260,4):p.key(e)
        o.submit([260,4])
    raw=p.update((0xfffffff0+i*10)&0xffffffff)
    if raw is not None:o.check(raw);frames+=1
assert frames==3601 and len(o.events)<=2
p=Player(rom,500,0);o=Oracle(rom)
o.check(p.update(0));o.check(p.update(1000))
for offset in (12,48,320,324,328,332,340,352,356,360,364):
    p=Player(rom,500,0);o=Oracle(rom);raw=bytearray(p.update(0));raw[offset]^=1 if offset!=328 else 128
    try:o.check(raw)
    except ValueError:pass
    else:raise AssertionError(('tamper accepted',offset))
print('PASS 3601 independent replay frames, 300 brief edges, wrap/clamp, bounded input history, 11 mutations')

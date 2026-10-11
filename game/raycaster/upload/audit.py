#!/usr/bin/env python3
"""Byte-check the exact vendor disassembly and preserve the upload/UART trace."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];p=ROOT/'artifacts/vendor-fujitsu/4.07-0-29'
regions={'bootstrap':[(0xfefc8170,0xfefc81a0),(0xfefc9120,0xfefc9188),(0xfefc92a0,0xfefc93a0),(0xfefcb78c,0xfefcb7e8)],'unpacked':[(0xc004cd00,0xc004cd50),(0xc004ce90,0xc004cf10),(0xc004c010,0xc004c138)]}
for name,base,file in [('bootstrap',0xfefc8000,'Fgj40729.img.raw'),('unpacked',0xc0010000,'unpacked.bin')]:
 b=(p/file).read_bytes();print(name,'SHA256',hashlib.sha256(b).hexdigest())
 rows=[]
 for line in (p/(name+'.dis')).read_text().splitlines():
  m=re.match(r'^([0-9a-f]{8}):\s+((?:[0-9a-f]{2} ){3}[0-9a-f]{2})',line)
  if m:
   addr=int(m[1],16);assert b[addr-base:addr-base+4]==bytes.fromhex(m[2]);rows.append((addr,line))
 print('verified rows:',len(rows))
 for lo,hi in regions[name]:
  print('\n'+hex(lo)+'..'+hex(hi))
  for addr,line in rows:
   if lo<=addr<hi:print(line)
b=(p/'unpacked.bin').read_bytes();needle=(0xc004cec0).to_bytes(4,'little')
print('\nAligned references to format string:',[hex(0xc0010000+i) for i in range(0,len(b)-3,4) if b[i:i+4]==needle])
print('Format:',repr(b[0x3cec0:0x3ced0]))
print('Inference: upload-only unconditional formatter -> blocking UART readiness loop. Live paired method/code checks and reversible A/B are required to establish the active route and timing effect.')

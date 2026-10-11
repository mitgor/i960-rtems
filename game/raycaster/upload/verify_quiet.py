#!/usr/bin/env python3
"""Independent verification of paired UART-string evidence in live captures."""
import argparse,gzip,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--activation',choices=['step','open'],default='step');a=p.parse_args()
fw=(ROOT/'artifacts/vendor-fujitsu/4.07-0-29/unpacked.bin').read_bytes()
boot=(ROOT/'artifacts/vendor-fujitsu/4.07-0-29/Fgj40729.img.raw').read_bytes()
original=fw[0x3cec0:0x3cf10];quiet=b'\0'+original[1:]
expected={0xc011e22c:bytes.fromhex('800711c0'),0xc0110860:bytes.fromhex('90ce04c0d0ce04c0'),0xc000a2a0:boot[0x12a0:0x13a0],0xc000a120:boot[0x1120:0x1188]}
def pairs(log):
 pending={};result=[]
 for line in log.splitlines():
  m=re.fullmatch(r'QUIET BYTES address=([0-9a-f]{8}) offset=(\d+) pass=([01]) data=([0-9a-f]+)',line)
  if m:
   addr,off,k=int(m[1],16),int(m[2]),int(m[3]);data=bytes.fromhex(m[4]);key=(addr,k)
   b=pending.setdefault(key,bytearray());assert len(b)==off and len(data)<=32;b.extend(data)
  m=re.fullmatch(r'QUIET PAIR address=([0-9a-f]{8}) bytes=(\d+) verified',line)
  if m:
   addr,n=int(m[1],16),int(m[2]);x=bytes(pending.pop((addr,0)));y=bytes(pending.pop((addr,1)))
   assert len(x)==n and x==y
   if addr!=0xc004cec0:assert x==expected[addr]
   else:assert x in (original,quiet)
   result.append((addr,x))
 assert not pending
 return result
opening=(a.capture/'open/result.txt').read_text();closing=(a.capture/'close/result.txt').read_text()
assert ('QUIET BEGIN:' in opening)==(a.activation=='open') and 'QUIET END:' in closing
first_pairs=list(expected.items())+[(0xc004cec0,original),(0xc004cec0,quiet)]
assert pairs(opening)==(first_pairs if a.activation=='open' else [])
if a.activation=='open':first_pairs=[(0xc004cec0,quiet)]
assert pairs(closing)==[(0xc004cec0,quiet),(0xc004cec0,original)]
steps=json.loads((a.capture/'summary.json').read_text())['steps'];checked=0
if (a.capture/'commands.jsonl.gz').exists():
 with gzip.open(a.capture/'commands.jsonl.gz','rt') as f:
  for i,line in enumerate(f,1):
   row=json.loads(line);assert row['sequence']==i
   assert pairs(row['log'])==(first_pairs if i==1 else [(0xc004cec0,quiet)]);checked+=1
 assert checked==steps
else:
 for f in sorted(a.capture.glob('audit-*.txt')):
  assert pairs(f.read_text())==(first_pairs if f.name=='audit-000001.txt' else [(0xc004cec0,quiet)]);checked+=1
print(json.dumps(dict(steps=steps,paired_live_method_and_code_preimages=True,changed_bytes=1,step_logs_checked=checked,format_and_neighboring_handler_restored=True),indent=2))

#!/usr/bin/env python3
"""Exercise strict host decoder integration using an actual DMA frame capture."""
import argparse,json,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('manifest',type=Path);a=p.parse_args()
root=Path(__file__).resolve().parents[4];sys.path.insert(0,str(root/'rtems/residentnet'))
from presentation_profile import decode,preflight
b=a.capture.read_bytes()
if len(b) in (73728,77824):b=b[4096:69632]
m=json.loads(a.manifest.read_text());preflight(m,True,True,False)
assert decode(b,1,False,m)['cache_bench']['generation']==1
for offset in (65024,65028,65032,65036,65040,65048,65052,65060,65064,65068,65092):
 c=bytearray(b);c[offset]^=1
 try:decode(c,1,False,m)
 except AssertionError:pass
 else:raise AssertionError(('accepted corrupt diagnostic',offset))
for bad in (dict(m,cache_bench=False),dict(m,wall_profile=True),dict(m,input_trace=True),dict(m,fixed_div_profile=True)):
 try:decode(b,1,False,bad)
 except AssertionError:pass
 else:raise AssertionError('accepted conflicting/undeclared diagnostic')
print('PASS: actual frame, 11 corruptions, four undeclared/conflicting modes rejected')

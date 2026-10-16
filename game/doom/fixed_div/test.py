#!/usr/bin/env python3
"""Host arithmetic oracle and strict telemetry refusal tests."""
import ctypes,subprocess,tempfile,random,struct,sys
from pathlib import Path
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as work:
 p=Path(work);p.joinpath('legacy.c').write_text('#include <stdlib.h>\n#include <limits.h>\nint doom_div_legacy(int a,int b){if((abs(a)>>14)>=abs(b))return (a^b)<0?INT_MIN:INT_MAX;return (int)(((long long)a*65536)/b);}\n')
 subprocess.run(['cc','-O2','-fno-builtin','-fwrapv','-shared','-fPIC',str(here/'divide.c'),str(p/'legacy.c'),'-o',str(p/'test.so')],check=True)
 lib=ctypes.CDLL(str(p/'test.so'));fast=lib.doom_div_fast;old=lib.doom_div_legacy
 edges=[-2147483648,-2147483647,-1073741824,-65536,-16384,-1,0,1,16383,16384,65536,1073741823,2147483647]
 rng=random.Random(960);cases=[(a,b) for a in edges for b in edges if (a,b)!=(-2147483648,0)]
 for magnitude in [1,16383,16384,65535,65536,1073741823,2147483647]+[rng.randrange(1,2147483648) for _ in range(10000)]:
  for denominator in (max(0,(magnitude>>14)-1),magnitude>>14,(magnitude>>14)+1):
   for sa in (-1,1):
    for sb in (-1,1):cases.append((sa*magnitude,sb*denominator))
 cases.extend((rng.randrange(-2147483647,2147483648),rng.randrange(-2147483647,2147483648)) for _ in range(1000000))
 for a,b in cases:
  got=fast(a,b);assert got==old(a,b),(a,b,got,old(a,b))
  if -2147483648 not in (a,b):
   negative=(a<0)!=(b<0)
   expected=(-2147483648 if negative else 2147483647) if abs(a)>>14>=abs(b) else ((-1 if negative else 1)*((abs(a)*65536)//abs(b)))
   assert got==expected,(a,b,got,expected)
 print('PASS exact quotient/saturation/sign oracle:',len(cases),'pairs; legacy INT_MIN/0 excluded')
sys.path.insert(0,str(here.parents[2]/'rtems/residentnet'))
from presentation_profile import decode
raw=bytearray(65536);struct.pack_into('<16I',raw,64768,0x31524650,1,1,2,*([0]*10),10,0)
struct.pack_into('<8I',raw,65024,0x31564446,1,47,1,4166700,32,0,0)
opts=dict(fixed_div_profile=True,fast_fixed_div=True)
decode(raw,1,options=opts)
for offset,value in [(65024,0),(65028,2),(65032,48),(65032,61),(65036,0),(65040,0),(65044,31),(65052,1),(65532,1)]:
 bad=raw.copy();struct.pack_into('<I',bad,offset,value)
 try:decode(bad,1,options=opts)
 except AssertionError:pass
 else:raise AssertionError((offset,value))
try:decode(raw,1)
except AssertionError:pass
else:raise AssertionError('profile requires explicit opt-in')
print('PASS telemetry: explicit opt-in, schema/mode/check count and reserved padding; ten refusals')

# Fast arithmetic does not authorize telemetry in a non-profiled frame.
raw[65024:]=bytes(512)
decode(raw,1,options=dict(fast_fixed_div=True))
raw[65024]=1
try:decode(raw,1,options=dict(fast_fixed_div=True))
except AssertionError:pass
else:raise AssertionError('unprofiled fast mode must reject nonzero reserved tail')
print('PASS independent fast mode retains strict reserved-tail validation')

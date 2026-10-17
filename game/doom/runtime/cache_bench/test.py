#!/usr/bin/env python3
import subprocess,tempfile,struct
from pathlib import Path
from verify import EXPECTED,verify,decode
r=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'test.c').write_text('#include <stdio.h>\n#include "bench.h"\nstatic unsigned p[16384],q[16384];\nint main(void){unsigned i,k;for(i=0;i<16384;i++)p[i]=i;for(k=0;k<8;k++)printf("%u\\n",cb_run(k,p,q));return 0;}\n')
 subprocess.run(['cc','-O2','-fsanitize=address,undefined','-I'+str(r),str(p/'test.c'),'-o',str(p/'test')],check=True)
 got=list(map(int,subprocess.check_output([str(p/'test')],text=True).split()))
 assert got==EXPECTED,(got,EXPECTED)
 for k in range(8):
  b=bytearray(65536);struct.pack_into('<12I',b,65024,0x31424343,2,k+1,k,1048576,100,EXPECTED[k],1,1,0xc0810040,16384,1);verify(b)
  for off in (0,1,2,3,4,6,7,9,10,11,17):
   c=bytearray(b);c[65024+off*4]^=1
   try:verify(c)
   except AssertionError:pass
   else:raise AssertionError(('accepted tamper',k,off))
print('PASS: eight native workloads, sanitizers, 88 malformed trailer rejections')

assert decode(0x8221,0xc0f00000,[0,0xc0000002,0xff800001,0,0])['effective_cache_enabled']==False
assert decode(0x8221,0xc0100000,[0,0xc0000002,0xff800001,0,0])['effective_cache_enabled']==True
assert decode(0x7221,0xc0f00000,[2,0,0,0,0])['data_cache_bytes']==2048
assert decode(0x8220,0xc0100000,[2,0,0,0,0])['effective_cache_enabled']==False
print('PASS: logical range/default/global-disable decode')

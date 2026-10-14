#!/usr/bin/env python3
"""Compile actual host request validation: only the read-only counter is added."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--generated',type=Path);a=p.parse_args()
h=(a.generated if a.generated else Path(__file__).resolve().parents[2]/'residentnet/upload_host.h').read_text();
if a.generated:assert '#define I960_DOOM_DMA 1\n' in h, 'generated transport omitted DMA feature macro'
start=h.index(' if(op==10){if(');end=h.index('\n if(op==9||op==11)',start);body=h[start:end]
code=r'''
#include <assert.h>
#include <errno.h>
static int validate(unsigned index,unsigned value,unsigned extra){unsigned w[264]={0},op=10,i;int rc=0;w[8]=index;w[9]=value;w[10]=extra;
BODY
free:return rc;
}
int main(void){unsigned i,j;
 for(i=0;i<32;i++)for(j=0;j<600;j++){
  unsigned valid=(i==0&&!j)||i==1||(i==2&&j<=511);
#ifdef I960_DOOM_DMA
  valid|=i==5&&j==16;
#endif
  assert((validate(i,j,0)==0)==valid);assert(validate(i,j,1)==-EINVAL);
 }
 assert(validate(5,0xffffffffu,0)==-EINVAL);return 0;
}
'''.replace('BODY',body)
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'test.c').write_text(code)
 for flags in ([],['-DI960_DOOM_DMA']):
  subprocess.run(['cc','-fsanitize=address,undefined',*flags,str(p/'test.c'),'-o',str(p/'test')],check=True);subprocess.run([str(p/'test')],check=True)
print('PASS actual host validation with/without DMA: counter (5,16) only; arbitrary addresses, submits and nonzero tails refused')

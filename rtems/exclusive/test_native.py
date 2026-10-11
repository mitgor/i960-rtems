#!/usr/bin/env python3
import subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);src=p/'gate.c';exe=p/'gate'
 src.write_text('#include <stdio.h>\n#include "engines.h"\nint main(void){unsigned int w[16]={0},p,i,v;while(scanf("%u%u%u",&p,&i,&v)==3){unsigned int n;for(n=0;n<16;n++)w[n]=0;w[9]=0x10000;w[i]=v;printf("%u\\n",engine_admit(w,p));}return 0;}\n')
 subprocess.run(['cc','-fsanitize=address,undefined','-Wno-int-to-pointer-cast','-I'+str(HERE),str(src),'-o',str(exe)],check=True)
 cases=[(p,i,v) for p in range(4) for i in range(16) for v in [0,1,2,4,0x40,0x400,0x10000,0xffffffff]]
 expected=[]
 for phase,i,v in cases:
  w=[0]*16;w[9]=0x10000;w[i]=v
  expected.append(1 if phase>2 else 2 if any(w[:6]) else 3 if w[8]&0x40 else 4 if phase==2 and not w[9]&0x10000 else 0)
 result=list(map(int,subprocess.check_output([str(exe)],input=''.join(f'{p} {i} {v}\n' for p,i,v in cases).encode()).split()));assert result==expected
print('Exclusive admission:',len(cases),'cases passed with ASan/UBSan; active/error DMA, existing reset, external arbiter and invalid phases denied.')

# Admission/retention invariants in the actual generated host source.
from build_transport import build
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);payload=p/'payload';payload.write_bytes(bytes(4));build(p/'module',payload)
 host=(p/'module/dac960auto.c').read_text();stage=(p/'module/stage_rehearsal.h').read_text()
 assert 'd->mu_resident=true;d->ready=false;token=' in host
 assert '(!d->mu_resident||readl(d->bar+0x14)==0)' in host
 assert 'if(d->mu_failed||d->mu_resident)return -EBUSY;' in stage
 assert stage.index('if(d->mu_failed||d->mu_resident)')<stage.index('if(!d->irq_may_run)')
 assert 'd->removed || !d->ready || d->pinned' in host
print('Generated host source: one-way state before publication, write lockout, consumed-request acknowledgement and retain-before-STOP ordering verified.')

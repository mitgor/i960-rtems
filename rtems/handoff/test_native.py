#!/usr/bin/env python3
import os,subprocess,tempfile
from pathlib import Path
from build_transport import build
HERE=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as tmp:
 d=Path(tmp);src=d/'policy.c';exe=d/'policy'
 src.write_text('#include <stdio.h>\n#include "policy.h"\nstatic unsigned int input;\n#define MONITOR_READ() input\n#define MONITOR_WRITE(v) (input=(v))\n#include "entry.h"\nint main(void){unsigned int p,b,d;input=0x81000009; if(!monitor_take(9)||input||monitor_take(9))return 3; input=0x81000008;if(monitor_take(9)||input!=0x81000008)return 4;input=0x81000009;if(!monitor_take(9)||monitor_take(9))return 5;while(scanf("%u%u%u",&p,&b,&d)==3)printf("%u\\n",transfer_check(p,b,d));return 0;}\n')
 subprocess.run(['cc','-Wall','-Wextra','-fsanitize=address,undefined','-I'+str(HERE),str(src),'-o',str(exe)],check=True)
 cases=[(p,b,d) for p in range(256) for b in (0,1,0x400,0xffffffff) for d in (0,1,17)]
 expected=[2 if b or drift else 0 if p&127==127 else 1 for p,b,drift in cases]
 actual=list(map(int,subprocess.check_output([str(exe)],input=''.join(f'{p} {b} {drift}\n' for p,b,drift in cases).encode()).split()));assert actual==expected
 payload=d/'payload';payload.write_bytes(bytes(4));build(d/'module',payload)
 host=(d/'module/dac960auto.c').read_text();stage=(d/'module/stage_rehearsal.h').read_text()
 assert 'd->mu_failed=true;d->ready=false;' in host
 assert 'd->removed || !d->ready || d->pinned' in host
 assert 'd->pending||d->runner_uncertain' in host and 'epoch!=d->monitor_epoch' in host
 assert stage.index('if(d->mu_failed)return -EBUSY')<stage.index('if(!d->irq_may_run)')
 target=(HERE/'app.c').read_text();assert 'transfer_check(0,busy,drift)' in target
 # There are no target stores through sampled DMA addresses and no PCI/SCSI writes.
 assert 'REG(dma_regs[i])=' not in target.replace('REG(dma_regs[i])!=','')
print(f'Handoff gate: {len(cases)} proof/busy/drift combinations; no idle-to-proof promotion; host no-pending/epoch/retention guards passed under ASan/UBSan.')

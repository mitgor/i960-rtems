#!/usr/bin/env python3
"""Actual bulk-WAD ioctl fault injection, with modeled kernel/transport APIs."""
import ast,subprocess,tempfile
from pathlib import Path
here=Path(__file__).resolve().parent
tree=ast.parse((here/'test_frame_host.py').read_text());source=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='code' for x in n.targets))
code=source[:source.index('static int packet_exchange')]
code=code.replace('void*frame_dma_buf;','void*frame_dma_buf;void*wad_dma_buf;dma_addr_t wad_dma_bus;unsigned wad_dma_gen,wad_dma_geometry[3];bool wad_dma_pending;')
code+=r'''
#define min(a,b) ((a)<(b)?(a):(b))
static long frame_dma_ioctl(struct file*f,unsigned c,unsigned long a){return -ENOTTY;}
static int packet_exchange(struct experiment*d,unsigned token,unsigned value,unsigned*out,unsigned long deadline){
 unsigned op=token>>24,index=(token>>16)&255;calls++;if(calls==fail_at)return -ETIMEDOUT;*out=0;
 if(op==0x76){unsigned q[8]={0x31424157,1,1,1,123,4096,10000,0};*out=q[index];if(bad==1&&index==4)(*out)++;}
 if(op==0x77&&index==3)*out=phase?1:2;
 if(op==0x77&&index==4){unsigned r[12]={1,0x101000,0xc0801000,4096,0,0xc0f80000,0,0,6,4,0xc0f80000,0};*out=r[value];if(bad==2&&value==8)*out=7;if(bad==3)((u8*)d->wad_dma_buf)[0]=0;}
 return 0;
}
#include "wad_host.h"
static struct experiment d;static struct file f={&d};static struct pci_dev pci;static unsigned w[1032];
static void request(unsigned op){memset(w,0,sizeof w);w[0]=op;w[1]=42;w[2]=1;w[3]=123;w[4]=4096;w[5]=10000;if(op==1)memset(w+8,0x47,4096);}
static void reset(void){if(d.wad_dma_buf)free(d.wad_dma_buf);memset(&d,0,sizeof d);d.pdev=&pci;d.owned=d.mu_resident=d.irq_may_run=true;d.monitor_epoch=42;d.sequence=1;calls=fail_at=bad=phase=copyfail=freed=0;address=0x100000;request(1);}
static int raw(void){return wad_dma_ioctl(&f,0xd0204d09,(unsigned long)w);}
static int run(void){int rc=raw();if(rc)return rc;request(2);return raw();}
int main(void){unsigned i,n;
 reset();assert(!run()&&!d.wad_dma_pending);n=calls;assert(n==25);
 for(i=1;i<=n;i++){reset();fail_at=i;assert(run()<0&&d.mu_failed&&!freed);}
 reset();w[1]=43;assert(raw()==-ESTALE&&!calls);
 reset();w[6]=1;assert(raw()==-EINVAL&&!calls);
 reset();w[4]=4097;assert(raw()==-EINVAL&&!calls);
 reset();w[4]=2;assert(raw()==-EINVAL&&!calls); /* padding must be zero */
 reset();address=0xfffff000;assert(raw()==-ERANGE&&freed&&!d.wad_dma_buf);
 reset();bad=1;assert(raw()==-ESTALE&&!d.mu_failed);
 reset();assert(!raw());request(1);assert(raw()==-EBUSY);request(2);phase=1;assert(raw()==-EAGAIN&&!d.mu_failed);phase=0;assert(!raw());request(1);assert(raw()==-ESTALE);
 reset();bad=2;assert(run()==-EPROTO&&d.mu_failed&&!freed);
 reset();bad=3;assert(run()==-EILSEQ&&d.mu_failed&&!freed);
 reset();assert(!raw());request(2);w[3]++;assert(raw()==-ESTALE&&d.wad_dma_pending);
 reset();copyfail=1;assert(raw()==-EFAULT&&d.wad_dma_pending&&!freed);
 free(d.wad_dma_buf);return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'test.c').write_text(code)
 subprocess.run(['cc','-std=c99','-fsanitize=address,undefined','-fno-sanitize-recover=all','-I'+str(here),str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
print('PASS actual WAD ioctl: 25 exchange failures, pending/stale/geometry/padding/bounds, guard/completion faults, copyout retention')

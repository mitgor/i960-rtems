#!/usr/bin/env python3
"""Actual ioctl with coherent RAM and fault-injected registration."""
import ast,subprocess,tempfile
from pathlib import Path
here=Path(__file__).resolve().parent
s=ast.parse((here.parent/'test_frame_host.py').read_text());code=next(ast.literal_eval(n.value) for n in s.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='code' for x in n.targets))
code=code[:code.index('static int packet_exchange')].replace('void*frame_dma_buf;','void*frame_dma_buf;void*wr_buf[2];dma_addr_t wr_bus[2];unsigned wr_next[2],wr_total;')
code+=r'''
#define READ_ONCE(x) (x)
#define WRITE_ONCE(x,v) ((x)=(v))
static long pingpong_ioctl(struct file*f,unsigned c,unsigned long a){return -ENOTTY;}
static int packet_exchange(struct experiment*d,unsigned t,unsigned v,unsigned*out,unsigned long deadline){calls++;*out=0;return calls==fail_at?-ETIMEDOUT:0;}
#include "wire.h"
#include "host.h"
static struct experiment d;static struct file f={&d};static struct pci_dev pci;static unsigned w[8+WR_BLOCK/4];
static void request(unsigned op,unsigned gen){memset(w,0,sizeof w);w[0]=op;w[1]=42;w[2]=gen?(gen-1)&1:0;w[3]=gen;w[6]=100003;}
static void reset(void){unsigned i;for(i=0;i<2;i++)if(d.wr_buf[i])free(d.wr_buf[i]);memset(&d,0,sizeof d);d.pdev=&pci;d.owned=d.mu_resident=d.irq_may_run=true;d.monitor_epoch=42;d.sequence=1;calls=fail_at=bad=phase=copyfail=freed=0;address=0x100000;request(1,0);}
static int raw(void){return wad_ring_ioctl(&f,0xc0204d0b,(unsigned long)w);}
static void publish(unsigned gen,unsigned offset){struct wr_record*r=(void*)((u8*)d.wr_buf[(gen-1)&1]+WR_REQUEST);wr_record_make(r,WR_REQ_MAGIC,gen,offset,32768,100003);}
int main(void){unsigned i;struct wr_record*r,*c;
 reset();assert(!raw()&&calls==2);request(2,1);assert(raw()==-EAGAIN&&calls==2);
 publish(1,0);assert(!raw()&&w[8]==WR_REQ_MAGIC&&calls==2);request(3,1);w[5]=32768;memset(w+8,0x47,32768);assert(!raw()&&d.wr_next[0]==3&&calls==2);
 r=(void*)((u8*)d.wr_buf[0]+WR_RESPONSE);c=(void*)((u8*)d.wr_buf[0]+WR_COMPLETE);assert(wr_record_valid(r,WR_RSP_MAGIC,1,100003));
 request(3,1);assert(raw()==-ESTALE);publish(3,32768);request(2,3);assert(raw()==-EPROTO&&d.mu_failed);
 reset();assert(!raw());publish(1,0);request(3,1);w[5]=32768;assert(!raw());r=(void*)((u8*)d.wr_buf[0]+WR_RESPONSE);c=(void*)((u8*)d.wr_buf[0]+WR_COMPLETE);*c=*r;c->w[0]=WR_END_MAGIC;publish(3,32768);request(2,3);assert(!raw());
 for(i=1;i<=2;i++){reset();fail_at=i;assert(raw()==-ETIMEDOUT&&d.mu_failed&&!freed);}
 reset();assert(!raw());publish(1,0);((u8*)d.wr_buf[0])[0]=0;request(2,1);assert(raw()==-EILSEQ&&d.mu_failed);
 reset();assert(!raw());publish(1,0);request(3,1);w[4]=32768;w[5]=32768;assert(raw()==-ESTALE&&!d.mu_failed);
 reset();assert(!raw());publish(1,0);request(3,1);w[5]=32768;copyfail=1;assert(raw()==-EFAULT&&d.wr_next[0]==3&&!freed);
 reset();for(i=0;i<2;i++)if(d.wr_buf[i])free(d.wr_buf[i]);return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'test.c').write_text(code)
 subprocess.run(['cc','-std=c99','-fsanitize=address,undefined','-fno-sanitize-recover=all','-I'+str(here),str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
print('PASS ring host: RAM-only service, exact prior completion before reuse, stale/geometry refusal, guard fault, registration quarantine, uncertain copyout retention')

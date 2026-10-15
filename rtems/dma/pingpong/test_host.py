#!/usr/bin/env python3
"""Actual driver ioctl with coherent-memory / exchange fault models."""
from pathlib import Path
import subprocess,tempfile
r=Path(__file__).resolve().parent
s=r'''
#include <assert.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
typedef unsigned char u8;typedef uint64_t dma_addr_t;
struct pci_dev{int dev;};
struct experiment{struct pci_dev*pdev;void*pp_buf[2];dma_addr_t pp_bus[2];unsigned pp_next[2],pp_reads[2][3],monitor_epoch,sequence;bool pp_enabled,pp_running,removed,pinned,owned,mu_resident,pending,runner_uncertain,irq_may_run,response_ready,mu_failed,mu_halted,ready;int session_lock;};
struct file{void*private_data;};
static unsigned calls,fail_at,copyfail;static uint64_t address;
#define __user
#define GFP_KERNEL 0
#define IS_ERR(p) (!(p))
#define PTR_ERR(p) (-ENOMEM)
#define jiffies 1
#define msecs_to_jiffies(n) (n)
#define mutex_lock(p) ((void)0)
#define mutex_unlock(p) ((void)0)
#define dma_rmb() ((void)0)
#define dma_wmb() ((void)0)
#define READ_ONCE(x) (x)
#define FRAME_DMA_DIAG(...) ((void)0)
#define record(...) ((void)0)
#define session_log_end(p) ((void)0)
#define kfree free
static void*memdup_user(void*p,unsigned n){void*q=malloc(n);memcpy(q,p,n);return q;}
static int copy_to_user(void*p,void*q,unsigned n){if(copyfail)return 1;memcpy(p,q,n);return 0;}
static void*dma_alloc_coherent(void*d,unsigned n,dma_addr_t*a,int flags){*a=address;address+=0x100000;return malloc(n);}
static long wad_dma_ioctl(struct file*f,unsigned c,unsigned long a){return -ENOTTY;}
static int packet_exchange(struct experiment*d,unsigned token,unsigned value,unsigned*v,unsigned long deadline){calls++;if(calls==fail_at)return -ETIMEDOUT;assert(token>>24==0x6b&&(token&65535)==42);*v=0;return 0;}
#include "host.h"
static struct pci_dev pd;static struct experiment d;static struct file f={&d};static unsigned w[264];
static long req(unsigned op,unsigned g,unsigned off){memset(w,0,sizeof w);w[0]=op;w[1]=42;w[2]=g;w[3]=off;return pingpong_ioctl(&f,0xc4204d0a,(unsigned long)w);}
static void reset(void){free(d.pp_buf[0]);free(d.pp_buf[1]);memset(&d,0,sizeof d);d.pdev=&pd;d.monitor_epoch=42;d.sequence=1;d.owned=d.mu_resident=d.irq_may_run=1;calls=fail_at=copyfail=0;address=0x100000;}
static void ready(unsigned g){unsigned slot=(g-1)&1;unsigned*m=(unsigned*)((u8*)d.pp_buf[slot]+PP_MARK);m[0]=0x31505044;m[1]=g;m[2]=slot;m[3]=65536;m[4]=0xc0800000;m[5]=100;m[6]=~g;m[7]=g;}
int main(void){unsigned i,n;reset();assert(!req(1,0,0)&&calls==2);assert(!req(6,17,0)&&calls==3);
 assert(req(2,17,0)==-EAGAIN&&calls==3);ready(17);assert(!req(2,17,0)&&calls==3);
 assert(req(4,17,0)==-EBUSY&&calls==3);for(i=0;i<73728;i+=1024)assert(!req(3,17,i));assert(calls==3);
 assert(!req(4,17,0)&&calls==4&&d.pp_next[0]==19);assert(req(4,17,0)==-ESTALE);
 assert(req(3,19,73728)==-EINVAL);assert(req(6,19,0)==-EINVAL);
 for(i=0;i<7;i++){reset();assert(!req(1,0,0)&&!req(6,17,0));ready(17);((unsigned*)((u8*)d.pp_buf[0]+PP_MARK))[i]^=1;if(i==5)continue;assert(req(2,17,0)==-EPROTO&&d.mu_failed&&d.pp_buf[0]&&d.pp_buf[1]);}
 for(i=0;i<2;i++){reset();assert(!req(1,0,0)&&!req(6,17,0));ready(17);((u8*)d.pp_buf[0])[i?73695:0]^=1;assert(req(2,17,0)==-EILSEQ&&d.mu_failed);}
 for(n=1;n<=3;n++){reset();fail_at=n;long rc=req(1,0,0);if(!rc)rc=req(6,17,0);assert(rc==-ETIMEDOUT&&d.mu_failed&&d.pp_buf[0]);}
 reset();address=0xfffff000;assert(req(1,0,0)==-ERANGE&&d.mu_failed&&d.pp_buf[0]);
 reset();assert(!req(1,0,0)&&!req(6,17,0));ready(17);copyfail=1;assert(req(2,17,0)==-EFAULT&&d.pp_buf[0]);copyfail=0;assert(!req(2,17,0));
 free(d.pp_buf[0]);free(d.pp_buf[1]);return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'test.c').write_text(s)
 subprocess.run(['gcc','-std=gnu99','-fsanitize=address,undefined','-fno-sanitize-recover=all','-I'+str(r),str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
print('PASS actual host ioctl: no PCI command for poll/read, full-read release gate, two slots, guard/metadata corruption, stale release, exchange failures and copyout retention')

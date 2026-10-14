#!/usr/bin/env python3
"""Compile the actual Linux DMA-frame ioctl with fault-injecting API shims."""
import subprocess,tempfile
from pathlib import Path
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
typedef unsigned char u8;typedef uint64_t dma_addr_t;
struct pci_dev{int dev;};struct debugfs_blob_wrapper{void*data;unsigned size;};
struct experiment{struct pci_dev*pdev;void*frame_dma_buf;dma_addr_t frame_dma_bus;struct debugfs_blob_wrapper frame_dma_blob;unsigned frame_dma_gen,frame_dma_no_crc,monitor_epoch,sequence;bool frame_dma_pending,frame_dma_valid,removed,pinned,owned,mu_resident,pending,runner_uncertain,irq_may_run,response_ready,mu_failed,mu_halted,ready;int session_lock;};
struct file{void*private_data;};
static unsigned payload_crc;
static unsigned calls,fail_at,bad,phase,copyfail,freed;static uint64_t address=0x100000;
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
#define record(...) ((void)0)
#define session_log_end(p) ((void)0)
#define debugfs_create_blob(...) ((void)0)
#define kfree free
static void*memdup_user(void*p,unsigned n){void*q=malloc(n);memcpy(q,p,n);return q;}
static int copy_to_user(void*p,void*q,unsigned n){if(copyfail)return 1;memcpy(p,q,n);return 0;}
static void*dma_alloc_coherent(void*d,unsigned n,dma_addr_t*a,int flags){*a=address;return malloc(n);}
static void dma_free_coherent(void*d,unsigned n,void*p,dma_addr_t a){freed++;free(p);}
static long upload_ioctl(struct file*f,unsigned c,unsigned long a){return -ENOTTY;}
static unsigned crc32_le(unsigned c,const unsigned char*p,unsigned n){unsigned j;while(n--){c^=*p++;for(j=0;j<8;j++)c=(c>>1)^(0xedb88320u&-(c&1));}return c;}
static int packet_exchange(struct experiment*d,unsigned token,unsigned value,unsigned*v,unsigned long deadline){unsigned i,index=(token>>16)&255;calls++;if(calls==fail_at)return -ETIMEDOUT;assert(token>>24==0x6b&&(token&65535)==42);*v=0;
 if(index==0)*v=7;
 else if(index==6)assert(value==d->frame_dma_no_crc);
 else if(index==3)assert(value==address+4096);
 else if(index==4){assert(value==7);for(i=0;i<65536;i++)((u8*)d->frame_dma_buf)[4096+i]=(i*7)^(i>>8);payload_crc=crc32_le(~0u,(u8*)d->frame_dma_buf+4096,65536)^~0u;if(bad==1)((u8*)d->frame_dma_buf)[0]^=1;if(bad==3)((u8*)d->frame_dma_buf)[5000]^=1;if(bad==4)((u8*)d->frame_dma_buf)[73727]^=1;}
 else {unsigned report[16]={0x314d4446,2,7,(unsigned)address+4096,0xc0800000,0,0,0,0xc0f80000,0,0,7,1,0,0,0xc0f80000};assert(index==5&&value<16);report[14]=d->frame_dma_no_crc;report[5]=report[6]=d->frame_dma_no_crc?0:payload_crc;if(bad==2)report[5]^=1;if(bad==6)report[14]^=1;if(phase)report[1]=phase;*v=report[value];}
 return 0;
}
#include "frame_host.h"
static struct pci_dev pd;static struct experiment d;static struct file f={&d};static unsigned w[264];
static void request(unsigned op){memset(w,0,sizeof w);w[0]=op;w[1]=42;w[2]=7;}
static void reset(void){free(d.frame_dma_buf);memset(&d,0,sizeof d);d.pdev=&pd;d.monitor_epoch=42;d.sequence=1;d.owned=d.mu_resident=d.irq_may_run=1;calls=fail_at=bad=phase=copyfail=freed=0;address=0x100000;request(1);}
static long raw(void){return frame_dma_ioctl(&f,0xc4204d08,(unsigned long)w);}
static long run(void){long rc=raw();if(!rc){request(2);rc=raw();}return rc;}
int main(void){unsigned i;reset();assert(!run()&&calls==22&&d.frame_dma_valid&&!d.frame_dma_pending);request(3);assert(!raw());
 for(i=1;i<=22;i++){reset();fail_at=i;assert(run()==-ETIMEDOUT&&d.mu_failed&&!d.frame_dma_valid&&!freed);}
 reset();w[2]=8;assert(raw()==-ESTALE&&!d.frame_dma_buf);
 reset();w[1]=41;assert(raw()==-ESTALE&&!calls);
 reset();w[3]=4;assert(raw()==-EINVAL&&!calls);
 reset();address=0xfffff000;assert(raw()==-ERANGE&&freed&&!d.frame_dma_buf);
 reset();assert(!raw());request(1);assert(raw()==-EBUSY);request(2);phase=1;assert(raw()==-EAGAIN&&!d.mu_failed);phase=0;assert(!raw());request(1);assert(raw()==-ESTALE);
 reset();bad=1;assert(run()==-EILSEQ&&d.mu_failed&&!freed);
 reset();bad=3;assert(run()==-EILSEQ&&d.mu_failed&&!freed);
 reset();bad=4;assert(run()==-EILSEQ&&d.mu_failed&&!freed);
 reset();bad=2;assert(run()==-EPROTO&&d.mu_failed&&!freed);
 reset();assert(!raw());request(2);copyfail=1;assert(raw()==-EFAULT&&d.frame_dma_valid&&!freed);copyfail=0;request(3);w[3]=72704;assert(!raw());request(3);w[3]=73728;assert(raw()==-EINVAL);
 reset();w[3]=1;assert(!run()&&d.frame_dma_valid);
 reset();w[3]=1;bad=6;assert(run()==-EPROTO&&d.mu_failed&&!freed);
 reset();w[3]=1;bad=3;assert(!run()); /* CRC off deliberately cannot detect pixel corruption. */
 reset();w[3]=1;bad=1;assert(run()==-EILSEQ);
 free(d.frame_dma_buf);return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'linux').mkdir();(p/'linux/crc32.h').write_text('/* modeled CRC primitive */\n');(p/'test.c').write_text(code)
 subprocess.run(['cc','-std=c99','-fsanitize=address,undefined','-fno-sanitize-recover=all','-I'+str(p),'-I'+str(here),str(p/'test.c'),'-o',str(p/'test')],check=True);subprocess.run([str(p/'test')],check=True)
print('PASS actual frame-DMA ioctl: 22 exchange failure points, CRC/guards, pending, stale, bounds, 32-bit mapping, copyout retention')

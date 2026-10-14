#!/usr/bin/env python3
"""Compile actual ioctl code; verify mapping ownership and every exchange failure."""
import subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
source=r'''
#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
typedef unsigned char u8;typedef uint64_t dma_addr_t;
struct pci_dev{int dev;};
struct debugfs_blob_wrapper{void*data;unsigned size;};
#define debugfs_create_blob(...) ((void)0)
struct experiment{struct pci_dev*pdev;void*proof_buf;struct debugfs_blob_wrapper proof_blob;dma_addr_t proof_dma;unsigned proof_seq,monitor_epoch,sequence;bool proof_valid,removed,pinned,owned,mu_resident,pending,runner_uncertain,irq_may_run,response_ready,mu_failed,mu_halted,ready;int session_lock;};
struct file{void*private_data;};
static unsigned calls,fail_at,bad_byte,copy_fail,freed,target_error,staged[4];static uint64_t address=0x100000;
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
#define kfree free
static void*memdup_user(void*p,unsigned n){void*q=malloc(n);memcpy(q,p,n);return q;}
static int copy_to_user(void*p,void*q,unsigned n){if(copy_fail)return 1;memcpy(p,q,n);return 0;}
static void*dma_alloc_coherent(void*d,unsigned n,dma_addr_t*a,int flags){*a=address;return malloc(n);}
static void dma_free_coherent(void*d,unsigned n,void*p,dma_addr_t a){freed++;free(p);}
static long resident_ioctl(struct file*f,unsigned c,unsigned long a){return -ENOTTY;}
static int packet_exchange(struct experiment*d,unsigned token,unsigned value,unsigned*v,unsigned long deadline){
 unsigned op=token>>24,index=(token>>16)&255,i;calls++;if(calls==fail_at)return -ETIMEDOUT;assert((token&65535)==42);*v=0;
 if(op==0x50){assert(index<4);staged[index]=value;}
 else if(op==0x51){
  for(i=0;i<staged[1];i++)((u8*)d->proof_buf)[staged[0]-address+i]=(i*13u^staged[2]^(i>>8))&255;
  if(bad_byte)((u8*)d->proof_buf)[0]^=1;*v=target_error;
 }else{unsigned report[32]={0x31414d44,staged[3],staged[0],staged[1],staged[2],0,1,0xc0f70000,0,0,7,2,0,0,1,0};
  assert(op==0x52&&index<32);*v=report[index];}
 return 0;
}
#include "host.h"
static struct pci_dev pdev;
static struct experiment d;
static struct file f={&d};
static unsigned w[264];
static void reset(void){free(d.proof_buf);memset(&d,0,sizeof(d));d.pdev=&pdev;d.monitor_epoch=42;d.sequence=1;d.owned=d.mu_resident=d.irq_may_run=1;calls=fail_at=bad_byte=copy_fail=freed=target_error=0;address=0x100000;memset(w,0,sizeof(w));w[0]=1;w[1]=42;w[2]=65536;w[3]=4095;w[4]=1;w[5]=17;}
static long run(void){return dma_proof_ioctl(&f,0xc4204d07,(unsigned long)w);}
int main(void){unsigned i;
 reset();assert(run()==0&&calls==37&&d.proof_valid&&!freed);assert(run()==-EINVAL); /* output report cannot be reused as input */
 reset();w[2]=65537;assert(run()==-EINVAL&&!calls&&!d.proof_buf);
 reset();w[3]=4096;assert(run()==-EINVAL&&!calls);
 reset();w[1]=41;assert(run()==-ESTALE&&!calls);
 reset();w[4]=2;assert(run()==-ESTALE&&!calls);
 reset();address=0xfffff000;assert(run()==-ERANGE&&!calls&&freed==1&&!d.proof_buf);
 for(i=1;i<=37;i++){reset();fail_at=i;assert(run()==-ETIMEDOUT&&d.mu_failed&&d.proof_buf&&!d.proof_valid&&!freed);}
 reset();target_error=7;assert(run()==-EIO&&calls==37&&d.mu_failed&&d.proof_buf&&!d.proof_valid&&!freed);
 reset();bad_byte=1;assert(run()==-EILSEQ&&d.mu_failed&&!d.proof_valid&&!freed);
 reset();copy_fail=1;assert(run()==-EFAULT&&d.proof_valid&&d.proof_buf&&!freed);
 copy_fail=0;memset(w,0,sizeof(w));w[0]=2;w[1]=42;w[2]=1024;w[4]=1;assert(run()==0);
 memset(w+8,0,1024);w[3]=73728;assert(run()==-EINVAL);
 free(d.proof_buf);return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'test.c').write_text(source)
 subprocess.run(['cc','-std=c99','-fsanitize=address,undefined','-fno-sanitize-recover=all','-I'+str(HERE),str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
print('Actual host ioctl: guards, bounds, epochs, 32-bit mapping, all 37 uncertain exchanges, corruption, copyout retention passed')

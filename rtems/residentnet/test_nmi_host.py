#!/usr/bin/env python3
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#define __user
#define ODB 0x2c
struct experiment {unsigned char*bar;unsigned int monitor_epoch,removed,pinned,owned,mu_resident,pending,runner_uncertain,mu_failed,mu_halted,mu_nmi_injected,steps,sequence,irq_may_run,response_ready,session_lock;};
struct file {struct experiment*private_data;};
static unsigned int regs[32],writes,copyin,copyout;
static int copy_from_user(void*a,void*b,unsigned int n){if(copyin)return 1;memcpy(a,b,n);return 0;}
static int copy_to_user(void*a,void*b,unsigned int n){if(copyout)return 1;memcpy(a,b,n);return 0;}
static void mutex_lock(void*p){}static void mutex_unlock(void*p){}
static unsigned int readl(void*p){return *(unsigned int*)p;}
static void writel(unsigned int v,void*p){assert(p==&regs[8]&&v==0x80000000u);writes++;*(unsigned int*)p=v;}
#define record(...) ((void)0)
#define session_log_end(...) ((void)0)
static long resident_ioctl(struct file*f,unsigned int c,unsigned long a){return -ENOTTY;}
#include "nmi_test_host.h"
int main(void){struct experiment d={0},saved;struct file f={&d};unsigned int w[8]={1,123,0,0,0,0,0,0},i;
 d.bar=(unsigned char*)regs;d.monitor_epoch=123;d.owned=d.mu_resident=d.steps=d.sequence=d.irq_may_run=1;saved=d;
 regs[0x28/4]=0x1f3;regs[0x34/4]=0xff;
 assert(nmi_test_ioctl(&f,0xc0204d06,(unsigned long)w)==0&&writes==1&&w[3]==1);
 w[3]=0;assert(nmi_test_ioctl(&f,0xc0204d06,(unsigned long)w)==-EBUSY&&writes==1);
 d=saved;regs[8]=0;copyout=1;assert(nmi_test_ioctl(&f,0xc0204d06,(unsigned long)w)==-EFAULT&&writes==2&&d.mu_nmi_injected);copyout=0;
 /* Every scalar admission predicate must reject, with no additional write. */
 for(i=0;i<14;i++){unsigned int*fields[]={&d.removed,&d.pinned,&d.owned,&d.mu_resident,&d.pending,&d.runner_uncertain,&d.mu_failed,&d.mu_halted,&d.mu_nmi_injected,&d.steps,&d.sequence,&d.irq_may_run,&d.response_ready};d=saved;regs[8]=0;if(i<13)*fields[i]^=1;else d.monitor_epoch^=1;
  assert(nmi_test_ioctl(&f,0xc0204d06,(unsigned long)w)<0&&writes==2);
 }
 for(i=0;i<4;i++){unsigned int off[]={0x28,0x34,0x20,ODB};d=saved;regs[off[i]/4]^=1;assert(nmi_test_ioctl(&f,0xc0204d06,(unsigned long)w)<0&&writes==2);regs[off[i]/4]^=1;}
 d=saved;copyin=1;assert(nmi_test_ioctl(&f,0xc0204d06,(unsigned long)w)==-EFAULT&&writes==2);
 puts("Actual one-shot NMI ioctl: identity/state/mask/latch refusals, duplicate rejection and copy-out uncertainty retain the one-shot latch");
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'nmi.c';p.write_text(code);exe=p.with_suffix('')
 subprocess.run(['cc','-Wno-int-conversion','-fsanitize=address,undefined','-I',str(root),str(p),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)

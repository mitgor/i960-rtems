#!/usr/bin/env python3
"""Compile the actual host reply-wait loop with a deterministic MMIO clock."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here.parent/'exclusive/host.h').read_text().split('static long monitor_ioctl')[0]
prefix=r'''
#include <assert.h>
#include <errno.h>
#include <stdio.h>
#define ODB 0x24
static unsigned long jiffies,us,ready_at;
static unsigned int token,failed,uncleared;
static char bar[128];
struct experiment {char*bar;unsigned int mu_resident;};
#define msecs_to_jiffies(x) (x)
#define time_before(a,b) ((long)((a)-(b))<0)
static void usleep_range(unsigned int lo,unsigned int hi){us+=(lo+hi)/2;jiffies=us/1000;}
static unsigned int readl(char*p){unsigned int off=p-bar;
 if(off==ODB)return failed;
 if(off==0x28)return 0x1fb;
 if(off==0x34)return 0xff;
 if(off==0x14)return uncleared;
 assert(off==0x1c);return us>=ready_at?token:0;
}
'''
suffix=r'''
int main(void){struct experiment d={bar,1};unsigned int seen;int rc;
 token=0x92000001;ready_at=200;assert(!monitor_wait(&d,token,token,&seen));
#ifdef I960_LARGE_CONTROL
 assert(us==225);
#else
 assert(us==1250);
#endif
 us=jiffies=0;failed=1;assert(monitor_wait(&d,token,token,&seen)==-EPROTO&&us==0);failed=0;
 us=jiffies=0;ready_at=0;uncleared=1;rc=monitor_wait(&d,token,token,&seen);assert(rc==-ETIMEDOUT);
#ifdef I960_LARGE_CONTROL
 assert(jiffies>=20000&&jiffies<=20001);
 us=jiffies=0;token=0x8b000001;rc=monitor_wait(&d,token,token,&seen);assert(rc==-ETIMEDOUT&&jiffies==180000);
#else
 assert(us==18750000);
#endif
 puts("control wait: prompt reply, completion refusal, stale token and bounded timeout passed");
}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.c').write_text(prefix+source+suffix)
 for flags in ([],['-DI960_LARGE_CONTROL']):
  subprocess.run(['cc','-O2',*flags,str(p/'test.c'),'-o',str(p/'test')],check=True)
  subprocess.run([str(p/'test')],check=True)

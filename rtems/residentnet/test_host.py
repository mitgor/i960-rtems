#!/usr/bin/env python3
"""Exercise the actual host exchange function with deterministic MMIO/time mocks."""
from pathlib import Path
import subprocess,tempfile
h=Path(__file__).resolve().parent
source=(h/'host.h').read_text().split('static long resident_ioctl')[0]
prefix=r'''
#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#define ODB 0x2c
#define time_after_eq(a,b) ((long)((a)-(b))>=0)
struct experiment {unsigned char *bar;};
static unsigned int regs[32],mode,steps;static unsigned long jiffies;
static unsigned int readl(void *p){return *(unsigned int*)p;}
static void writel(unsigned int v,void*p){*(unsigned int*)p=v;}
static void usleep_range(unsigned int a,unsigned int b){
 steps++;jiffies++;
 if(mode==1||mode==2){regs[0x1c/4]=regs[0x14/4]|0x08000000u;regs[0x18/4]=0x12345678;if(mode==1)regs[0x14/4]=0;}
 if(mode==3)regs[ODB/4]=1;
 if(mode==4)regs[0x28/4]=0;
 if(mode==5)regs[0x34/4]=0;
}
'''
main=r'''
int main(void){struct experiment d={(unsigned char*)regs};unsigned int v,m;int rc;
 for(m=0;m<=5;m++){
  for(unsigned int i=0;i<32;i++)regs[i]=0;
  regs[0x28/4]=0x1fb;regs[0x34/4]=0xff;mode=m;steps=0;jiffies=0;
  rc=packet_exchange(&d,0xa0001234,1500,&v,10);
  if(m==1){assert(rc==0&&v==0x12345678&&steps==1);}
  else if(m>=3)assert(rc==-EPROTO&&steps==1);
  else assert(rc==-ETIMEDOUT&&steps==10);
 }
 puts("actual host exchange: success, absent reply, stale unconsumed reply, deadline, completion and both mask drifts passed");
}
'''
with tempfile.TemporaryDirectory() as d:
 f=Path(d)/'test.c';f.write_text(prefix+source+main);exe=Path(d)/'test'
 subprocess.run(['cc','-std=c99','-fsanitize=address,undefined',str(f),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
s=(h/'host.h').read_text();assert 'deadline=jiffies+msecs_to_jiffies(5000)' in s and 'd->mu_failed=true;d->ready=false' in s
print('One transaction deadline and uncertainty retention guards present.')

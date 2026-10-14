#!/usr/bin/env python3
"""Test the actual generated packet handshake and opt-in WAD polling policy."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--generated',type=Path,required=True);a=p.parse_args()
s=a.generated.read_text();s=s[s.index('static int packet_exchange('):s.index('static long resident_ioctl(')]
code=r'''
#include <assert.h>
#include <errno.h>
#include <string.h>
#define ODB 0x30
static unsigned regs[16],polls,ready_at,mode,sleeps,spins,jiffies,token;
struct experiment{unsigned char *bar;unsigned wad_dma_gen;};
#define time_after_eq(a,b) ((a)>=(b))
static void writel(unsigned v,void*p){*(unsigned*)p=v;}
static unsigned readl(void*p){unsigned off=(unsigned char*)p-(unsigned char*)regs;
 if(off==0x30&&mode==2)return 1;
 if(off==0x28&&mode==3)return 0;
 if(off==0x34&&mode==4)return 0;
 if(off==0x1c){polls++;if(polls>=ready_at){regs[5]=mode==5?token:0;regs[6]=0x89abcdef;regs[7]=token|0x08000000u;}}
 return *(unsigned*)p;
}
static void usleep_range(unsigned a,unsigned b){assert(a==50&&b==100);sleeps++;if(mode==6)jiffies++;}
static void cpu_relax(void){spins++;}
/*FUNCTION*/
static int run(unsigned m,unsigned ready,unsigned active,unsigned op){struct experiment d={(void*)regs,active};unsigned v=123;int rc;
 memset(regs,0,sizeof regs);regs[10]=0x1fb;regs[13]=0xff;
 mode=m;ready_at=ready;polls=sleeps=spins=jiffies=0;token=op|42;
 rc=packet_exchange(&d,token,321,&v,3);
 if(!rc){assert(v==0x89abcdef&&polls==ready);}else assert(v==123);
 return rc;
}
int main(void){unsigned i,op;unsigned fast[]={0x75000000,0x76000000,0x77010000,0x77050000};
 for(op=0;op<4;op++)for(i=1;i<=20;i++){
  assert(!run(0,i,1,fast[op]));assert(spins==(i<=17?i-1:16));assert(sleeps==(i<=17?0:i-17));
  assert(!run(0,i,0,fast[op])&&!spins&&sleeps==i-1);
 }
 assert(!run(0,20,1,0x77000000)&&!spins&&sleeps==19);
 assert(!run(0,20,1,0x78000000)&&!spins&&sleeps==19);
 assert(!run(0,20,1,0x6b000000)&&!spins&&sleeps==19);
 for(i=2;i<=4;i++)assert(run(i,1,1,0x75000000)==-EPROTO);
 assert(run(5,1,1,0x75000000)==-ETIMEDOUT&&polls==20000&&spins==16&&sleeps==19984);
 assert(run(6,20001,1,0x75000000)==-ETIMEDOUT&&spins==16&&sleeps==3);
 return 0;
}
'''.replace('/*FUNCTION*/',s)
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'t.c').write_text(code)
 subprocess.run(['cc','-std=c11','-fsanitize=address,undefined',str(p/'t.c'),'-o',str(p/'t')],check=True);subprocess.run([str(p/'t')],check=True)
print('PASS generated WAD polling: activation gating, legacy unchanged, 16-poll fallback, masks/doorbell, stale completion and unchanged bounds')

#!/usr/bin/env python3
"""Exercise the actual paired MMIO handshake, including its bounded fallback."""
import subprocess,tempfile
from pathlib import Path
r=Path(__file__).resolve().parent
h=(r/'upload_host.h').read_text();h=h[h.index('static int frame_pair_exchange'):h.index('\n#endif\nstatic long upload_ioctl')]
s=r'''
#include <assert.h>
#include <errno.h>
#include <string.h>
#define ODB 0x30
static unsigned regs[16],polls,ready_at,mode,sleeps,spins,jiffies,token;
struct experiment{unsigned char *bar;};
#define time_after_eq(a,b) ((a)>=(b))
static void writel(unsigned v,void*p){*(unsigned*)p=v;}
static unsigned readl(void*p){unsigned off=(unsigned char*)p-(unsigned char*)regs;
 if(off==0x30&&mode==2)return 1;
 if(off==0x28&&mode==3)return 0;
 if(off==0x34&&mode==4)return 0;
 if(off==0x1c){polls++;if(polls>=ready_at){regs[4]=0x89abcdef;regs[5]=mode==5?token:0;regs[6]=~0u;regs[7]=token|0x08000000u;}}
 return *(unsigned*)p;
}
static void usleep_range(unsigned a,unsigned b){assert(a==50&&b==100);sleeps++;if(mode==6)jiffies++;}
static void cpu_relax(void){spins++;}
/*FUNCTION*/
static int run(unsigned m,unsigned ready){struct experiment d={(void*)regs};unsigned a=123,b=456;int rc;
 memset(regs,0,sizeof regs);regs[10]=0x1fb;regs[13]=0xff;
 mode=m;ready_at=ready;polls=sleeps=spins=jiffies=0;token=0x6f7f002a;
 rc=frame_pair_exchange(&d,token,&a,&b,3);
 if(!rc){assert(a==~0u&&b==0x89abcdef&&polls==ready);}
 else assert(a==123&&b==456);
 return rc;
}
int main(void){unsigned i;
 for(i=1;i<=20;i++){assert(!run(0,i));assert(spins==(i<=17?i-1:16));assert(sleeps==(i<=17?0:i-17));}
 for(i=2;i<=4;i++)assert(run(i,1)==-EPROTO);
 assert(run(5,1)==-ETIMEDOUT&&polls==20000&&spins==16&&sleeps==19984);
 assert(run(6,20001)==-ETIMEDOUT&&spins==16&&sleeps==3);
 return 0;
}
'''.replace('/*FUNCTION*/',h)
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'t.c').write_text(s)
 subprocess.run(['cc','-std=c11','-fsanitize=address,undefined',str(p/'t.c'),'-o',str(p/'t')],check=True)
 subprocess.run([str(p/'t')],check=True)
print('PASS actual paired MMIO: two-word visibility, 16-poll fallback, mask/doorbell refusals, stale completion, deadline and iteration bounds')

#!/usr/bin/env python3
"""Execute the actual target state machine with modeled DMA register effects."""
import subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
source=r'''
#include <assert.h>
#include <stdint.h>
#include <string.h>
static unsigned regs[0x1800/4],cmd[2],mode,writes,stopping;
static unsigned char host[73728];
static unsigned *reg(unsigned);
static unsigned addr(const volatile void*);
#define DMA_JOB_R(a) DMA_R(a)
#define DMA_R(a) (*reg(a))
#define DMA_S(a) (cmd[(a)==0x1204?0:1])
#define DMA_ADDR(p) addr(p)
#define DMA_STOP() stopping
#define DMA_FENCE() ((void)0)
#include "target.h"
static unsigned addr(const volatile void*p){return p==(const volatile void*)dma_desc?0xc0f70000:0xc0f80000;}
static unsigned *reg(unsigned a){
 assert(a!=0x1448); /* Reserved: DAR1 is 144c in Intel table 20-2. */
 if(a==0x1444 && regs[0x1440/4]==1){
  writes++;if(mode==3)stopping=1;
  if(mode==1)regs[a/4]=0x400;
  else if(mode==2)regs[a/4]=8;
  else {
   assert(dma_desc[0]==0&&dma_desc[2]==0&&dma_desc[5]==7);
   memcpy(host+(dma_desc[1]-0x100000),(const void*)(dma_source+64),dma_desc[4]);
   regs[a/4]=0;regs[0x144c/4]=addr(dma_desc);regs[0x1450/4]=0;regs[0x1460/4]=0;regs[0x1464/4]=7;
   if(mode==4)dma_desc[6]^=1;if(mode==5)dma_source[0]^=1;
  }
 }
 return regs+a/4;
}
static void reset(void){memset(regs,0,sizeof(regs));memset(host,0xa5,sizeof(host));memset(dma_args,0,sizeof(dma_args));cmd[0]=2;cmd[1]=0;regs[0x104c/4]=0x13ffc;mode=writes=stopping=0;memset(dma_report,0,sizeof(dma_report));dma_report[0]=0x31414d44;dma_report[11]=2;}
static unsigned run(unsigned n,unsigned off,unsigned seed,unsigned seq){
 assert(!dma_control(0x50,0,0x101000+off,1));assert(!dma_control(0x50,1,n,1));
 assert(!dma_control(0x50,2,seed,1));assert(!dma_control(0x50,3,seq,1));unsigned rc=dma_control(0x51,0,0,1);if(rc)return rc;
 assert(dma_report[31]==1);assert(dma_control(0x50,0,1,1)==10);
 dma_step();assert(dma_report[31]==2);return dma_report[15];
}
int main(void){unsigned lengths[]={1,3,4,31,64,511,1024,2048,4095,4096,65536},i,j,n,off;
 for(i=0;i<sizeof(lengths)/sizeof(*lengths);i++){
  reset();n=lengths[i];off=i%4;assert(run(n,off,0x1357+i,1)==0);assert(writes&&dma_report[1]==1&&!dma_report[15]);
  for(j=0;j<sizeof(host);j++){unsigned k=j-4096-off;assert(host[j]==(k<n?((k*13u^(0x1357+i)^(k>>8))&255):0xa5));}
  assert(cmd[0]==2&&regs[0x1440/4]==0&&dma_report[14]==1);
  j=writes;assert(!run(n,off,2,2));assert(writes>j);
 }
 reset();assert(run(0,0,0,1)==3&&!writes);reset();assert(run(65537,0,0,1)==3&&!writes);
 reset();regs[0x1400/4]=1;assert(run(32,0,0,1)==4&&!writes);
 reset();mode=1;assert(run(32,0,0,1)==7&&dma_report[15]&&cmd[0]==2);assert(dma_control(0x50,0,1,1)==1);
 reset();mode=2;assert(run(32,0,0,1)==6&&dma_report[15]&&cmd[0]==2);
 reset();mode=4;assert(run(32,0,0,1)==9&&dma_report[15]);
 reset();mode=5;assert(run(32,0,0,1)==9&&dma_report[15]);
 reset();mode=3;assert(!run(65536,0,0,1)&&stopping&&writes&&!dma_report[15]);
 reset();stopping=1;assert(run(65536,0,0,1)==10&&!writes&&dma_report[15]);
 reset();assert(dma_control(0x51,0,0,0)==1&&!writes);
 assert(dma_control(0x50,4,0,1)==2);assert(dma_control(0x52,32,0,1)==~0u);
 return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'test.c').write_text(source)
 subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-fsanitize=address,undefined','-fno-sanitize-recover=all','-I'+str(HERE),str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
print('Actual target: 11 lengths, alignment, repeat/stale, idle admission, timeout, error, STOP and bounds passed')

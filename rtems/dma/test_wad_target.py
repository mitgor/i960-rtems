#!/usr/bin/env python3
"""Run the actual WAD DMA target with independent register/PCI-read modeling."""
import subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[2]
code=r'''
#include <assert.h>
#include <string.h>
#include <setjmp.h>
#include "game/doom/runtime/batch/wire.h"
static struct doom_batch batch;
static unsigned regs[0x1800/4],cmd[2],mode,reads,owner=1;
static unsigned char memory[12288],host[4096];static jmp_buf failed;
static unsigned *reg(unsigned);static unsigned addr(const volatile void*);
#define WD_R(a) (*reg(a))
#define WD_S(a) cmd[(a)==0x1204?0:1]
#define WD_ADDR(p) addr(p)
static unsigned owned_owner(void){return owner;}
static void exclusive_abort(void){longjmp(failed,1);}
#include "rtems/dma/wad_target.h"
static unsigned addr(const volatile void*p){return p==(const volatile void*)wd_desc?0xc0f80000:0xc0801000;}
static unsigned*reg(unsigned a){assert(a!=0x1448);
 if(a==0x1444&&regs[0x1440/4]){
  reads++;if(mode==1)regs[a/4]=0x400;else if(mode==2)regs[a/4]=8;
  else {assert(wd_desc[1]==0x101000&&wd_desc[3]==0xc0801000&&wd_desc[4]==4096&&wd_desc[5]==6);
   memcpy(memory+4096,host,4096);regs[0x144c/4]=addr(wd_desc);regs[0x1450/4]=regs[0x1460/4]=regs[a/4]=0;regs[0x1464/4]=6;
   if(mode==3)memory[8192]^=1;if(mode==4)wd_desc[7]^=1;
  }
 }return regs+a/4;
}
static void reset(void){unsigned i;memset(regs,0,sizeof regs);memset(&batch,0,sizeof batch);memset(wd_report,0,sizeof wd_report);memset(memory,0xa5,sizeof memory);
 cmd[0]=2;cmd[1]=0;regs[0x104c/4]=0x13ffc;wd_phase=wd_stage=wd_host=wd_sequence=mode=reads=0;owner=1;wd_buffer=memory;batch.state=WAD_REQUEST;batch.sequence=1;
 for(i=0;i<4096;i++)host[i]=(i*7)^(i>>8);
}
static void submit(void){assert(!wd_control(1,0x101000,1));assert(!wd_control(2,1,1));assert(wd_phase==1&&!reads);assert(wd_control(1,0x102000,1)==~0u);assert(wd_control(5,1,1)==~0u);}
int main(void){unsigned i,j,w[16],save;
 reset();assert(wd_control(1,0xfffffff0,1)==~0u);assert(wd_control(1,0x101001,1)==~0u);assert(wd_control(2,1,1)==~0u);assert(wd_control(1,0x101000,0)==~0u);
 submit();wd_step();assert(wd_phase==2&&reads&&cmd[0]==2&&!memcmp(host,memory+4096,4096));assert(wd_report[8]==6);
 assert(wd_control(5,2,1)==~0u);assert(!wd_control(5,1,1)&&wd_phase==3);
 wd_phase=1;
 for(i=4;i<=10;i++){wd_stage=i;memset(w,0,sizeof w);w[2]=i>=6&&i<=9;w[3]=w[2]?0x400:0;w[6]=i==4?2:6;assert(wad_dma_isolation_snapshot(w));}
 wd_stage=7;
 for(i=0;i<8;i++){save=wd_desc[i];for(j=0;j<32;j++){wd_desc[i]=save^(1u<<j);memset(w,0,sizeof w);w[2]=1;w[6]=6;assert(!wad_dma_isolation_snapshot(w));}wd_desc[i]=save;}
 for(i=1;i<=4;i++){reset();submit();mode=i;if(!setjmp(failed)){wd_step();assert(0);}assert(wd_phase==1&&wd_buffer&&wd_report[11]&&cmd[0]==2);}
 for(i=1;i<=2;i++){reset();wd_phase=i;if(!setjmp(failed)){wd_release();assert(0);}assert(wd_buffer&&wd_phase==i);}
 reset();wd_phase=3;wd_release();assert(!wd_buffer&&!wd_phase);
 reset();submit();owner=0;if(!setjmp(failed)){wd_step();assert(0);}assert(!reads&&wd_phase==1);
 return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'test.c').write_text(code)
 subprocess.run(['cc','-std=c99','-fsanitize=address,undefined','-fno-sanitize-recover=all','-I'+str(root),str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
print('PASS actual WAD target: exact read, ACK pin, stale/misaligned/overflow/owner refusal, 256 descriptor mutations, active isolation, timeout/error/guard quarantine')

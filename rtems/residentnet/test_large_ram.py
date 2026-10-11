#!/usr/bin/env python3
"""Exercise the target admission/pattern/guard code with simulated DRAM/MMIO."""
import re,subprocess,tempfile
from pathlib import Path
here=Path(__file__).resolve().parent
source=(here/'large_ram.c').read_text().replace('#define R(a) (*(volatile unsigned int*)(a))','#define R(a) (*native_reg(a))')
source=re.sub(r'__asm__ volatile\([^;]+;', '(void)0;', source)
source=source.replace('unsigned int w[17],a,p,v,cache,scratch;', 'unsigned int w[17],a,p,v,cache=0,scratch=0;')
prefix=r'''
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
static unsigned int mem[4194304],prcb=0xfeffd0c0u,zero,mode,corrupted;
unsigned int irq_owned_entry_fp=0xc0100000;
static unsigned int *native_reg(unsigned int a){
 if(a==0xfeffd4e0)return &prcb;
 if(a>=0xfeffd0c0&&a<0xfeffd0e4)return &zero;
 assert(a>=0xc0000000u&&a<0xc1000000u&&!(a&3));
 if(mode==2&&a>=0xc0240000u&&a<0xc0240000u+I960_OWNED_MIB*1048576u)a=(a-0xc0240000u)%0x80000+0xc0240000u;
 if(mode==4&&a>=0xc0240000u&&a<0xc0240000u+I960_OWNED_MIB*1048576u&&!corrupted){mem[0]^=1;corrupted=1;}
 return mem+(a-0xc0000000u)/4;
}
unsigned int exclusive_fault_valid(void){return mode!=1;}
unsigned int scsi_target_verified(void){return 1;}
static unsigned int polls;
void exclusive_drain_poll(void){polls++;}
void exclusive_stack_report(unsigned int*w){}
void exclusive_engine_report(unsigned int*w){unsigned int i;for(i=0;i<17;i++)w[i]=0;}
'''
source=source.replace('(*(volatile unsigned char*)0xe0400000)&31','6')
suffix=r'''
int main(int argc,char**argv){unsigned int w[64];mode=atoi(argv[1]);
 R(0xc011e22c)=0xc0110780;R(0xc0110780+0xc0)=0xc000d540;R(0xc0110780+0x168)=0xc004fc40;R(0xc00a8718)=0x1000000;R(0xc0112a70)=0xc0f2c000;R(0xc0110780+8)=0x80000;
 if(mode==3)irq_owned_entry_fp=LARGE_LO+4096;
 if(mode){assert(exclusive_large_prepare());assert(!ready);return 0;}
 assert(!exclusive_large_prepare());assert(exclusive_large_valid());exclusive_large_report(w);
 assert(w[4]==4&&w[5]==LARGE_BYTES&&w[16]==1);
 assert(exclusive_large_finish());assert(final_checked==(LARGE_HI-64-LARGE_RESERVE)/4);assert(polls==(final_checked+1023)/1024);
 R(LARGE_RESERVE+4)^=1;assert(exclusive_large_valid());assert(!exclusive_large_finish());assert(error==7);R(LARGE_RESERVE+4)^=1;error=0;
 R(LARGE_LO)^=1;assert(!exclusive_large_valid());R(LARGE_LO)^=1;
 R(LARGE_RESERVE)^=1;assert(!exclusive_large_valid());
 puts("large RAM admission, four patterns, guards and reserve mutation passed");return 0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.c').write_text(prefix+source+suffix)
 for mib in (1,4,10,12):
  subprocess.run(['cc','-O2','-DI960_OWNED_MIB='+str(mib),'-I'+str(here),str(p/'test.c'),'-o',str(p/'test')],check=True)
  for mode in range(5):subprocess.run([str(p/'test'),str(mode)],check=True)
print('All four RAM sizes: positive admission, missing ownership, alias, parked-frame refusal and protected-memory mutation passed')

#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include "policy.h"
static unsigned int record[1024],stack[1024],report[16],regs[1024];
static unsigned int ticks=42,claimed=1,switch_fault,code;
static volatile unsigned int *claim_report=report;
static jmp_buf parked;
static unsigned int *reg(unsigned int addr){
 if(addr>=AT_STACK&&addr<AT_END)return &stack[(addr-AT_STACK)/4];
 if(addr>=0xc0000800u&&addr<0xc0000900u)return &regs[(addr-0xc0000800u)/4];
 if(addr>=0xfeffdd20u&&addr<0xfeffdd40u)return &regs[64+(addr-0xfeffdd20u)/4];
 if(addr>=0xff008500u&&addr<=0xff008528u)return &regs[96+(addr-0xff008500u)/4];
 if(addr>=0xff008700u&&addr<=0xff008704u)return &regs[128+(addr-0xff008700u)/4];
 if(addr==4)return &regs[130];
 if(addr==0xff000300u||addr==0xff000304u||addr==0xff000310u||addr==0xff000314u)return &regs[160+(addr-0xff000300u)/4];
 if(addr>=0x1400u&&addr<0x14c0u){unsigned int off=(addr-0x1400u)%64;assert(off==0||off==16||off==32);return &regs[192+(addr-0x1400u)/4];}
 assert(!"unreviewed MMIO read");return 0;
}
#define REG(a) (*reg(a))
#define ACCELE_TERMINAL_TEST 2
#define AT_BUFFER record
#define AT_SYNC() ((void)0)
#define AT_VECTOR0() 0x12345678u
#define AT_PARK() longjmp(parked,1)
#include "card.inc"
void accele_terminal_enter(unsigned int c){code=c;longjmp(parked,1);}
int main(void){unsigned int i;
 record[0]=123;at_init();assert(at_initialized&&at_nonce==123&&record[31]==AT_READY&&record[26]);
 for(i=0;i<16;i++){
  stack[i]^=1;assert(!at_guard());stack[i]^=1;
  stack[1008+i]^=1;assert(!at_guard());stack[1008+i]^=1;
 }
 record[0]=124;record[1]=1;record[2]=AT_TRIGGER;at_poll();assert(!code);
 record[0]=123;
 if(!setjmp(parked)){at_poll();assert(!"trigger missed");}
 assert(code==0x7d002&&!at_guard());
 record[20]=code;
 if(!setjmp(parked))accele_terminal_record();
 assert(record[31]==AT_DONE&&record[27]==42&&record[28]==1&&record[26]==0);
 assert(record[34]==0x12345678&&report[6]==(0xf0000000u|code));
 puts("actual card C: bounded MMIO inventory, guards, stale trigger and terminal record passed");
 return 0;
}

#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include "policy.h"
static unsigned int record[1024],stack[2048],report[16],regs[1024];
static unsigned int ticks=42,claimed=1,switch_fault,code;
static volatile unsigned int *claim_report=report;
static jmp_buf parked;
static unsigned int *reg(unsigned int addr){
 if(addr>=AT_STACK&&addr<AT_IRQ_END)return &stack[(addr-AT_STACK)/4];
 if(addr>=0xc0000800u&&addr<0xc0000900u)return &regs[(addr-0xc0000800u)/4];
 if(addr>=0xfeffdd20u&&addr<0xfeffdd40u)return &regs[64+(addr-0xfeffdd20u)/4];
 if(addr>=0xff008500u&&addr<=0xff008528u)return &regs[96+(addr-0xff008500u)/4];
 if(addr>=0xff008700u&&addr<=0xff008704u)return &regs[128+(addr-0xff008700u)/4];
 if(addr>=0x1320u&&addr<=0x1328u)return &regs[240+(addr-0x1320u)/4];
 if(addr==0x1700u)return &regs[220];
 if(addr==4)return &regs[130];
 if(addr==0xff000300u||addr==0xff000304u||addr==0xff000310u||addr==0xff000314u)return &regs[160+(addr-0xff000300u)/4];
 if(addr>=0x1400u&&addr<0x14c0u){unsigned int off=(addr-0x1400u)%64;assert(off==0||off==12||off==16||off==20||off==24||off==28||off==32||off==36);return &regs[192+(addr-0x1400u)/4];}
 if(addr==0x1600u||addr==0x104cu||addr==0x1800u||addr==0x1808u||addr==0x180cu||addr==0x1820u||addr==0x1824u||addr==0x1828u)return &regs[300+(addr&63)/4];
 if((addr>=0xc0384b6cu&&addr<=0xc0384e7cu)||(addr>=0xc049b7ccu&&addr<=0xc049b7d4u))return &regs[400+(addr&255)/4];
 assert(!"unreviewed MMIO read");return 0;
}
#define REG(a) (*reg(a))
#ifndef ACCELE_TERMINAL_TEST
#define ACCELE_TERMINAL_TEST 3
#endif
static unsigned int vector0,drop_vector;
#if (ACCELE_TERMINAL_TEST == 5 || ACCELE_TERMINAL_TEST == 14)
static unsigned int handoffs=12;
#endif
#define AT_SET_VECTOR0(v) (drop_vector?vector0:(vector0=(v)))
#define AT_ENTRY_ADDRESS(fn) ((fn)==accele_fault_entry?0xc0711000u:0xc0711100u)
#define AT_BUFFER record
#define AT_SYNC() ((void)0)
#define AT_VECTOR0() vector0
#define AT_PARK() longjmp(parked,1)
#include "card.inc"
void accele_terminal_enter(unsigned int c){code=c;longjmp(parked,1);}
void accele_fault_entry(void){}
void accele_nmi_entry(void){}
void accele_raise_fault(void){longjmp(parked,2);}
static void baseline(void){unsigned int i;
 for(i=0;i<1024;i++){record[i]=0;regs[i]=0;}
 for(i=0;i<32;i+=2)regs[i]=0xc0053400u;
 regs[64]=0xc0000800u;regs[128]=0xfeffdd20u;regs[129]=0xc0001000u;
 vector0=0xc00521b0u;record[0]=123;code=0;drop_vector=0;
}
int main(void){unsigned int i,b;
 /* Every stock table bit must be checked before any vector/ISP mutation. */
 for(i=0;i<64;i++)for(b=0;b<32;b++){
  baseline();regs[i]^=1u<<b;
  if(!setjmp(parked)){at_init();assert(!"corrupt stock accepted");}
  assert(code==0x7d011u&&vector0==0xc00521b0u&&regs[129]==0xc0001000u);
 }
 baseline();drop_vector=1;
 if(!setjmp(parked)){at_init();assert(!"failed vector write accepted");}
 assert(code==0x7d012u&&record[146]==1u);
 baseline();at_init();assert(record[146]==2&&record[147]&&record[31]==AT_READY);
 assert(vector0==0xc0711100u&&regs[129]==AT_IRQ_STACK+64);
 for(i=0;i<64;i++)assert(regs[i]==((i&1)?0:0xc0711000u));
 for(i=0;i<16;i++){
  stack[1024+i]^=1;assert(!at_irq_guard());stack[1024+i]^=1;
  stack[2032+i]^=1;assert(!at_irq_guard());stack[2032+i]^=1;
 }
 for(i=0;i<64;i++)for(b=0;b<32;b++){
  regs[i]^=1u<<b;assert(!at_owned_valid());regs[i]^=1u<<b;
 }
 record[1]=1;record[2]=AT_TRIGGER;record[0]=124;at_poll();
 record[0]=123;
 assert(at_owned_valid());
#if ACCELE_TERMINAL_TEST == 3
 if(!setjmp(parked)){at_poll();assert(!"real fault dispatch missed");}
#elif (ACCELE_TERMINAL_TEST == 5 || ACCELE_TERMINAL_TEST == 14)
 at_poll();assert(!code&&!record[166]); /* injection is never accepted */
 record[3]=124;record[4]=1;at_poll();assert(!record[166]);
 record[3]=123;at_poll();assert(record[166]==1&&record[170]==1&&record[167]==42);
 ticks=43;at_poll();assert(record[167]==42); /* no unsolicited mutation */
 record[4]=2;at_poll();assert(record[167]==43&&record[166]==2);
 at_runtime_snapshot(1);assert(record[171]==1&&record[170]==1);
 regs[0]^=1;record[4]=3;
 if(!setjmp(parked)){at_poll();assert(!"corrupt ownership accepted");}
 assert(code==0x7d019u);
#else
 regs[242]=0x7f;record[154]=0x7f;
 at_poll();assert(record[155]==1&&regs[242]==0x77);
 record[160]=2;regs[220]=0x100;regs[240]=0x80000000u;regs[241]=8;
 if(!setjmp(parked))accele_terminal_record();
 assert(record[151]==0x100&&record[152]==8&&record[153]==0x80000000u);
 assert(record[154]==0x77&&regs[242]==0x7f&&record[31]==AT_DONE);
#endif
 puts("owned table baseline: 2048 corruptions rejected; all entries, ISP/NMI and guards passed");
 return 0;
}

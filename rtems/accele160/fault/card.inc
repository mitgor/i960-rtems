#include "policy.h"
#ifndef AT_SYNC
#define AT_SYNC() __asm__ volatile("syncf":::"memory")
#endif
#ifndef AT_VECTOR0
static unsigned int at_vector0(void){unsigned int v;
 __asm__ volatile("ld 0,%0":"=r"(v)::"memory");return v;
}
#define AT_VECTOR0() at_vector0()
#endif
#ifndef AT_PARK
#define AT_PARK() for(;;)__asm__ volatile("":::"memory")
#endif
extern void accele_terminal_enter(unsigned int) __attribute__((noreturn));
#ifndef AT_BUFFER
#define AT_BUFFER ((volatile unsigned int*)AT_RECORD)
#endif
static volatile unsigned int * const at=AT_BUFFER;
static unsigned int at_nonce,at_initialized;
static unsigned int at_guard(void){unsigned int i;
 for(i=0;i<16;i++)if(REG(AT_STACK+i*4)!=AT_GUARD||
 REG(AT_END-64+i*4)!=AT_GUARD)return 0;
 return 1;
}
/* Only established read-only addresses. No CSR, timer mode, PCI config cycles,
 * doorbell/status clearing, or accesses to unknown SCSI register windows. */
static void at_snapshot(void){unsigned int i,ch;
 at[32]=REG(0xff008700u);at[33]=REG(0xff008704u);
 at[34]=AT_VECTOR0();at[35]=REG(4u);at[36]=REG(0xff008510u);
 at[37]=REG(0xff008500u);at[38]=REG(0xff008504u);
 at[39]=REG(0xff008520u);at[40]=REG(0xff008524u);at[41]=REG(0xff008528u);
 at[42]=REG(0xff000300u);at[43]=REG(0xff000304u);
 at[44]=REG(0xff000310u);at[45]=REG(0xff000314u);
 for(ch=0;ch<3;ch++)for(i=0;i<3;i++)
  at[48+ch*3+i]=REG(0x1400u+ch*64u+at_dma_offsets[i]);
 /* Fixed ROM PRCB identity, never dereference an arbitrary live pointer. */
 for(i=0;i<8;i++)at[64+i]=REG(0xfeffdd20u+i*4u);
 for(i=0;i<64;i++)at[80+i]=REG(0xc0000800u+i*4u);
}
#if ACCELE_TERMINAL_TEST >= 3
extern void accele_fault_entry(void),accele_nmi_entry(void);
extern void accele_raise_fault(void) __attribute__((noreturn));
#ifndef AT_SET_VECTOR0
static void at_set_vector0(unsigned int v){
 __asm__ volatile("st %0,0"::"r"(v):"memory");
}
#define AT_SET_VECTOR0(v) at_set_vector0(v)
#endif
static unsigned int at_irq_guard(void){unsigned int i;
 for(i=0;i<16;i++)if(REG(AT_IRQ_STACK+i*4)!=AT_GUARD||
 REG(AT_IRQ_END-64+i*4)!=AT_GUARD)return 0;
 return 1;
}
#ifndef AT_ENTRY_ADDRESS
#define AT_ENTRY_ADDRESS(fn) ((unsigned int)(fn))
#endif
static unsigned int at_owned_valid(void){unsigned int i;
 if(at[146]!=2u||!at_irq_guard()||AT_VECTOR0()!=at[149]||
    REG(0xff008704u)!=AT_IRQ_STACK+64u)return 0;
 for(i=0;i<64;i++)if(REG(0xc0000800u+4*i)!=((i&1u)?0u:at[148]))return 0;
 return 1;
}
static void at_install_owned(void){unsigned int i;
 at[144]=AT_VECTOR0();at[145]=REG(0xff008704u);
 at[148]=AT_ENTRY_ADDRESS(accele_fault_entry);
 at[149]=AT_ENTRY_ADDRESS(accele_nmi_entry);
 /* Exact captured stock baseline. No writes until every entry is verified. */
 if(REG(0xff008700u)!=0xfeffdd20u||REG(0xfeffdd20u)!=0xc0000800u||
    at[144]!=0xc00521b0u||at[145]!=0xc0001000u||
    (at[148]&15u)||(at[149]&3u))accele_terminal_enter(0x7d010u);
 for(i=0;i<64;i++)if(REG(0xc0000800u+4*i)!=
    ((i<32u&&!(i&1u))?0xc0053400u:0u))accele_terminal_enter(0x7d011u);
 for(i=0;i<1024;i++)REG(AT_IRQ_STACK+4*i)=AT_GUARD;
 at[146]=1u; /* From the first vector write, reset is required on failure. */
 AT_SET_VECTOR0(at[149]);AT_SYNC();
 if(AT_VECTOR0()!=at[149])accele_terminal_enter(0x7d012u);
 REG(0xff008704u)=AT_IRQ_STACK+64u;AT_SYNC();
 for(i=0;i<32;i++){
  REG(0xc0000800u+8*i)=at[148];REG(0xc0000804u+8*i)=0u;
 }
 AT_SYNC();
 if(REG(0xff008704u)!=AT_IRQ_STACK+64u)accele_terminal_enter(0x7d013u);
 for(i=0;i<64;i++)if(REG(0xc0000800u+4*i)!=((i&1u)?0u:at[148]))
  accele_terminal_enter(0x7d014u);
 at[147]=at_irq_guard();at[146]=2u;
#if ACCELE_TERMINAL_TEST == 4 || ACCELE_TERMINAL_TEST == 7 || ACCELE_TERMINAL_TEST == 9 || ACCELE_TERMINAL_TEST == 11 || ACCELE_TERMINAL_TEST == 13
 at[151]=REG(0x1700u);at[152]=REG(0x1324u);
 at[153]=REG(0x1320u);at[154]=REG(0x1328u);
 if(at[151]||(at[152]&8u)||(at[153]&0x80000000u))
  accele_terminal_enter(0x7d015u);
#endif
}
#endif
static void at_init(void){unsigned int i;
 at_nonce=at[0];
 for(i=16;i<AT_WORDS;i++)at[i]=0;
 for(i=0;i<1024;i++)REG(AT_STACK+i*4)=AT_GUARD;
 at[16]=AT_MAGIC;at[17]=at_nonce;at[18]=1u;at[25]=ACCELE_TERMINAL_TEST;
 at_initialized=1;
#if ACCELE_TERMINAL_TEST >= 3
 at_install_owned();
#endif
 at_snapshot();at[26]=at_guard();
 AT_SYNC();at[31]=AT_READY;
}
#if ACCELE_TERMINAL_TEST >= 6 && ACCELE_TERMINAL_TEST <= 13
static void at_dma_finish(void);
#endif
void accele_terminal_record(void){
 at[27]=ticks;at[28]=claimed;at[29]=switch_fault;
 at_snapshot();at[26]=at_guard();
#if ACCELE_TERMINAL_TEST >= 3
 at[147]=at_irq_guard();at[151]=REG(0x1700u);
 if(at[160]==2u){
  /* Save source before masking/acknowledging ONLY the test doorbell. */
  at[152]=REG(0x1324u);at[153]=REG(0x1320u);at[154]=REG(0x1328u);
#if ACCELE_TERMINAL_TEST == 4 || ACCELE_TERMINAL_TEST == 7 || ACCELE_TERMINAL_TEST == 9 || ACCELE_TERMINAL_TEST == 11 || ACCELE_TERMINAL_TEST == 13
  if(at[155]==1u){REG(0x1328u)=at[154]|8u;REG(0x1320u)=0x80000000u;AT_SYNC();}
#endif
 }
#endif
#if ACCELE_TERMINAL_TEST >= 6 && ACCELE_TERMINAL_TEST <= 13
 at_dma_finish();at[26]=at_guard();at[147]=at_irq_guard();
#endif
 claim_report[6]=0xf0000000u|at[20];
 /* No driver completion, STOP drain claim, timer restoration or return. */
 AT_SYNC();at[31]=AT_DONE;
 AT_PARK();
}
#if (ACCELE_TERMINAL_TEST == 5 || ACCELE_TERMINAL_TEST == 14 || ACCELE_TERMINAL_TEST == 15 || ACCELE_TERMINAL_TEST == 16 || ACCELE_TERMINAL_TEST == 17)
/* Host requests use words 3/4; ack 166 publishes a complete immutable sample.
 * No injection token is accepted by this profile. */
#if ACCELE_TERMINAL_TEST == 14 || ACCELE_TERMINAL_TEST == 15 || ACCELE_TERMINAL_TEST == 16 || ACCELE_TERMINAL_TEST == 17
#include "../ownership/inventory.h"
#if ACCELE_TERMINAL_TEST == 16 || ACCELE_TERMINAL_TEST == 17
#define QR_READ(a) REG(a)
#include "../ownership/qlogic_queue.h"
#endif
#if ACCELE_TERMINAL_TEST == 15 || ACCELE_TERMINAL_TEST == 17
#define Q_READ(a) REG(a)
#define Q_WRITE(a,v) do { REG(a)=(v); AT_SYNC(); } while(0)
#include "../ownership/qlogic_config.h"
#if ACCELE_TERMINAL_TEST == 17
#define QC_READ16(a) (*(volatile unsigned short *)(unsigned long)(a))
#include "../ownership/qlogic_chip.h"
#endif
#endif
#endif
static void at_runtime_snapshot(unsigned int phase){
 at_snapshot();at[26]=at_guard();at[147]=at_irq_guard();
 at[167]=ticks;at[168]=handoffs;at[169]=switch_fault;
 at[170]=at_owned_valid();at[171]=phase;
 if(!at[170]||!at[26]||at[169])accele_terminal_enter(0x7d019u);
#if ACCELE_TERMINAL_TEST == 14 || ACCELE_TERMINAL_TEST == 15 || ACCELE_TERMINAL_TEST == 16 || ACCELE_TERMINAL_TEST == 17
 at_engine_snapshot(at,at_nonce,at[4],phase);
#if ACCELE_TERMINAL_TEST == 16 || ACCELE_TERMINAL_TEST == 17
 at_qlogic_queue(at,at_nonce,at[4],phase);
#endif
#if ACCELE_TERMINAL_TEST == 15 || ACCELE_TERMINAL_TEST == 17
 at_qlogic_snapshot(at,at_nonce,at[4],phase);
#if ACCELE_TERMINAL_TEST == 17
 at_qlogic_chip(at,at_nonce,at[4],phase);
#endif
#endif
#endif
 AT_SYNC();at[166]=at[4];
}
#endif
#if ACCELE_TERMINAL_TEST >= 6 && ACCELE_TERMINAL_TEST <= 13
static void at_dma_test(void);
#endif
static void at_poll(void){
#if (ACCELE_TERMINAL_TEST == 5 || ACCELE_TERMINAL_TEST == 14 || ACCELE_TERMINAL_TEST == 15 || ACCELE_TERMINAL_TEST == 16 || ACCELE_TERMINAL_TEST == 17)
 if(at[3]==at_nonce && at_nonce && at[4] && at[4]!=at[166])
  at_runtime_snapshot(0u);
#endif
#if ACCELE_TERMINAL_TEST
 if(at_request(at[0],at[1],at[2],at_nonce,ACCELE_TERMINAL_TEST)){
#if ACCELE_TERMINAL_TEST >= 3
  if(!at_owned_valid())accele_terminal_enter(0x7d018u);
#endif
#if ACCELE_TERMINAL_TEST >= 6 && ACCELE_TERMINAL_TEST <= 13
  if(!at[184])at_dma_test();
  return;
#endif
#if ACCELE_TERMINAL_TEST == 3
  accele_raise_fault();
#endif
#if ACCELE_TERMINAL_TEST == 4 || ACCELE_TERMINAL_TEST == 7 || ACCELE_TERMINAL_TEST == 9 || ACCELE_TERMINAL_TEST == 11 || ACCELE_TERMINAL_TEST == 13
  if(!at[155]){
   if(REG(0x1700u)||(REG(0x1324u)&8u)||(REG(0x1320u)&0x80000000u))
    accele_terminal_enter(0x7d016u);
   REG(0x1328u)=at[154]&~8u;AT_SYNC();
   if(REG(0x1328u)!=(at[154]&~8u))accele_terminal_enter(0x7d017u);
   at[155]=1u;AT_SYNC();
  }
  return;
#endif
  if(ACCELE_TERMINAL_TEST==2)REG(AT_STACK)=0;
  accele_terminal_enter(ACCELE_TERMINAL_TEST==2?0x7d002u:0x7d001u);
 }
#endif
}

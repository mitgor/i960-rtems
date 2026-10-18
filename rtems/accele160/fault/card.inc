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
static void at_init(void){unsigned int i;
 at_nonce=at[0];
 for(i=16;i<AT_WORDS;i++)at[i]=0;
 for(i=0;i<1024;i++)REG(AT_STACK+i*4)=AT_GUARD;
 at[16]=AT_MAGIC;at[17]=at_nonce;at[18]=1u;at[25]=ACCELE_TERMINAL_TEST;
 at_snapshot();at[26]=at_guard();at_initialized=1;
 AT_SYNC();at[31]=AT_READY;
}
void accele_terminal_record(void){
 at[27]=ticks;at[28]=claimed;at[29]=switch_fault;
 at_snapshot();at[26]=at_guard();
 claim_report[6]=0xf0000000u|at[20];
 /* No driver completion, STOP drain claim, timer restoration or return. */
 AT_SYNC();at[31]=AT_DONE;
 AT_PARK();
}
static void at_poll(void){
#if ACCELE_TERMINAL_TEST
 if(at_request(at[0],at[1],at[2],at_nonce,ACCELE_TERMINAL_TEST)){
  if(ACCELE_TERMINAL_TEST==2)REG(AT_STACK)=0;
  accele_terminal_enter(ACCELE_TERMINAL_TEST==2?0x7d002u:0x7d001u);
 }
#endif
}

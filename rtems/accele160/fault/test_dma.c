/* Linux x86-64 native harness: compile -no-pie so card-sized pointers fit.
 * Executes the actual frame_dma.h diagnostic, with simulated MMIO only. */
#include <assert.h>
#include <setjmp.h>
#include <stdint.h>
#include <stdio.h>
static unsigned regs[4096],cfg[16],logwords[32],record[1024];
static unsigned char storage[131072] __attribute__((aligned(4096)));
static unsigned char *image_base=storage+16;
static unsigned claimed=1,ticks,reads,finish_after=~0u,forced_error;
#if ACCELE_TERMINAL_TEST == 10
static unsigned switch_fault,resume_complete,resume_reads;
static unsigned at_guard(void){return 1;}
#endif
static volatile unsigned *at=record;
static jmp_buf escape;
static unsigned *reg(unsigned a){
 assert(a<sizeof(regs));
 if(a==0x1404 && (regs[0x1400/4]||record[195])){
#if ACCELE_TERMINAL_TEST >= 8
  if(!regs[0x140c/4]){regs[0x140c/4]=record[180];regs[0x1410/4]=record[180]+32;regs[0x1420/4]=65536;regs[0x1424/4]=7;}
#endif
  regs[a/4]=++reads<finish_after?0x400:0;
  regs[a/4]|=forced_error;
#if ACCELE_TERMINAL_TEST == 10
  if(record[208]==2 && regs[0x1400/4] && resume_complete && ++resume_reads==3){
   regs[a/4]=0;regs[0x140c/4]=record[180]+32768;
   regs[0x1410/4]=regs[0x1420/4]=0;
  }
#endif
 }
 return &regs[a/4];
}
#define REG(a) (*reg(a))
#ifndef ACCELE_TERMINAL_TEST
#define ACCELE_TERMINAL_TEST 6
#endif
#define DMA_CFG_PTR cfg
#define DMA_LOG_PTR logwords
#define DMA_SYNC() ((void)0)
#define BRIDGE_EPOCH 0x161610e1u
#define FRAME_BYTES 65536u
#define RTEMS_SUCCESSFUL 0
static int rtems_task_wake_after(unsigned x){(void)x;return 0;}
static void priority0(void){}
static unsigned dma_busy_mask(void){return 0;}
static unsigned at_owned_valid(void){return 1;}
static void bounded_fatal(unsigned x){(void)x;longjmp(escape,3);}
static void accele_terminal_enter(unsigned x){(void)x;longjmp(escape,4);}
static void accele_raise_fault(void){longjmp(escape,2);}
static unsigned byte_fnv(const volatile unsigned char*p,unsigned n){unsigned h=2166136261u;
 while(n--)h=(h^*p++)*16777619u;
 return h;}
#include "frame_dma.h"
int main(void){
 unsigned i;assert((uintptr_t)storage<0xffffffffu);
 cfg[0]=0x31464d44;cfg[1]=BRIDGE_EPOCH;cfg[2]=0x10000000;cfg[3]=0x20000000;
 cfg[4]=65536;cfg[5]=0x314d5241;cfg[6]=32;
 int rc=setjmp(escape);if(!rc)at_dma_test();assert(rc==2);
 assert(at[181]==(uintptr_t)storage+4096 && at[180]==at[181]+65536);
 assert(at[183]==1024 && at[184]==0x400);
 for(i=0;i<65536;i++)assert(storage[4096+i]==(unsigned char)(i^(i>>8)^0x69));
 unsigned *d=(unsigned*)(uintptr_t)at[180];
 for(i=0;i<1025;i++){
  assert(d[i*8]==(i==1024?0:at[180]+(i+1)*32));
  assert(d[i*8+1]==cfg[2]+(i==1024?65536:0));
  assert(d[i*8+3]==(i==1024?at[185]:at[181]));
  assert(d[i*8+4]==(i==1024?32:65536));
  assert(d[i*8+5]==7 && !d[i*8+2] && !d[i*8+6] && !d[i*8+7]);
 }
#if ACCELE_TERMINAL_TEST >= 8
 assert(at[195]==1 && at[203]==4096 && at[197]==0);
#endif
#if ACCELE_TERMINAL_TEST == 10
 at[160]=1;at[20]=0x7d003;
 /* First: actual timeout followed by another bounded resume timeout. */
 at_dma_finish();assert(at[175]==10000000 && at[208]==2 && at[210]==10000000);
 assert(regs[0x1400/4]==1 && at[211]==0x400);
 /* Every gate rejection leaves CE off; an attempt cannot be retried. */
 unsigned fields[]={160,20,175,195,203,186,187,191,183,184,194,192,193,188,189,190};
 for(i=0;i<sizeof(fields)/sizeof(fields[0]);i++){
  unsigned k=fields[i],old=at[k];at[208]=0;at[k]^=1;regs[0x1400/4]=0;
  at_dma_resume();assert(at[208]==1 && !regs[0x1400/4]);at[k]=old;
  at_dma_resume();assert(at[208]==1 && !regs[0x1400/4]);
 }
 at[208]=0;switch_fault=1;at_dma_resume();assert(at[208]==1 && !regs[0x1400/4]);switch_fault=0;
 at[208]=0;forced_error=8;at_dma_resume();assert(at[208]==1 && !regs[0x1400/4]);forced_error=0;
 /* Complete the same chain after CE resume, retaining original timeout. */
 at[208]=0;resume_complete=1;at_dma_resume();
 assert(at[208]==3 && at[210]==2 && at[211]==0 && at[213]==at[180]+32768);
 assert(at[175]==10000000 && at[186]==0x400 && at[187]==0);
 assert(at[217]==at[204] && at[218]==at[205] && at[219] && at[220]);
 puts("actual CE resume: gates reject, retries blocked, bounded re-timeout and completion retain original evidence (simulated)");
#else
 /* A stuck active engine exhausts a finite bound and stays enabled/retained. */
 at_dma_finish();assert(at[175]==10000000 && at[186]==0x400 && at[187]==(ACCELE_TERMINAL_TEST>=8?0:1));
 finish_after=reads+3;at_dma_finish();assert(at[175]==2 && at[186]==0 && at[187]==(ACCELE_TERMINAL_TEST>=8?0:1));
 assert(at[192]==byte_fnv(storage+4096,65536) && at[193]==byte_fnv((void*)(uintptr_t)at[180],32800) && at[194]==1);
 forced_error=8;at_dma_finish();assert(at[175]==0 && at[186]==8 && at[187]==(ACCELE_TERMINAL_TEST>=8?0:1));
 puts("actual diagnostic: aligned bounded chain, inactive completion, error and 10M-poll timeout retain DMA ownership (simulated)");
 #endif
 return 0;
}

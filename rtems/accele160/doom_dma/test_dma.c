#include <assert.h>
#include <setjmp.h>
#include <string.h>
#include <stdio.h>
static unsigned regs[3*16],cfg[16],log_words[32],ticks,error;
static jmp_buf escaped;
#define REG(a) regs[((a)-0x1400u)/4u]
#define BRIDGE_EPOCH 0x161610e1u
#define FRAME_BYTES 65536u
#define DMA_CFG_PTR cfg
#define DMA_LOG_PTR log_words
#define DMA_SYNC() do{}while(0)
#define RTEMS_SUCCESSFUL 0
static unsigned dma_busy_mask(void){return !!(regs[0]||regs[4]||regs[8]);}
static void bounded_fatal(unsigned n){error=n;longjmp(escaped,1);}
static int rtems_task_wake_after(unsigned n){ticks+=n;return 0;}
static void priority0(void){}
#include "frame_dma.h"
static void reset(void){
 memset(regs,0,sizeof regs);memset(cfg,0,sizeof cfg);memset(log_words,0,sizeof log_words);
 dma_initialized=dma_phase=dma_completed=ticks=error=0;
 cfg[0]=0x31464d44;cfg[1]=BRIDGE_EPOCH;cfg[2]=0x100000;cfg[3]=0x200000;
 cfg[4]=65536;cfg[5]=0x314d5241;cfg[6]=4;
}
static void complete(void){regs[0]=1;regs[1]=0;regs[3]=dma_desc_addr()+32;regs[4]=regs[8]=0;regs[9]=7;dma_step();}
int main(void){unsigned d;volatile unsigned *desc;
 reset();cfg[7]=1;dma_init();assert(dma_initialized);ticks=97;
 dma_kick(1,0,(void*)0xc0901000,0x12345678,91);d=dma_desc_addr();desc=(void*)d;
 assert(regs[0]==1&&regs[4]==d&&dma_phase==1);
 assert(desc[0]==d+32&&desc[1]==cfg[2]&&desc[3]==0xc0901000&&desc[4]==65536&&desc[5]==7);
 assert(desc[8]==0&&desc[9]==cfg[2]+65536&&desc[11]==(unsigned)dma_marker&&desc[12]==32&&desc[13]==7);
 assert(dma_marker[0]==0x31505044&&dma_marker[2]==1&&dma_marker[7]==~1u&&dma_marker[6]==91);
 complete();assert(!dma_phase&&!regs[0]&&dma_completed==1);
 dma_kick(2,1,(void*)0xc0911000,1,92);assert(desc[1]==cfg[3]&&dma_marker[2]==2);complete();assert(dma_completed==2);
 reset();cfg[3]=cfg[2]+4096;if(!setjmp(escaped)){dma_init();assert(0);}assert(error==0x78004);
 reset();cfg[2]++;if(!setjmp(escaped)){dma_init();assert(0);}assert(error==0x78003);
 reset();dma_init();regs[16+7]=3;if(!setjmp(escaped)){dma_peer_check();assert(0);}assert(error==0x78001);
 reset();dma_init();dma_kick(1,0,(void*)0xc0901000,1,93);regs[1]=0x400;ticks=50;
 if(!setjmp(escaped)){dma_step();assert(0);}assert(error==0x78009&&regs[0]==1&&dma_phase==1);
 reset();dma_init();dma_kick(1,0,(void*)0xc0901000,1,93);regs[1]=0x401;
 if(!setjmp(escaped)){dma_step();assert(0);}assert(error==0x78007&&regs[0]==1&&dma_phase==1);
 puts("DMA descriptor chain, reuse, marker, peer isolation, admission and timeout/error retention passed");
}

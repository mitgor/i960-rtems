#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
static unsigned regs[48],dma_store[24] __attribute__((aligned(32))),dma_marker[8],dma_bus[2]={0x100000,0x200000},logbuf[32],*dma_log=logbuf;
static unsigned game_idle=1,engine_running,dma_initialized=1,dma_phase,mode,error,peer_checks;
static jmp_buf done;
static unsigned dma_desc_addr(void){return (unsigned)dma_store;}
static unsigned *reg(unsigned addr){
 if(addr==0x1404&&regs[0]){
  if(mode==0){regs[1]=0;regs[3]=dma_desc_addr()+32;regs[4]=regs[8]=0;regs[9]=7;}
  else regs[1]=mode==1?0x400:0x401;
 }
 return regs+(addr-0x1400)/4;
}
#define REG(a) (*reg(a))
#define FRAME_BYTES 65536u
#define DMA_SYNC() do{}while(0)
static void bounded_fatal(unsigned v){error=v;longjmp(done,1);}
static void dma_peer_check(void){peer_checks++;}
#include "packet_dma.h"
static void reset(void){memset(regs,0,sizeof regs);memset(logbuf,0,sizeof logbuf);regs[3]=dma_desc_addr()+32;regs[9]=7;mode=error=packet_dma_completed=peer_checks=0;game_idle=1;}
int main(void){
 reset();packet_dma_reply(5,23,(void*)0xc077b000);
 assert(!regs[0]&&packet_dma_completed==1&&peer_checks==2&&!dma_log[18]);
 assert(dma_store[4]==4096&&dma_store[1]==dma_bus[0]&&dma_store[9]==dma_bus[0]+65536);
 assert(dma_marker[0]==0x31525044&&dma_marker[2]==5&&dma_marker[5]==0xc077b000&&dma_marker[7]==~5u);
 packet_dma_reply(6,23,(void*)0xc077b000);assert(packet_dma_completed==2&&dma_log[11]==0);
 reset();mode=1;if(!setjmp(done)){packet_dma_reply(1,23,(void*)0xc077b000);assert(0);}assert(error==0x78104&&regs[0]==1&&dma_log[18]==1&&!packet_dma_completed);
 reset();mode=2;if(!setjmp(done)){packet_dma_reply(1,23,(void*)0xc077b000);assert(0);}assert(error==0x78103&&regs[0]==1&&dma_log[18]==1);
 reset();game_idle=0;if(!setjmp(done)){packet_dma_reply(1,23,(void*)0xc077b000);assert(0);}assert(error==0x78101&&!regs[0]);
 puts("packet DMA: finite chain, exact marker, retired-game gate, reuse and error/timeout retention passed");
}

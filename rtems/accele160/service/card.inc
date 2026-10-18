/* This worker performs only bounded scalar reads, never heap walks or DMA
 * register reads. Its IRQ continuation already belongs to worker 0. */
#define SVC_SYNC() __asm__ volatile("syncf":::"memory")
#include "protocol.h"
static struct svc_state service_state;
static volatile unsigned int * const service_wire=(volatile unsigned int*)0xc0775000u;
static void service_init(void){
 unsigned int i;
 service_state.epoch=service_wire[2];
 for(i=0;i<1024u;i++)service_wire[i]=0;
 service_wire[18]=service_state.epoch;service_wire[24]=SVC_MAGIC;
}
static void service_poll(void){
 unsigned int v[24],i;
 if(!service_wire[0] || service_wire[0]==service_wire[16])return;
 v[0]=ticks;v[1]=handoffs;v[2]=switch_fault;v[3]=switch_stop;
 for(i=0;i<4u;i++){v[4+i]=switch_threads[i];v[8+i]=switch_active[i];}
 v[12]=RTEMS_WORKSPACE_BYTES;v[13]=ARENA_END-ARENA_BASE;v[14]=7;
 v[15]=zone_loaned;v[16]=game_run;v[17]=engine_running;v[18]=game_idle;
 v[19]=transport_frame;v[20]=wad_good;v[21]=wad_bad;v[22]=dma_completed;v[23]=loops[0];
 svc_poll(&service_state,service_wire,v);
}

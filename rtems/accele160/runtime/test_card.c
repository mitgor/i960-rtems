#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "runtime.h"
#define ACCELE_SERVICE 1
#define STOP 0x504f5453u
static unsigned ticks,game_idle,engine_running,control[4],wire[1024],cache_syncs;
static struct arena doom_arena;
static unsigned zone_loaned,zone_handle;
#define ZONE_BYTES (6u*1024u*1024u)
static unsigned char storage[AR_BYTES+64] __attribute__((aligned(16)));
static unsigned little_word(const unsigned char *p){return p[0]|p[1]<<8|p[2]<<16|(unsigned)p[3]<<24;}
static unsigned mock(unsigned op,unsigned ms,const unsigned char*in,unsigned n,unsigned char*out,unsigned cap);
#define AR_WIRE wire
#define AR_SYNC() do {} while(0)
#define AR_ICACHE(scratch) do { scratch=0;cache_syncs++; } while(0)
#define AR_INVOKE(entry,op,ms,in,n,out,cap) ((void)(entry),mock(op,ms,in,n,out,cap))
#include "card.inc"
static unsigned mock(unsigned op,unsigned ms,const unsigned char*in,unsigned n,unsigned char*out,unsigned cap){
 assert(app_runtime.busy&&app_runtime.image.state==SEG_RUNNING&&ms<=1000);
 assert(!ar_close(&app_runtime));
 if(op==2){assert(cap>=n);memcpy(out,in,n);return n;}
 return 0;
}
static void request(unsigned op,const void *p,unsigned n){
 memset(wire+1,0,15*4);wire[1]=app_runtime.epoch;wire[2]=op;wire[3]=n;
 if(n)memcpy(wire+16,p,n);wire[4]=seg_crc32(0,p,n);wire[0]++;app_poll();
}
int main(void){unsigned char b[1024]={0};unsigned seq;
 struct manifest m={1,2,0,{{0,16,16,SEG_RX,0},{16,0,32,SEG_RW,0}}};
 unsigned request_manifest[3+sizeof(m)/4];
 assert(arena_init(&doom_arena,storage,sizeof(storage)));app_init(23);
 request(7,0,0);assert(!wire[417]);game_idle=1;app_poll();assert(wire[417]==1&&!wire[418]);
 wire[1]=24;wire[0]++;app_poll();assert(wire[418]==1&&!app_runtime.reservation);
 wire[0]--;wire[1]=23;
 request(7,0,0);assert(!wire[418]);
 memset(b,0,184);request(1,b,184);assert(wire[418]==5&&!app_runtime.reservation);
 request(7,0,0);assert(!wire[418]); /* authenticated refusal consumed its sequence */
 wire[0]++;wire[1]=app_runtime.epoch;wire[3]=1501;app_poll();assert(wire[418]==3);
 request(7,0,0);assert(!wire[418]);
 wire[0]++;wire[15]=1;app_poll();assert(wire[418]==3);
 request(7,0,0);assert(!wire[418]);
 wire[0]++;wire[3]=1;((unsigned char*)(wire+16))[0]=42;wire[4]=0;app_poll();assert(wire[418]==4);
 request(7,0,0);assert(!wire[418]);
 m.segment[0].crc32=seg_crc32(0,b,16);
 request_manifest[0]=AR_BOARD;request_manifest[1]=AR_ABI;
 /* Native pointer width is wider than the card wire. Reserve directly and use
  * segmented core for the pointer-width-dependent begin; card begin is built
  * and checked with the actual 32-bit compiler. */
 (void)request_manifest;
 assert(ar_reserve(&app_runtime,&doom_arena));assert(ar_begin(&app_runtime,AR_BOARD,AR_ABI,(unsigned long)app_runtime.modules.base+16,&m));
 memset(b,0,24);request(2,b,24);assert(!wire[418]);
 do{request(3,0,0);assert(!wire[418]);}while(wire[420]==1);
 assert(wire[420]==2&&cache_syncs==1);request(4,0,0);assert(app_started&&!wire[418]);
 ticks=200;seq=wire[417];app_poll();assert(wire[417]==seq&&app_tick==100);app_poll();assert(app_tick==200);
 request(5,"echo",4);assert(wire[420]==4&&!memcmp(wire+432,"echo",4));
 seq=app_runtime.calls;app_poll();assert(app_runtime.calls==seq); /* duplicate */
 request(6,0,0);assert(!app_started&&!app_runtime.reservation&&app_runtime.epoch==24);
 puts("actual application card adapter: idle gate, epochs, upload chunks, incremental verification, cache sync, busy retention, bounded timer catch-up, packet reply, duplicate and close passed");return 0;
}

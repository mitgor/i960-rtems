/* Opt-in integration with the existing Init task. The diagnostic worker keeps
 * its independent IRQ stack. Only Init calls this loader/allocator/lwIP owner.
 * Host must serialize with Doom through the existing owning runner. */
#if !ACCELE_SERVICE
#error application runtime requires the owned console service
#endif
#include "../runtime/runtime.h"
static struct ar_runtime app_runtime;
static unsigned int app_sequence,app_started,app_tick;
#ifndef AR_WIRE
#define AR_WIRE ((volatile unsigned int*)0xc077b000u)
#endif
#ifndef AR_SYNC
#define AR_SYNC() __asm__ volatile("syncf":::"memory")
#define AR_ICACHE(scratch) __asm__ volatile("icctl 2,0,%0":"=r"(scratch)::"memory")
#endif
#ifndef AR_INVOKE
#define AR_INVOKE(entry,op,ms,in,n,out,cap) entry(op,ms,in,n,out,cap)
#endif
static volatile unsigned int * const app_wire=AR_WIRE;
typedef unsigned int (*ar_entry)(unsigned int,unsigned int,const unsigned char*,unsigned int,unsigned char*,unsigned int);
static int app_cache_sync(void *p,unsigned int n){unsigned int scratch;
 (void)p;(void)n;AR_SYNC();AR_ICACHE(scratch);(void)scratch;return 1;
}
static unsigned int app_call(unsigned int op,const unsigned char *in,unsigned int n,unsigned char *out,unsigned int cap){
 ar_entry entry;unsigned int result,delta=ticks-app_tick;
 if(!ar_valid(&app_runtime)||app_runtime.busy)return 0xffffffffu;
 entry=(ar_entry)seg_start(&app_runtime.image);if(!entry)return 0xffffffffu;
 app_runtime.busy=1;
 /* Timer catch-up is bounded; a delayed caller advances at most 1 s per call. */
 if(delta>100u)delta=100u;
 result=AR_INVOKE(entry,op,delta*10u,in,n,out,cap);app_tick+=delta;
 app_runtime.busy=0;app_runtime.calls++;
 if(!seg_complete(&app_runtime.image)){seg_uncertain(&app_runtime.image);return 0xffffffffu;}
 return result;
}
static void app_init(unsigned int epoch){unsigned int i;
 for(i=0;i<1024u;i++)app_wire[i]=0;
 ar_init(&app_runtime,epoch);app_sequence=app_started=0;app_tick=ticks;
 app_wire[416]=0x31525041u;app_wire[419]=epoch;
}
static void app_poll(void){
 unsigned int seq=app_wire[0],op=app_wire[2],n=app_wire[3],i,status=0,value=0;
 unsigned char input[1500];unsigned char *out=(unsigned char*)(app_wire+432);
 /* Module code is trusted and must return. Uncertain execution is never freed.
  * The service cannot run while Doom holds its application context. */
 if(!game_idle||engine_running||control[3]==STOP)return;
 if(app_started&&ticks!=app_tick){
  if(app_call(1,0,0,0,0)!=0){app_runtime.poisoned=1;app_started=0;}
 }
 if(!seq||seq==app_sequence)return;
 if(app_wire[1]!=app_runtime.epoch||!app_runtime.epoch){status=1;goto reply;}
 if(app_sequence==0xffffffffu||seq!=app_sequence+1u){status=2;goto reply;}
 app_sequence=seq; /* Every authenticated next sequence is consumed, including refusal. */
 if(n>sizeof(input)){status=3;goto reply;}
 for(i=5;i<16;i++)if(app_wire[i]){status=3;goto reply;}
 for(i=0;i<n;i++)input[i]=((volatile unsigned char*)(app_wire+16))[i];
 if(seg_crc32(0,input,n)!=app_wire[4]){status=4;goto reply;}
 if(op==1){ /* begin: board, ABI, exact link base, fixed-size segment manifest */
  struct manifest m;unsigned int board,abi,base;
  if(n!=184u||app_started){status=5;goto reply;}
  /* Five LE words per segment on the wire. i960 GCC pads this C struct to
   * 32 bytes, so never memcpy a host manifest into native structures. */
  m.abi=little_word(input+12);m.count=little_word(input+16);m.entry=little_word(input+20);
  for(i=0;i<SEG_MAX;i++){
   unsigned int off=24u+i*20u;
   m.segment[i].offset=little_word(input+off);
   m.segment[i].file_bytes=little_word(input+off+4);
   m.segment[i].memory_bytes=little_word(input+off+8);
   m.segment[i].flags=little_word(input+off+12);
   m.segment[i].crc32=little_word(input+off+16);
   if(i>=m.count&&(m.segment[i].offset||m.segment[i].file_bytes||m.segment[i].memory_bytes||m.segment[i].flags||m.segment[i].crc32)){status=5;goto reply;}
  }
  board=little_word(input);abi=little_word(input+4);base=little_word(input+8);
  if(board!=AR_BOARD||abi!=AR_ABI){status=5;goto reply;}
  if(!app_runtime.reservation&&!ar_reserve(&app_runtime,&doom_arena)){status=6;goto reply;}
  if(!ar_begin(&app_runtime,board,abi,base,&m))status=7;
 }else if(op==2){ /* chunk: segment index, offset, <=1016 bytes */
  if(n<=8||!seg_write(&app_runtime.image,little_word(input),little_word(input+4),input+8,n-8))status=8;
 }else if(op==3){if(n){status=3;goto reply;}value=seg_prepare(&app_runtime.image,app_cache_sync);if(!value)status=9;
 }else if(op==4){if(n||app_started){status=10;goto reply;}app_tick=ticks;value=app_call(0,0,0,0,0);if(value)status=10;else app_started=1;
 }else if(op==5){if(!app_started){status=11;goto reply;}value=app_call(2,input,n,out,2048);if(value>2048){status=11;value=0;}
 }else if(op==6){if(n){status=3;goto reply;}if(!ar_close(&app_runtime))status=12;else app_started=0;
 }else if(op==7){if(n){status=3;goto reply;}if(app_started){value=app_call(3,0,0,out,2048);if(value>2048){status=11;value=0;}}
 }else if(op==8){if(n){status=3;goto reply;}value=ar_heap_proof(&app_runtime);if(value!=255u)status=14;
 }else status=13;
 app_sequence=seq;
reply:
 app_wire[418]=status;app_wire[419]=app_runtime.epoch;app_wire[420]=value;
 app_wire[421]=app_runtime.image.state;app_wire[422]=app_runtime.reservation;
 app_wire[423]=app_runtime.busy;app_wire[424]=app_runtime.poisoned;
 app_wire[425]=app_runtime.calls;app_wire[426]=app_started;
 AR_SYNC();app_wire[417]=seq;
}

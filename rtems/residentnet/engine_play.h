/* Interactive ownership: one published immutable frame; an admitted two-slot
 * producer may prepare one further frame before waiting for the published ACK.
 * IRQ only reads immutable bytes and appends bounded key events. No host address
 * is accepted. The image stays pinned until the owned invocation has returned. */
#ifdef ENGINE_PLAYABLE
static unsigned char *play_allowed;
static const struct doom_runtime_owned *play_api;
static unsigned char *volatile play_frame;
static volatile unsigned play_sequence,play_ack,play_head,play_tail;
static unsigned play_keys[32];
static unsigned play_selected,play_offset,play_window;
#ifdef I960_DOOM_DMA
#include "../dma/frame_target.h"
#endif
static void play_clear(void){
#ifdef I960_DOOM_DMA
#ifdef ENGINE_PINGPONG
 if(pp_active&&fd_phase==1)fd_step();
#endif
 unsigned pc=FD_LOCK();
 if(fd_phase==1){FD_FATAL();for(;;){}} /* Never release a queued/active DMA pin. */
#endif
 play_frame=0;play_selected=play_window=0;
#ifdef I960_DOOM_DMA
 FD_UNLOCK(pc);
#endif
}
/* Only the engine task services DMA. A dual-buffer producer can render into
 * the other slot while this immutable published slot is being read by host. */
static int play_wait(void){unsigned start=play_api->io.ticks_ms(),polls=0;
 while(play_frame&&!play_ack){
#ifdef I960_DOOM_DMA
#ifdef ENGINE_PINGPONG
  pp_service();
#else
  fd_step();
#endif
#endif
  if(play_api->stopping()||play_api->io.ticks_ms()-start>=60000||++polls>=10000000u){play_clear();return -1;}
  {extern void doom_shared_service(void);doom_shared_service();}
  if(!(polls&1023u))doom_shared_yield();
 }
 play_clear();return 1;
}
int engine_play_mark(unsigned stage,unsigned x,unsigned y,unsigned z){
 if(!play_api||!play_api->owner()||play_api->stopping())return -1;
#ifdef ENGINE_CPU_PROFILE
 if(stage==102){extern unsigned doom_profile_samples(void);return (int)doom_profile_samples();}
#endif
 if(stage==101){unsigned t=play_tail,v;
#ifdef ENGINE_PLAY_DOUBLE
#ifdef I960_DOOM_DMA
#ifdef ENGINE_PINGPONG
  pp_service();
#else
  fd_step();
#endif
#endif
#endif
  if(t==play_head)return 1;v=play_keys[t];play_tail=(t+1)&31;return (int)v+2;
 }
 if(stage!=100)return 1;
 if(y!=65536||!z||z!=play_sequence+1)return 0;
#ifdef ENGINE_PLAY_DOUBLE
 if((unsigned long)(play_allowed+((z-1)&1)*65536)!=x)return 0;
 if(play_wait()<0)return -1;
#else
 if((unsigned long)play_allowed!=x||play_frame)return 0;
#endif
 play_ack=0;play_sequence=z;play_selected=play_window=0;
 __asm__ volatile("":::"memory");play_frame=(unsigned char*)(unsigned long)x;
#ifdef ENGINE_PINGPONG
 pp_service();
#endif
#ifdef ENGINE_PLAY_DOUBLE
 return 1;
#else
 return play_wait();
#endif
}
unsigned engine_play_control(unsigned index,unsigned value){
 #ifdef I960_DOOM_DMA
#ifdef ENGINE_PINGPONG
 if(index>=8&&index<=12)return pp_control(index,value);
 if(pp_active&&index==1)return ~0u;
#endif
 if(index>=3&&index<=6)return fd_control(index,value);
#ifdef ENGINE_FRAME_PROFILE
 if(index==7)return fd_control(index,value);
#endif
 if(index==1&&fd_phase==1)return ~0u;
#endif
 if(index==0)return play_frame?play_sequence:0;
 if(!play_api||!play_frame)return ~0u;
 if(index==1){if(!value||value!=play_sequence||play_ack)return ~0u;play_ack=1;return 0;}
 if(index==2){unsigned n=(play_head+1)&31;if(value>511||n==play_tail)return ~0u;play_keys[play_head]=value;play_head=n;return 0;}
 return ~0u;
}
unsigned engine_frame_control(unsigned op,unsigned index,unsigned value){
 if(!play_frame||play_ack)return ~0u;
 if(op==0x6c){play_selected=play_window=0;if(index||value!=play_sequence)return ~0u;play_selected=value;return 0;}
 if(play_selected!=play_sequence)return ~0u;
 if(op==0x6d){play_window=0;if(index||(value&1023)||value>65536-1024)return ~0u;play_offset=value;play_window=1;return 0;}
 if(op==0x6e&&play_window&&index<256&&!value)return word(play_frame+play_offset+index*4);
 return ~0u;
}
/* The caller owns the four MU words for the entire exchange. Reuse IMR0
 * for the second result only after its zero request value has been consumed.
 * No RAM aperture, DMA address or additional target pointer crosses the ABI. */
unsigned engine_frame_pair(unsigned index,unsigned value,unsigned *second){
 if(!play_frame||play_ack||play_selected!=play_sequence||!play_window||index>=128||value)return ~0u;
 *second=word(play_frame+play_offset+index*8+4);
 return word(play_frame+play_offset+index*8);
}
unsigned engine_frame_finish(void){return !play_api&&!play_frame;}
#else
int engine_play_mark(unsigned s,unsigned x,unsigned y,unsigned z){(void)s;(void)x;(void)y;(void)z;return 0;}
unsigned engine_play_control(unsigned i,unsigned v){(void)i;(void)v;return ~0u;}
#endif

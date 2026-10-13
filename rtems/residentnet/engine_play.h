/* Interactive ownership: the renderer blocks while its single frame is visible.
 * IRQ only reads immutable bytes and appends bounded key events. No host address
 * is accepted. The image stays pinned until the owned invocation has returned. */
#ifdef ENGINE_PLAYABLE
static unsigned char *play_allowed;
static const struct doom_runtime_owned *play_api;
static unsigned char *volatile play_frame;
static volatile unsigned play_sequence,play_ack,play_head,play_tail;
static unsigned play_keys[32];
static unsigned play_selected,play_offset,play_window;
static void play_clear(void){play_frame=0;play_selected=play_window=0;}
int engine_play_mark(unsigned stage,unsigned x,unsigned y,unsigned z){unsigned start,polls=0;
 if(!play_api||!play_api->owner()||play_api->stopping())return -1;
 if(stage==101){unsigned t=play_tail,v;if(t==play_head)return 1;v=play_keys[t];play_tail=(t+1)&31;return (int)v+2;}
 if(stage!=100)return 1;
 if((unsigned long)play_allowed!=x||y!=65536||!z||z!=play_sequence+1||play_frame)return 0;
 play_ack=0;play_sequence=z;play_selected=play_window=0;
 __asm__ volatile("":::"memory");play_frame=play_allowed;start=play_api->io.ticks_ms();
 while(!play_ack){
  if(play_api->stopping()||play_api->io.ticks_ms()-start>=60000||++polls>=10000000u){play_clear();return -1;}
  {extern void doom_shared_service(void);doom_shared_service();}
  if(!(polls&1023u))doom_shared_yield();
 }
 play_clear();return 1;
}
unsigned engine_play_control(unsigned index,unsigned value){
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
unsigned engine_frame_finish(void){return !play_api&&!play_frame;}
#else
int engine_play_mark(unsigned s,unsigned x,unsigned y,unsigned z){(void)s;(void)x;(void)y;(void)z;return 0;}
unsigned engine_play_control(unsigned i,unsigned v){(void)i;(void)v;return ~0u;}
#endif

/* Execute the actual target adapter through a bounded native owner/mark API.
 * Linux -m32 supplies the same pointer width; no MMIO or hardware is modeled. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../../doom/runtime/startup/checkpoint_api.h"
#define ENGINE_RESULT 0xf00u
#define ENGINE_PLAY_OFFSET 0xff0u
#define FRAME_BYTES 65536u
static unsigned char *image_base;
static unsigned now,frames,stop,input;
static unsigned little_word(const unsigned char*p){return p[0]|(unsigned)p[1]<<8|(unsigned)p[2]<<16|(unsigned)p[3]<<24;}
#include "entry.h"
static unsigned owner(void){return 1;}
static unsigned stopping(void){return stop;}
static unsigned clock_ms(void){return now;}
static int wait_ms(unsigned ms){assert(ms==1);now+=10;return stop?-1:0;}
static int mark(unsigned stage,unsigned x,unsigned n,unsigned g){
 if(stage==101){if(input<2)return (int)((input++?3:259)+2);return 1;}
 assert(stage==100 && n==65536 && g==++frames);
 assert(x==(unsigned)(image_base+ENGINE_PLAY_OFFSET+((g-1)&1)*65536));
 {const unsigned char*p=(const unsigned char*)x;unsigned i;
  assert(little_word(p)==C8_MAGIC && little_word(p+304)==C8_PLAYER_MAGIC && little_word(p+312)==g);
  for(i=512;i<65536;i++)assert(p[i]==0);
 }
 if(frames==8)stop=1;return 1;
}
static void put(unsigned char*p,unsigned v){p[0]=v;p[1]=v>>8;p[2]=v>>16;p[3]=v>>24;}
int main(void){struct doom_runtime_checkpoint a;unsigned ret;unsigned char original[32];
 image_base=calloc(1,0xff0+2*65536);assert(image_base);memset(&a,0,sizeof a);
 a.base.io.magic=DOOM_API_MAGIC;a.base.io.version=DOOM_API_BATCH_VERSION;a.base.io.bytes=sizeof(a.base.io);
 a.base.io.pointer_bytes=sizeof(void*);a.base.io.little_endian=1;a.base.magic=DOOM_OWNED_MAGIC;
 a.base.version=DOOM_CHECKPOINT_VERSION;a.base.bytes=sizeof(a);a.base.features=DOOM_CHECKPOINT_FEATURES;
 a.base.io.ticks_ms=clock_ms;a.base.owner=owner;a.base.stopping=stopping;a.base.wait_ms=wait_ms;a.mark=mark;
 put(image_base,0x314d5243);put(image_base+4,4);put(image_base+8,1);put(image_base+12,500);
 image_base[16]=0xf0;image_base[17]=0x0a;image_base[18]=0x12;image_base[19]=0x00;
 memcpy(original,image_base,32);ret=chip8_entry(&a.base);
 assert(ret==0x43384702 && frames==8 && !memcmp(original,image_base,32));
 assert(chip8_player.guest.v[0]==3 && chip8_player.held==0 && chip8_player.input_seen==2);
 assert(little_word(image_base+ENGINE_RESULT)==0x31453843 && little_word(image_base+ENGINE_RESULT+20)==8);
 assert(little_word(image_base+ENGINE_RESULT+40)==1);
 frames=0;input=0;now=0;stop=1;ret=chip8_entry(&a.base);
 assert(ret==0x43384702 && frames==0 && little_word(image_base+ENGINE_RESULT+20)==0);
 assert(chip8_entry(0)==1);a.base.version=0;assert(chip8_entry(&a.base)==1);
 free(image_base);puts("PASS actual card adapter: alternating sources, compact payload/tail, brief key, ROM immutability, STOP before/after frames");return 0;
}

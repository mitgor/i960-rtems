/* Built into the trusted RTEMS kernel. The admitted image is guest ROM/data,
 * never native guest code. Reuses the existing owned callback ABI only. */
#include "../../../game/chip8/stream/player.h"
static struct c8_player chip8_player;
static unsigned chip8_entry(const struct doom_runtime_owned *owned){
 const struct doom_runtime_checkpoint*a=(const struct doom_runtime_checkpoint*)owned;
 volatile unsigned*r=(volatile unsigned*)(image_base+ENGINE_RESULT);
 unsigned n,seed,hz,i,ret;
 if(!owned||!image_base||owned->io.magic!=DOOM_API_MAGIC||
    owned->io.version!=DOOM_API_BATCH_VERSION||owned->io.bytes!=sizeof(owned->io)||
    owned->io.pointer_bytes!=sizeof(void*)||owned->io.little_endian!=1u||
    owned->magic!=DOOM_OWNED_MAGIC||owned->version!=DOOM_CHECKPOINT_VERSION||
    owned->bytes!=sizeof(*a)||owned->features!=DOOM_CHECKPOINT_FEATURES||
    !owned->owner||!owned->stopping||!owned->wait_ms||!owned->io.ticks_ms||!a->mark)return 1;
 n=little_word(image_base+4);seed=little_word(image_base+8);hz=little_word(image_base+12);
 if(little_word(image_base)!=0x314d5243u||n<2||n>3584||
    !c8_player_init(&chip8_player,image_base+16,n,seed,hz,owned->io.ticks_ms()))return 1;
 for(i=0;i<12;i++)r[i]=0;
 r[0]=0x31453843u;r[1]=1;r[2]=0;
 while(owned->owner()&&!owned->stopping()){
  /* One bounded drain per scheduling slice. No input work in the ISR. */
  for(i=0;i<16;i++){
   int event=a->mark(101,0,0,0);
   if(event<1)goto stop;
   if(event==1)break;
   if(!c8_player_key(&chip8_player,(unsigned)event-2u))return 2;
  }
  {unsigned slot=chip8_player.generation&1u;
   unsigned char*out=image_base+ENGINE_PLAY_OFFSET+slot*FRAME_BYTES;
   ret=c8_player_update(&chip8_player,owned->io.ticks_ms(),out);
   if(ret>1)goto stop;
   if(ret==1){
    int published=a->mark(100,(unsigned)out,FRAME_BYTES,chip8_player.generation);
    r[5]=chip8_player.generation;
    if(published<1)goto stop;
   }
  }
  if(owned->wait_ms(1)<0)break;
 }
stop:
 r[9]=2;r[10]=1;r[11]=210;
 return 0x43384702u;
}

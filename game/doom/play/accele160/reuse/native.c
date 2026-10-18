/* Host32 investigation only: reload actual Doom/Newlib while its outer arena
 * and seven pinned card-style allocations survive. No PCI or DMA access. */
#include <assert.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "../../../runtime/platform/platform.h"
#include "../../../runtime/startup/checkpoint_api.h"
#include "../../../runtime/heap.h"

static unsigned char memory[0x7e0000] __attribute__((aligned(16)));
static unsigned char reference[32][64768];
static struct arena arena;
static struct doom_heap heap;
static unsigned char *wad,*zone;
static unsigned wad_bytes,zone_loaned,locked,running,stop,frames,reads,total_reads;
static unsigned epoch,ticks,events;
static int quit_mode;
static int enter(void*p){if(locked)return 0;locked=1;return 1;}
static void leave(void*p){locked=0;}
static int progress(void*p){return 1;}
static unsigned owner(void){return running&&!locked;}
static unsigned stopping(void){return stop;}
static unsigned clock_ms(void){return ticks;}
static int wait_ms(unsigned n){ticks+=n;return stop?-1:0;}
static void *allocate(unsigned n){
 assert(owner()&&!stop);
 if(n==6291456u&&!zone_loaned){zone_loaned=1;return zone;}
 return doom_heap_malloc(&heap,n);
}
static void release(void*p){
 assert(owner());
 if(p==zone){assert(zone_loaned);zone_loaned=0;return;}
 assert(doom_heap_free(&heap,p));
}
static int read_wad(unsigned file,unsigned off,void *dst,unsigned n){
 unsigned loan;
 assert(owner()&&file==1&&n&&n<=4096&&off<=wad_bytes&&n<=wad_bytes-off);
 loan=doom_heap_borrow(&heap,dst,n);assert(loan);
 memcpy(dst,wad+off,n);
 assert(doom_heap_return(&heap,dst,loan));
 reads++;total_reads++;ticks++;
 return n;
}
static int mark(unsigned stage,unsigned x,unsigned y,unsigned z){
 if(stage==100){
  assert(y==65536&&z==frames+1);frames=z;ticks+=10;
  if(z<=32){
   if(epoch==1)memcpy(reference[z-1],(void*)(uintptr_t)x,64768);
   else assert(!memcmp(reference[z-1],(void*)(uintptr_t)x,64768));
  }
  if((!quit_mode&&z==64)||z==128){stop=1;return -1;}
 }
 if(stage==101&&quit_mode){
  /* Doom's normal F10 quit prompt, then Y. Keep each release queued until
   * the next input poll, just like the production event transport. */
  if(frames>=40&&events<2)return 2+196+((events++==0)?256:0);
  if(frames>=42&&events<4)return 2+121+((events++==2)?256:0);
 }
 return 1;
}

int main(int argc,char**argv){
 struct doom_runtime_checkpoint api;
 struct doom_heap_hooks hooks={enter,leave,progress,0};
 struct arena_slot pinned[7];
 unsigned sizes[7]={900000,6291456,65536,4096,65536,17*8192,17*8192};
 unsigned handles[7],i,j;void *addresses[7],*first_entry=0;
 FILE *file;long length;
 assert(argc==3);file=fopen(argv[2],"rb");assert(file);
 assert(!fseek(file,0,SEEK_END));length=ftell(file);assert(length>512);
 wad_bytes=(unsigned)length;wad=malloc(wad_bytes);assert(wad);
 rewind(file);assert(fread(wad,1,wad_bytes,file)==wad_bytes);fclose(file);
 assert(arena_init(&arena,memory,sizeof memory));
 assert(doom_heap_init(&heap,&arena,&hooks));
 for(i=0;i<7;i++){
  handles[i]=arena_alloc(&arena,sizes[i]);assert(handles[i]);
  addresses[i]=arena_pin(&arena,handles[i]);assert(addresses[i]);
  pinned[i]=arena.slot[i];memset(addresses[i],0xa5,sizes[i]);
 }
 zone=addresses[1];
 memset(&api,0,sizeof api);
 api.base.io.magic=DOOM_API_MAGIC;api.base.io.version=DOOM_API_BATCH_VERSION;
 api.base.io.bytes=sizeof api.base.io;api.base.io.features=DOOM_API_BATCH_FEATURES;
 api.base.io.pointer_bytes=4;api.base.io.little_endian=1;
 api.base.io.arena_bytes=sizeof memory;api.base.io.max_read=4096;
 api.base.io.file_id=1;api.base.io.file_bytes=wad_bytes;
 api.base.io.allocate=allocate;api.base.io.release=release;
 api.base.io.ticks_ms=clock_ms;api.base.io.read=read_wad;
 api.base.magic=DOOM_OWNED_MAGIC;api.base.version=DOOM_CHECKPOINT_VERSION;
 api.base.bytes=sizeof api;api.base.features=DOOM_CHECKPOINT_FEATURES;
 api.base.owner=owner;api.base.stopping=stopping;api.base.wait_ms=wait_ms;api.mark=mark;
 for(epoch=1;epoch<=3;epoch++){
  void *image=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);unsigned value;
  unsigned (*entry)(const struct doom_runtime_owned*);
  const struct doom_platform_stats *(*stats)(void);
  volatile unsigned *result;
  if(!image){fprintf(stderr,"dlopen: %s\n",dlerror());return 1;}
  entry=dlsym(image,"doom_engine_entry");stats=dlsym(image,"doom_platform_stats");
  result=dlsym(image,"doom_engine_result");assert(entry&&stats&&result);
  if(first_entry)assert((void*)entry==first_entry);else first_entry=(void*)entry;
  assert(!stats()->frames&&!stats()->blocks&&!result[0]);
  stop=frames=reads=events=0;quit_mode=(epoch==2);running=1;
  value=entry(&api.base);
  assert(value==0x454e4702&&result[9]==2&&result[10]==1&&result[11]==210);
  assert(quit_mode?(!stop&&frames>=42&&frames<128):(stop&&frames==64));
  assert(!zone_loaned&&!heap.blocks&&!heap.busy&&arena_valid(&arena));
  for(i=0;i<7;i++)assert(!memcmp(&pinned[i],&arena.slot[i],sizeof pinned[i]));
  for(i=7;i<ARENA_SLOTS;i++)assert(!arena.slot[i].span);
  /* Existing retired globals must refuse direct re-entry, without allocating. */
  stop=0;assert(entry(&api.base)==1);assert(!heap.blocks&&!zone_loaned);
  running=0;
  printf("epoch=%u stop=%s frames=%u reads=%u total_reads=%u same_entry=1 empty_dynamic_heap=1 fixed_pins_unchanged=1 retired_reentry_rejected=1\n",
         epoch,quit_mode?"menu-quit":"owner-stop",frames,reads,total_reads);
  assert(!dlclose(image));
 }
 for(i=0;i<7;i++){
  assert(arena_unpin(&arena,handles[i]));assert(arena_release(&arena,handles[i]));
 }
 assert(arena_valid(&arena));
 for(j=0;j<ARENA_SLOTS;j++)assert(!arena.slot[j].span);
 free(wad);puts("PASS three fresh-image epochs in one process and one retained arena");return 0;
}

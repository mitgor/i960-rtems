#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "../heap.h"
#include "../libc.h"
#include "api.h"
#define UPLOAD_NATIVE 1
#define I960_DOOM_RUNTIME 1
static unsigned ticks,stopping,mode,locked;
static unsigned char memory[8*1048576] __attribute__((aligned(16))),file[2048];
static struct arena arena;
static struct doom_heap heap;
static int enter(void*x){(void)x;assert(!locked);locked=1;return 1;}
static void leave(void*x){(void)x;assert(locked);locked=0;}
static int progress(void*x){(void)x;return !stopping;}
struct doom_heap *doom_arena_context(void){return &heap;}
static unsigned upload_time(void){return ticks;}
static unsigned upload_stopping(void){return stopping;}
static void exclusive_abort(void){assert(0);}
static void fatal(unsigned v){(void)v;assert(0);}
static void doom_shared_yield(void);
#include "../../../../rtems/residentnet/doom_runtime.c"
#include "probe.c"
static void doom_shared_yield(void){unsigned packet[136]={0},i,n;unsigned char*p=(unsigned char*)(packet+8);ticks++;
 if(mode==4)return;if(mode==5){stopping=1;return;}
 assert(wad.state==WAD_REQUEST&&leases==1&&!locked);
 /* The actual destination remains pinned while waiting for the host. */
 for(i=0;i<ARENA_SLOTS;i++)if(heap.slots[i].loan){assert(!doom_heap_free(&heap,heap.slots[i].pointer));assert(!doom_heap_realloc(&heap,heap.slots[i].pointer,2048));}
 n=wad.wanted;if(n>sizeof(file)-wad.offset)n=sizeof(file)-wad.offset;
 if(mode==2)n--;if(mode==3)n=0;
 memcpy(p,file+wad.offset,n);packet[0]=WAD_MAGIC;packet[1]=wad.sequence;packet[2]=1;packet[3]=wad.offset;packet[4]=n;packet[5]=mode==3;packet[6]=~0u;
 for(i=0;i<n;i++){unsigned j;packet[6]^=p[i];for(j=0;j<8;j++)packet[6]=(packet[6]>>1)^(0xedb88320u&(0u-(packet[6]&1)));}packet[6]=~packet[6];if(mode==1)packet[6]^=1;
 assert(!doom_runtime_control(0x77,0,32+((n+3)&~3u),1));
 for(i=0;i<8+(n+3)/4;i++)assert(!doom_runtime_control(0x78,i,packet[i],1));
 assert(!doom_runtime_control(0x79,0,0,1));
 assert(doom_runtime_control(0x77,0,32,1)==0xfffffffeu);
}
int main(void){unsigned binding[11]={WAD_MAGIC,1,sizeof(file)},i,h=2166136261u;struct doom_heap_hooks hooks={enter,leave,progress,0};
 assert(arena_init(&arena,memory,sizeof(memory)));assert(doom_heap_init(&heap,&arena,&hooks));assert(doom_libc_bind(&heap,fatal));
 for(i=0;i<sizeof(file);i++)file[i]=(unsigned char)i;memcpy(file,"IWAD",4);file[4]=32;file[5]=file[6]=file[7]=0;file[8]=0;file[9]=4;file[10]=file[11]=0;
 assert(!doom_runtime_api());assert(!doom_runtime_bind(binding,11));assert(doom_runtime_bind(binding,11));
 for(i=0;i<12;i++)h=(h^file[i])*16777619u;for(i=1024;i<1536;i++)h=(h^file[i])*16777619u;for(i=sizeof(file)-37;i<sizeof(file);i++)h=(h^file[i])*16777619u;
 {struct doom_runtime_v1 bad=*doom_runtime_api();bad.version++;assert(doom_runtime_probe(&bad)==1);bad=*doom_runtime_api();bad.bytes--;assert(doom_runtime_probe(&bad)==1);}
 for(mode=0;mode<6;mode++){assert(doom_runtime_probe(doom_runtime_api())==(mode?3:h));assert(!heap.blocks&&!leases&&doom_runtime_finish());}
 stopping=0;mode=0;assert(doom_runtime_probe(doom_runtime_api())==h);
 assert(wad.accepted==6&&wad.rejected==2&&wad.cancelled==2&&wad.sequence==11);
 assert(doom_heap_stop(&heap)&&doom_heap_drain(&heap));puts("PASS runtime API: real allocator, uploaded probe logic, WAD success/CRC/short/host error/timeout/STOP, pinned lifetime, recovery");
}

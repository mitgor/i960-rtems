#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "../heap.h"
#include "../libc.h"
#include "../cache/cache.h"
#define UPLOAD_NATIVE 1
#define I960_DOOM_RUNTIME 1
#define I960_DOOM_OWNED 1
#define I960_WAD_BATCH 1
#define I960_WAD_POLL 1
static unsigned ticks,stopping,mode,locked,identity=2,target_fragment;
static unsigned char memory[8*1048576] __attribute__((aligned(16))),file[20037];
static struct arena arena;static struct doom_heap heap;
static int enter(void*x){(void)x;assert(!locked);locked=1;return identity==2;}
static void leave(void*x){(void)x;assert(locked);locked=0;}
static int progress(void*x){(void)x;return !stopping;}
struct doom_heap *doom_arena_context(void){return &heap;}
static unsigned upload_time(void){return ticks;}
static unsigned upload_stopping(void){return stopping;}
static void exclusive_abort(void){assert(0);}
static void fatal(unsigned v){(void)v;assert(0);}
unsigned doom_shared_application_owner(void){return identity==2&&!locked;}
void doom_shared_yield(void){ticks++;}
void doom_shared_service(void);
#include "../../../../rtems/residentnet/doom_runtime.c"
static unsigned crc(const unsigned char*p,unsigned n){unsigned c=~0u,i;while(n--){c^=*p++;for(i=0;i<8;i++)c=(c>>1)^(0xedb88320u&(0u-(c&1)));}return ~c;}
void doom_shared_service(void){unsigned p[136]={0},i,n,off,mutate;ticks++;
 assert(batch.state==WAD_REQUEST&&leases==1&&!locked);
 for(i=0;i<ARENA_SLOTS;i++)if(heap.slots[i].loan){assert(!doom_heap_free(&heap,heap.slots[i].pointer));assert(!doom_heap_realloc(&heap,heap.slots[i].pointer,8192));}
 if(mode==4)return;
 if(mode==5&&batch.fragments==target_fragment){assert(!doom_runtime_owned_control(0x7a,0,owned_generation,1));return;}
 off=batch.offset+512*batch.fragments;n=batch.wanted-512*batch.fragments;if(n>512)n=512;if(n>sizeof(file)-off)n=sizeof(file)-off;
 mutate=batch.fragments==target_fragment;
 if(mutate&&mode==2)n--;if(mutate&&mode==3)n=0;
 memcpy(p+8,file+off,n);p[0]=DOOM_BATCH_MAGIC;p[1]=batch.sequence;p[2]=1;p[3]=off;p[4]=n;p[5]=mutate&&mode==3;p[6]=p[5]?0:crc((unsigned char*)(p+8),n);p[7]=batch.wanted;
 if(mutate&&mode==1)p[6]^=1;
 assert(!doom_runtime_control(0x77,0,32+((n+3)&~3u),1));
 for(i=0;i<8+(n+3)/4;i++)assert(!doom_runtime_control(0x78,i,p[i],1));
 assert(!doom_runtime_control(0x79,0,0,1));
}
int main(void){unsigned i,j,binding[11]={WAD_MAGIC,1,sizeof(file)};unsigned char*p;const struct doom_runtime_v1*a;struct doom_heap_hooks hooks={enter,leave,progress,0};
 assert(arena_init(&arena,memory,sizeof memory)&&doom_heap_init(&heap,&arena,&hooks)&&doom_libc_bind(&heap,fatal));
 for(i=0;i<sizeof file;i++)file[i]=(unsigned char)(i*17);
 assert(!doom_runtime_bind(binding,11));a=doom_runtime_batch_api(4096);assert(a&&a->version==DOOM_API_BATCH_VERSION&&a->max_read==4096);
 assert(!a->allocate(4096)&&a->read(1,0,file,4096)==-1);
 for(target_fragment=0;target_fragment<8;target_fragment++)for(mode=0;mode<=5;mode++){
  assert(doom_runtime_owned_begin());p=a->allocate(4096);assert(p);memset(p,0xa5,4096);
  assert(a->read(1,0,p,4096)==(mode==0?4096:mode==3?-3:mode>=4?-4:-2));
  if(!mode)assert(!memcmp(p,file,4096));else for(j=0;j<4096;j++)assert(p[j]==0xa5);
  assert(!leases&&batch.state==WAD_IDLE);a->release(p);assert(doom_runtime_owned_end()&&doom_runtime_finish()&&!heap.blocks);
 }
 mode=0;assert(doom_runtime_owned_begin());p=a->allocate(4096);assert(p);
 assert(a->read(1,20000,p,4096)==37&&!memcmp(p,file+20000,37));
 assert(a->read(1,sizeof file,p,1)==0&&a->read(1,sizeof file+1,p,1)==-1&&a->read(1,0,p+1,4095)==-1&&a->read(1,0,p,4097)==-1);
 identity=1;assert(a->read(1,0,p,10)==-1);identity=2;
 /* Exhaust allocation slots while keeping the caller's destination alive.
  * Staging OOM must return the destination loan and leave bytes unchanged. */
 {void*hog[ARENA_SLOTS];unsigned count=0;while(count<ARENA_SLOTS&&(hog[count]=a->allocate(16)))count++;
  memset(p,0xa5,4096);assert(a->read(1,0,p,4096)==-1&&!leases&&batch.state==WAD_IDLE&&!batch.inbox);
  for(i=0;i<4096;i++)assert(p[i]==0xa5);while(count)a->release(hog[--count]);
  assert(a->read(1,0,p,4096)==4096&&!memcmp(p,file,4096));
 }
 a->release(p);
 {struct doom_cache c={0};unsigned char out[20037];unsigned before;
  assert(doom_cache_open(&c,a));before=batch.sequence;
  assert(doom_cache_read(&c,0,out,8192)==8192&&!memcmp(out,file,8192)&&batch.sequence-before==2);
  for(i=0;i<10000;i++){unsigned off=i*7919u%sizeof file,n=i*37u%7000,want=sizeof file-off;if(want>n)want=n;assert(doom_cache_read(&c,off,out,n)==(int)want&&!memcmp(out,file+off,want));}
  assert(doom_cache_close(&c));
 }
 assert(doom_runtime_owned_end()&&doom_runtime_finish()&&!heap.blocks);assert(doom_heap_stop(&heap)&&doom_heap_drain(&heap));
 puts("PASS batch runtime/cache: 48 full/first-to-last fragment fault/STOP cases, atomic destination, real allocation loans, deadline, owner, EOF, 10000 reads, two requests per 8192 bytes, drain");
}

#include "heap.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
static unsigned char memory[8*1048576] __attribute__((aligned(16)));
static struct arena arena;
static struct doom_heap heap;
static unsigned int locked,denied,cancel_at,progress_calls;
static void *source;
static int lock(void*x){(void)x;if(denied)return 0;assert(!locked);locked=1;return 1;}
static void unlock(void*x){(void)x;assert(locked);locked=0;}
static int progress(void*x){(void)x;assert(!locked);progress_calls++;
 if(cancel_at&&progress_calls==cancel_at){
  assert(doom_heap_stop(&heap));assert(!doom_heap_drain(&heap));
  if(source)assert(!doom_heap_free(&heap,source));return 0;}
 return 1;}
static struct doom_heap_hooks hooks={lock,unlock,progress,0};
static void fresh(void){memset(&heap,0,sizeof heap);locked=denied=cancel_at=progress_calls=0;source=0;assert(arena_init(&arena,memory,sizeof memory));assert(doom_heap_init(&heap,&arena,&hooks));assert(!doom_heap_init(&heap,&arena,&hooks));}
int main(void){unsigned int i,j,h;unsigned char*p,*q,*r;void*many[128];
 fresh();h=arena_alloc(&arena,655360);assert(h&&arena_pin(&arena,h));
 p=doom_heap_calloc(&heap,6,1048576);assert(p&&!( (unsigned long)p&15));
 for(i=0;i<6*1048576;i++)assert(p[i]==0);
 q=doom_heap_malloc(&heap,128000);r=doom_heap_malloc(&heap,262144);assert(q&&r);
 assert(!doom_heap_malloc(&heap,8*1048576)&&heap.error==DH_OOM);
 assert(!doom_heap_calloc(&heap,~0u,2));assert(!doom_heap_malloc(&heap,~0u));
 for(i=0;i<128000;i++)q[i]=(unsigned char)i;
 {unsigned char*t=doom_heap_realloc(&heap,q,196608);assert(t);q=t;}
 for(i=0;i<128000;i++)assert(q[i]==(unsigned char)i);
 assert(!doom_heap_realloc(&heap,q,8*1048576));for(i=0;i<128000;i++)assert(q[i]==(unsigned char)i);
 q=doom_heap_realloc(&heap,q,33);assert(q);for(i=0;i<33;i++)assert(q[i]==(unsigned char)i);
 assert(doom_heap_free(&heap,q)&&!doom_heap_free(&heap,q));
 q=(unsigned char*)doom_heap_strdup(&heap,"Doom on i960");assert(q&&!strcmp((char*)q,"Doom on i960"));
 assert(!doom_heap_free(&heap,q+1));assert(doom_heap_free(&heap,q));
 q=doom_heap_malloc(&heap,0);assert(q);assert(!doom_heap_realloc(&heap,q,0));
 assert(doom_heap_free(&heap,0));denied=1;assert(!doom_heap_malloc(&heap,16));denied=0;
 assert(doom_heap_stop(&heap));assert(!doom_heap_malloc(&heap,1));assert(doom_heap_drain(&heap));
 assert(!heap.live&&!heap.blocks&&arena_valid(&arena));assert(arena.slot[(h&255)-1].pins==1);
 assert(arena_unpin(&arena,h)&&arena_release(&arena,h));
 fresh();for(i=0;i<128;i++){many[i]=doom_heap_malloc(&heap,16);assert(many[i]);}
 assert(!doom_heap_malloc(&heap,1));for(i=0;i<128;i++)assert(doom_heap_free(&heap,many[i]));
 /* Fragmentation and arbitrary release order; gap search remains bounded. */
 for(j=0;j<50;j++){for(i=0;i<100;i++){many[i]=doom_heap_malloc(&heap,17+(i*7919)%4000);assert(many[i]);}
 for(i=0;i<100;i+=2)assert(doom_heap_free(&heap,many[i]));for(i=1;i<100;i+=2)assert(doom_heap_free(&heap,many[i]));}
 fresh();p=doom_heap_malloc(&heap,4096);assert(p);memset(p,0x35,4096);source=p;cancel_at=2;
 assert(!doom_heap_realloc(&heap,p,8192)&&heap.error==DH_STOP);for(i=0;i<4096;i++)assert(p[i]==0x35);
 assert(heap.blocks==1&&heap.busy==0);assert(doom_heap_drain(&heap));
 fresh();cancel_at=2;assert(!doom_heap_calloc(&heap,1,8192));assert(!heap.blocks&&!heap.busy&&doom_heap_drain(&heap));
 fresh();p=doom_heap_malloc(&heap,16);h=heap.slots[0].handle;assert(arena_pin(&arena,h)==p);
 assert(!doom_heap_free(&heap,p));assert(!doom_heap_realloc(&heap,p,32)&&heap.error==DH_BUSY);
 assert(heap.blocks==1);assert(doom_heap_stop(&heap)&&!doom_heap_drain(&heap));
 assert(arena_unpin(&arena,h)&&doom_heap_drain(&heap));
 fresh();p=doom_heap_malloc(&heap,1024);assert(p);
 assert(!doom_heap_borrow(&heap,p+1,1)&&!doom_heap_borrow(&heap,p,1025));
 h=doom_heap_borrow(&heap,p,512);assert(h&&!doom_heap_borrow(&heap,p,1));
 assert(!doom_heap_return(&heap,0,h)&&!heap.fault&&!doom_heap_return(&heap,p,0));
 denied=1;assert(!doom_heap_return(&heap,p,h)&&!doom_heap_borrow(&heap,p,1));denied=0;
 assert(!doom_heap_free(&heap,p)&&!doom_heap_realloc(&heap,p,2048));
 assert(!doom_heap_return(&heap,p,h+1)&&doom_heap_return(&heap,p,h));
 assert(!doom_heap_return(&heap,p,h));j=doom_heap_borrow(&heap,p,512);assert(j&&j!=h);
 assert(!doom_heap_return(&heap,p,h));assert(doom_heap_stop(&heap)&&!doom_heap_drain(&heap));
 assert(doom_heap_return(&heap,p,j)&&doom_heap_drain(&heap));
 fresh();p=doom_heap_malloc(&heap,16);heap.loan_sequence=~0u;assert(!doom_heap_borrow(&heap,p,1)&&doom_heap_free(&heap,p));
 fresh();p=doom_heap_malloc(&heap,16);p[16]^=1;
 assert(!doom_heap_free(&heap,p)&&heap.fault&&heap.blocks==1);assert(!doom_heap_drain(&heap));
 fresh();p=doom_heap_malloc(&heap,16);heap.slots[0].bytes++;
 assert(!doom_heap_free(&heap,p)&&heap.fault&&heap.blocks==1);
 puts("PASS: 8 MiB arena, 6 MiB calloc plus image/buffers, resize/OOM preservation, overflow, zero-size, 128 slots, 5000 fragmented allocations, STOP during bulk, pins, guard/metadata retention");
 return 0;}

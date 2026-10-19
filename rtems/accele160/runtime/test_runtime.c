#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "runtime.h"
static unsigned char memory[AR_BYTES+4096] __attribute__((aligned(16)));
static struct arena parent;
static struct ar_runtime r;
static int sync_ok(void *p,unsigned int n){return p!=0&&n!=0;}
int main(void){
 unsigned int h,h2,i;unsigned char *p;unsigned char code[16]={1,2,3,4};
 struct manifest m={1,2,0,{{0,16,16,SEG_RX,0},{16,0,32,SEG_RW,0}}};
 m.segment[0].crc32=seg_crc32(0,code,16);
 assert(arena_init(&parent,memory,sizeof(memory)));ar_init(&r,9);
 assert(ar_reserve(&r,&parent));assert(ar_heap_proof(&r)==255);assert(!ar_reserve(&r,&parent));
 assert(!ar_begin(&r,0,AR_ABI,(unsigned long)r.modules.base+16,&m));
 assert(!ar_begin(&r,AR_BOARD,AR_ABI,(unsigned long)r.modules.base+32,&m));
 h=ar_alloc(&r,97);assert(h);p=ar_pin(&r,h);assert(p&&!((unsigned long)p&15));
 memset(p,42,97);assert(ar_cancel(&r,h));assert(!ar_pin(&r,h)&&!ar_release(&r,h));
 assert(!ar_close(&r));assert(p[0]==42);assert(ar_unpin(&r,h)&&ar_release(&r,h));
 h2=ar_alloc(&r,97);assert(h2!=h&&!ar_pin(&r,h));assert(ar_release(&r,h2));
 for(i=0;i<2;i++){
  assert(ar_begin(&r,AR_BOARD,AR_ABI,(unsigned long)r.modules.base+16,&m));
  assert(!seg_write(&r.image,0,1,code,16));assert(seg_write(&r.image,0,0,code,16));
  while(seg_prepare(&r.image,sync_ok)==1){}
  assert(r.image.state==SEG_READY);assert(!memcmp(r.image.base,code,16));
  for(h=16;h<48;h++)assert(!r.image.base[h]);
  assert(seg_start(&r.image));r.busy=1;assert(!ar_close(&r));
  r.busy=0;assert(seg_complete(&r.image));assert(seg_cancel(&r.image));
 }
 assert(ar_close(&r)&&r.epoch==10&&arena_valid(&parent));
 assert(ar_reserve(&r,&parent));h=ar_alloc(&r,32);p=ar_pin(&r,h);p[32]^=1;
 assert(!ar_valid(&r)&&!ar_close(&r)&&r.reservation&&parent.slot[0].pins==1);
 puts("Accele runtime: bounded partitions, exact board/base, two segmented reloads, BSS zero, pinned cancellation retention, stale handles, busy close and poisoned guard retention passed");return 0;
}

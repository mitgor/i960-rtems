#include "image.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
static unsigned int syncs;
static int sync_ok(void *p,unsigned int n){assert(p&&n);syncs++;return 1;}
static int sync_fail(void *p,unsigned int n){(void)p;(void)n;return 0;}
static struct manifest manifest(void){struct manifest m={0};m.abi=1;m.count=2;m.entry=0;
 m.segment[0]=(struct segment){0,16,16,SEG_RX,0};m.segment[1]=(struct segment){32,16,3072,SEG_RW,0};return m;}
int main(void){struct arena a;struct seg_image s;struct manifest m,bad;unsigned char data[16],*p;unsigned int i,h,old,hs[128],seed=19;
 unsigned char *ram=aligned_alloc(16,12u*1024*1024);assert(ram);memset(data,0x47,16);
 assert(!arena_init(&a,(void*)(~0ul-15ul),64));
 assert(arena_init(&a,ram,12u*1024*1024));assert(!arena_alloc(&a,~0u));
 h=arena_alloc(&a,6u*1024*1024);assert(h);p=arena_pin(&a,h);assert(p);memset(p,0x93,6u*1024*1024);
 assert(arena_cancel(&a,h));assert(!arena_pin(&a,h)&&!arena_release(&a,h));
 for(i=0;i<6u*1024*1024;i++)assert(p[i]==0x93);
 assert(arena_unpin(&a,h)&&arena_release(&a,h));old=h;h=arena_alloc(&a,32);assert(h!=old&&!arena_pin(&a,old));assert(arena_release(&a,h));
 a.slot[0].generation=0xffffff;h=arena_alloc(&a,32);assert((h&255)!=1);assert(arena_release(&a,h));a.slot[0].generation=0;
 for(i=0;i<128;i++){hs[i]=arena_alloc(&a,32+i);assert(hs[i]);}assert(!arena_alloc(&a,1));
 for(i=0;i<128;i+=2)assert(arena_release(&a,hs[i]));
 for(i=0;i<128;i+=2){hs[i]=arena_alloc(&a,16);assert(hs[i]);}
 for(i=0;i<128;i++)assert(arena_release(&a,hs[i]));
 memset(hs,0,sizeof hs);
 for(i=0;i<10000;i++){unsigned int index;seed=seed*1664525u+1013904223u;index=seed%128;
  if(hs[index]){assert(arena_release(&a,hs[index]));hs[index]=0;}else{hs[index]=arena_alloc(&a,1+(seed>>8)%65536);assert(hs[index]);}assert(arena_valid(&a));}
 for(i=0;i<128;i++)if(hs[i])assert(arena_release(&a,hs[i]));
 m=manifest();m.segment[0].crc32=m.segment[1].crc32=seg_crc32(0,data,16);
 assert(seg_crc32(0,"123456789",9)==0xcbf43926u);
 assert(seg_crc32(seg_crc32(0,"1234",4),"56789",5)==0xcbf43926u);
 seg_init(&s);bad=m;bad.segment[1].offset=0;assert(!seg_begin(&s,&a,&bad));bad=m;bad.entry=32;assert(!seg_begin(&s,&a,&bad));
 bad=m;bad.segment[1].memory_bytes=~0u;assert(!seg_begin(&s,&a,&bad));bad=m;bad.segment[0].flags=3;assert(!seg_begin(&s,&a,&bad));
 bad=m;bad.segment[0].file_bytes=bad.segment[0].memory_bytes=1;assert(!seg_begin(&s,&a,&bad));
 assert(seg_begin(&s,&a,&m));assert(!seg_prepare(&s,sync_ok));assert(!seg_write(&s,0,1,data,16));
 assert(seg_write(&s,0,0,data,16)&&seg_write(&s,1,0,data,16));assert(!seg_write(&s,0,0,data,16));assert(!seg_write(&s,2,0,data,1));assert(!seg_write(&s,1,16,data,1025));
 while(s.state!=SEG_READY)assert(seg_prepare(&s,sync_ok));assert(syncs==1);
 for(i=48;i<3104;i++)assert(!s.base[i]);assert(seg_start(&s));h=s.handle;
 assert(seg_cancel(&s)&&s.state==SEG_CANCELLING&&!arena_release(&a,h));assert(!seg_start(&s));
 assert(seg_complete(&s)&&s.state==SEG_EMPTY&&!arena_pin(&a,h));
 assert(seg_begin(&s,&a,&m));assert(seg_write(&s,0,0,data,16)&&seg_write(&s,1,0,data,16));s.base[0]^=1;
 while(s.state!=SEG_QUARANTINED)seg_prepare(&s,sync_ok);assert(!seg_cancel(&s)&&!arena_release(&a,s.handle));
 /* Fresh independently admitted arena for each fault (never reset live RAM). */
 free(ram);ram=aligned_alloc(16,8192);assert(arena_init(&a,ram,8192));seg_init(&s);
 assert(seg_begin(&s,&a,&m));assert(seg_write(&s,0,0,data,16)&&seg_write(&s,1,0,data,16));
 while(s.state!=SEG_QUARANTINED)seg_prepare(&s,sync_fail);assert(!seg_cancel(&s));free(ram);
 ram=aligned_alloc(16,8192);assert(arena_init(&a,ram,8192));h=arena_alloc(&a,100);p=arena_pin(&a,h);p[100]^=1;
 assert(!arena_release(&a,h)&&a.poisoned&&!arena_alloc(&a,1));free(ram);
 puts("PASS: 6 MiB allocation, 128 slots, fragmentation, 10000 operations, stale handles, pins/cancel, segmented load/BSS/checksum/cache failure");return 0;
}

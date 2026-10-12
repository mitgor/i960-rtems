/* Bounded cooperative test only: metadata and arena live entirely in BIO output.
 * Does not grant large RAM, modify flash, or invoke resident RTEMS callbacks. */
#include "image.h"
#include "../runtime/buffer_io.h"
extern unsigned char segment_code[],segment_end[];
static int sync_code(void *p,unsigned int n){unsigned int scratch;(void)p;(void)n;
 __asm__ volatile("dcctl 2,0,%0":"=r"(scratch)::"memory");
 __asm__ volatile("icctl 2,0,%0":"=r"(scratch)::"memory");return 1;
}
#define CHECK(x) do {if(!(x)){rc=__LINE__;goto done;}}while(0)
unsigned int payload(unsigned int address){
 unsigned char *b=(unsigned char*)address,*out=b+BIO_OUTPUT,*mem;
 struct arena *a=(struct arena*)out;
 struct seg_image *s=(struct seg_image*)(out+sizeof(struct arena));
 struct manifest m;unsigned int i,n,rc=0,result=0,steps=0,h,span;
 unsigned int (*entry)(unsigned int);
 if(!bio_request_valid(b)||bio_word(b+16)!=BIO_OUTPUT_MAX)return 1;
 for(i=0;i<BIO_OUTPUT_MAX;i++)out[i]=0;
 mem=(unsigned char*)(((unsigned int)(s+1)+15u)&~15u);span=(out+BIO_OUTPUT_MAX-mem)&~15u;
 CHECK(arena_init(a,mem,span));seg_init(s);
 for(i=0;i<sizeof(m)/4;i++)((unsigned int*)&m)[i]=0;
 n=segment_end-segment_code;m.abi=SEG_ABI;m.count=2;m.entry=0;
 m.segment[0].file_bytes=m.segment[0].memory_bytes=n;m.segment[0].flags=SEG_RX;m.segment[0].crc32=seg_crc32(0,segment_code,n);
 m.segment[1].offset=(n+15)&~15u;m.segment[1].file_bytes=4;m.segment[1].memory_bytes=128;m.segment[1].flags=SEG_RW;
 m.segment[1].crc32=seg_crc32(0,"DATA",4);
 CHECK(seg_begin(s,a,&m));CHECK(!seg_prepare(s,sync_code));
 CHECK(seg_write(s,1,0,"DATA",4));CHECK(seg_write(s,0,0,segment_code,n));CHECK(!seg_write(s,0,0,segment_code,n));
 while(s->state!=SEG_READY){CHECK(++steps<16);CHECK(seg_prepare(s,sync_code));}
 for(i=4;i<128;i++)CHECK(!s->base[m.segment[1].offset+i]);
 entry=(unsigned int(*)(unsigned int))seg_start(s);CHECK(entry);
 result=entry((unsigned int)(s->base+m.segment[1].offset));CHECK(result==(0x41544144u^0xa5a5a5a5u));
 h=s->handle;CHECK(seg_cancel(s));CHECK(!arena_release(a,h));CHECK(seg_complete(s));CHECK(!arena_pin(a,h));
 CHECK(arena_valid(a));
done:
 /* Return only deterministic summary; erase pointers/test state in output. */
 for(i=0;i<BIO_OUTPUT_MAX;i++)out[i]=0;
 bio_put(out,0x31474553u);bio_put(out+4,rc);bio_put(out+8,result);bio_put(out+12,steps);bio_put(out+16,span);
 bio_put(b+20,0);bio_put(b+24,BIO_OUTPUT_MAX);bio_put(b+28,bio_word(b+8));return rc;
}

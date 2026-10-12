#include <string.h>
#include "../platform/platform.h"
#include "../heap.h"
#include "i_video.h"
extern unsigned doom_engine_entry(const struct doom_runtime_owned*);
extern volatile unsigned doom_engine_result[12];
unsigned char *DG_ScreenBuffer;struct color colors[256];
static unsigned char memory[8*1048576] __attribute__((aligned(16)));
static struct arena arena;static struct doom_heap heap;static unsigned locked,ticks,stop_after,stop,yields;
static int enter(void*p){(void)p;if(locked)return 0;locked=1;return 1;}static void leave(void*p){(void)p;locked=0;}static int progress(void*p){(void)p;return 1;}
static unsigned owner(void){return !locked;}static unsigned stopping(void){return stop;}
static int wait_ms(unsigned ms){if(ms>1000||!owner()||stop)return -1;ticks+=ms;yields++;if(stop_after&&yields==stop_after)stop=1;return stop?-1:0;}
static void*allocate(unsigned n){return owner()&&!stop?doom_heap_malloc(&heap,n):0;}
static void release(void*p){if(!owner()||!doom_heap_free(&heap,p))__builtin_trap();}
static unsigned clock_ms(void){return ticks;}
static int read_wad(unsigned f,unsigned off,void*dst,unsigned n){unsigned token,i;if(f!=1||off>4096||n>512||stop)return -1;token=doom_heap_borrow(&heap,dst,n);if(!token)return -1;for(i=0;i<n;i++)((unsigned char*)dst)[i]=(off+i<4)?"IWAD"[off+i]:0;if(!doom_heap_return(&heap,dst,token))__builtin_trap();return n;}
static void owned_sleep(void){extern void DG_SleepMs(unsigned);DG_SleepMs(1000);}
int main(int argc,char**argv){struct doom_runtime_owned a;struct doom_heap_hooks hooks={enter,leave,progress,0};unsigned value,reserve,image_handle;void*initial,*retained[2];(void)argv;stop_after=argc==2?16:0;
 memset(&a,0,sizeof(a));if(!arena_init(&arena,memory,sizeof memory)||!doom_heap_init(&heap,&arena,&hooks))return 1;
 a.io.magic=DOOM_API_MAGIC;a.io.version=DOOM_API_VERSION;a.io.bytes=sizeof(a.io);a.io.features=DOOM_API_FEATURES;a.io.pointer_bytes=4;a.io.little_endian=1;a.io.arena_bytes=sizeof memory;a.io.max_read=512;a.io.file_id=1;a.io.file_bytes=4096;a.io.allocate=allocate;a.io.release=release;a.io.read=read_wad;a.io.ticks_ms=clock_ms;
 a.magic=DOOM_OWNED_MAGIC;a.version=DOOM_OWNED_VERSION;a.bytes=sizeof(a);a.features=DOOM_OWNED_FEATURES;a.owner=owner;a.wait_ms=wait_ms;a.stopping=stopping;
 {struct doom_runtime_owned bad=a;bad.version^=1;if(doom_platform_bind_owned(&bad,"/iwad.wad"))return 2;}
 if(argc==3){stop_after=1;if(!doom_platform_bind_owned(&a,"/iwad.wad")||doom_platform_call(owned_sleep)!=210||!stop||!doom_platform_finish()||heap.blocks)return 6;return 0;}
 /* Reproduce the retained proof layout before reserving the full image. */
 reserve=arena_alloc(&arena,argc>3?327680:1048576);if(!reserve||!arena_pin(&arena,reserve))return 8;
 initial=allocate(6291456);retained[0]=allocate(65536);retained[1]=allocate(98304);if(!initial||!retained[0]||!retained[1])return 9;
 release(initial);if(!arena_unpin(&arena,reserve)||!arena_release(&arena,reserve))return 10;
 image_handle=arena_alloc(&arena,807148);if(!image_handle||!arena_pin(&arena,image_handle))return 11;
 value=doom_engine_entry(&a);
 if(argc>3){if(value!=0x454e4702u||doom_engine_result[2]||doom_engine_result[9]!=3||heap.blocks!=2)return 12;}
 else if(value!=(stop_after?0x454e4702u:0x454e4700u)||doom_engine_result[2]!=6291456||doom_engine_result[5]!=1||doom_engine_result[6]!=(!stop_after)||doom_engine_result[9]!=(stop_after?2:0)||doom_engine_result[10]!=1||heap.blocks!=2)return 3;
 release(retained[0]);release(retained[1]);if(!arena_unpin(&arena,image_handle)||!arena_release(&arena,image_handle))return 13;
 if(doom_platform_call((void(*)(void))1)!=-1||doom_platform_finish())return 4;
 if(!doom_heap_stop(&heap)||!doom_heap_drain(&heap)||!arena_valid(&arena))return 5;
 {extern long syscall(long,...);if(syscall(4,1,doom_engine_result,48)!=48)return 7;}return 0;
}

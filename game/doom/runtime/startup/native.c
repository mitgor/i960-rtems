/* Host-only oracle: actual engine + private Newlib, real 8 MiB guarded arena. */
#include <string.h>
#include "../platform/platform.h"
#include "../heap.h"
extern unsigned doom_engine_entry(const struct doom_runtime_owned*);
extern volatile unsigned doom_engine_result[12];
extern long syscall(long,...);
static unsigned char memory[8*1048576] __attribute__((aligned(16))),wad[32*1048576],frame[64000],rgb[768],logbuf[4096];
static struct arena arena;static struct doom_heap heap;
static unsigned locked,ticks,reads,wire_bytes,stop,mode,wad_bytes;
static int trace_fd;
#ifdef DOOM_CHECKPOINTS
#include "checkpoint_log.h"
static struct doom_checkpoint_log *checkpoints;
static unsigned owner(void);
static int mark(unsigned stage,unsigned x,unsigned y,unsigned z){return owner()&&doom_checkpoint_put(checkpoints,1,reads,stage,x,y,z);}
#endif
static int enter(void*p){if(locked)return 0;locked=1;return 1;}
static void leave(void*p){locked=0;}
static int progress(void*p){return 1;}
static unsigned owner(void){return !locked;}
static unsigned stopping(void){return stop;}
static int wait_ms(unsigned n){if(n>1000||!owner()||stop)return -1;ticks+=n;return 0;}
static void*allocate(unsigned n){return owner()&&!stop?doom_heap_malloc(&heap,n):0;}
static void release(void*p){if(!owner()||!doom_heap_free(&heap,p))__builtin_trap();}
static unsigned clock_ms(void){return ticks;}
static int read_wad(unsigned f,unsigned off,void*dst,unsigned n){unsigned token,i;
 if(f!=1||off>wad_bytes||n>4096||stop)return -1;
 token=doom_heap_borrow(&heap,dst,n);if(!token)return -1;
 {unsigned pair[2]={off,n};if(syscall(4,trace_fd,pair,8)!=8)__builtin_trap();}
 reads++;if(n>wad_bytes-off)n=wad_bytes-off;
 if(mode==2&&reads==100)ticks=1800000;
 if(mode==1&&reads==100)stop=1;
 if(mode!=3||reads!=100)for(i=0;i<n;i++)((unsigned char*)dst)[i]=wad[off+i];
 if(!doom_heap_return(&heap,dst,token))__builtin_trap();wire_bytes+=n;
 return mode==3&&reads==100?-2:(int)n;
}
int main(int argc,char**argv){struct doom_runtime_owned a;
#ifdef DOOM_CHECKPOINTS
 struct doom_runtime_checkpoint extended;
#endif
 struct doom_heap_hooks hooks={enter,leave,progress,0};unsigned value,handle,extra[8],n;void*initial,*retained[2];int fd,got;
#ifdef DOOM_CHECKPOINTS
 if(argc<5)return 1;
#endif
 if(argc<4)return 1;trace_fd=syscall(5,argv[3],577,0600);if(trace_fd<0)return 12;mode=argc>2?(unsigned)(argv[2][0]-'0'):0;fd=syscall(5,argv[1],0,0);if(fd<0)return 2;
 while((got=syscall(3,fd,wad+wad_bytes,sizeof(wad)-wad_bytes))>0)wad_bytes+=got;
 syscall(6,fd);if(got<0||wad_bytes<512)return 3;
 memset(&a,0,sizeof(a));if(!arena_init(&arena,memory,sizeof memory)||!doom_heap_init(&heap,&arena,&hooks))return 4;
 a.io.magic=DOOM_API_MAGIC;a.io.version=DOOM_API_BATCH_VERSION;a.io.bytes=sizeof(a.io);a.io.features=DOOM_API_BATCH_FEATURES;a.io.pointer_bytes=4;a.io.little_endian=1;a.io.arena_bytes=sizeof memory;a.io.max_read=4096;a.io.file_id=1;a.io.file_bytes=wad_bytes;a.io.allocate=allocate;a.io.release=release;a.io.read=read_wad;a.io.ticks_ms=clock_ms;
 a.magic=DOOM_OWNED_MAGIC;a.version=DOOM_OWNED_VERSION;a.bytes=sizeof(a);a.features=DOOM_OWNED_FEATURES;a.owner=owner;a.wait_ms=wait_ms;a.stopping=stopping;
 handle=arena_alloc(&arena,1048576);if(!handle||!arena_pin(&arena,handle))return 5;
 initial=allocate(6291456);retained[0]=allocate(65536);retained[1]=allocate(98304);if(!initial||!retained[0]||!retained[1])return 6;release(initial);
 if(!arena_unpin(&arena,handle)||!arena_release(&arena,handle))return 10;
#ifdef DOOM_CHECKPOINTS
 checkpoints=allocate((sizeof(*checkpoints)+15u)&~15u);if(!checkpoints)return 14;memset(checkpoints,0,sizeof(*checkpoints));
#endif
 handle=arena_alloc(&arena,900000);if(!handle||!arena_pin(&arena,handle))return 11;

#ifdef DOOM_CHECKPOINTS
 memset(&extended,0,sizeof extended);extended.base=a;extended.base.version=DOOM_CHECKPOINT_VERSION;extended.base.bytes=sizeof extended;extended.base.features=DOOM_CHECKPOINT_FEATURES;extended.mark=mark;
 value=doom_engine_entry(&extended.base);
 fd=syscall(5,argv[4],577,0600);if(fd<0||checkpoints->overflow||syscall(4,fd,checkpoints->rows,checkpoints->count*32)!=(long)checkpoints->count*32)return 13;syscall(6,fd);release(checkpoints);checkpoints=0;
#else
 value=doom_engine_entry(&a);
#endif
syscall(6,trace_fd);n=doom_platform_log(logbuf,sizeof logbuf);syscall(4,2,logbuf,n);
 extra[0]=value;extra[1]=reads;extra[2]=wire_bytes;extra[3]=heap.blocks;extra[4]=heap.peak;extra[5]=mode;extra[6]=wad_bytes;extra[7]=0;
 syscall(4,1,doom_engine_result,48);syscall(4,1,extra,sizeof extra);
 if(!mode&&doom_platform_frame(frame,sizeof frame,rgb,sizeof rgb)){syscall(4,1,frame,sizeof frame);syscall(4,1,rgb,sizeof rgb);}
 if(heap.blocks!=2||!doom_engine_result[10])return 7;
 release(retained[0]);release(retained[1]);if(!arena_unpin(&arena,handle)||!arena_release(&arena,handle))return 8;
 if(!doom_heap_stop(&heap)||!doom_heap_drain(&heap)||!arena_valid(&arena))return 9;
 return 0;
}

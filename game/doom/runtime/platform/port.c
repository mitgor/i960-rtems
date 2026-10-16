/* Application-private Newlib syscall/allocator/platform port. Single owner.
 * All symbols that overlap libc are renamed by build.py after compilation. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <setjmp.h>
#include <reent.h>
#include "platform.h"
#include "i_video.h"
#include "../cache/cache.h"
static const struct doom_runtime_v1 *io;
static const char *iwad;
static const struct doom_runtime_owned *owned;
static struct doom_platform_stats stats;
static struct {void *p;unsigned n,internal;} allocations[128];
static struct {unsigned id,offset;} files[4];
static unsigned next_file=3,open_files;
static struct doom_cache cache;
static unsigned char log_ring[DPL_LOG],keys[DPL_KEYS],pressed[DPL_KEYS];
#ifdef DOOM_VISIBLE
unsigned char doom_platform_frames[2][65536];
#else
static unsigned char frame[64000];
#endif
static unsigned log_start,log_count,key_read,key_count,armed,initialized,retired;
#ifndef DOOM_VISIBLE
static unsigned char palette[768];
#endif
static jmp_buf escape;
#include "../startup/checkpoint_api.h"
static unsigned startup,started,budget,virtual_ms;
extern unsigned char *DG_ScreenBuffer;
#ifdef DOOM_PLAY
static void fatal(int n) __attribute__((noreturn));
#include "presentation.h"
#endif
void doom_platform_safe(void);
void doom_platform_mark(unsigned,unsigned,unsigned,unsigned);
#undef errno
extern int errno;
static int fail(int e){errno=e;_impure_ptr->_errno=e;return -1;}
static void fatal(int n) __attribute__((noreturn));
static void fatal(int n){
#ifdef DOOM_CHECKPOINTS
 doom_platform_mark(60,n,0,0);
#endif
 stats.exited=1;stats.exit_code=(unsigned)n;if(armed&&(!owned||owned->owner()))longjmp(escape,1);for(;;){/* fatal outside an admitted call: never pretend to return */}}
int doom_platform_bind(const struct doom_runtime_v1*a,const char*path){
 if(io||!path||!*path||!a||a->magic!=DOOM_API_MAGIC||!((a->version==DOOM_API_VERSION&&a->features==DOOM_API_FEATURES&&a->max_read==512)||(a->version==DOOM_API_BATCH_VERSION&&a->features==DOOM_API_BATCH_FEATURES&&(a->max_read==4096||a->max_read==65536)))||a->bytes!=sizeof(*a)||a->pointer_bytes!=sizeof(void*)||a->little_endian!=1||a->file_id!=1||a->file_bytes<512||a->file_bytes>268435456u||a->reserved[0]||a->reserved[1]||!a->allocate||!a->release||!a->read||!a->ticks_ms)return 0;
 io=a;iwad=path;return 1;
}
int doom_platform_bind_owned(const struct doom_runtime_owned*a,const char*path){
 if(owned||!a||a->magic!=DOOM_OWNED_MAGIC||
#ifdef DOOM_CHECKPOINTS
 a->version!=DOOM_CHECKPOINT_VERSION||a->bytes!=sizeof(struct doom_runtime_checkpoint)||a->features!=DOOM_CHECKPOINT_FEATURES
#else
 a->version!=DOOM_OWNED_VERSION||a->bytes!=sizeof(*a)||a->features!=DOOM_OWNED_FEATURES
#endif
||a->reserved||!a->owner||!a->wait_ms||!a->stopping||!a->owner()||a->stopping())return 0;
 #ifdef DOOM_CHECKPOINTS
 {const struct doom_runtime_checkpoint*t=(const void*)a;if(!t->mark||t->reserved[0]||t->reserved[1]||t->reserved[2])return 0;}
#endif
 if(!doom_platform_bind(&a->io,path))return 0;owned=a;return 1;
}
int doom_platform_checkpoint(void){if(!io||retired|| (owned&&!owned->owner()))return -1;return owned&&owned->stopping()?1:0;}
void *malloc(size_t n){unsigned i;void*p;if(!io||retired||n>0xffffffffu)return 0;if(!n)n=1;
 for(i=0;i<128&&allocations[i].p;i++){}if(i==128){fail(ENOMEM);return 0;}
 p=io->allocate((unsigned)n);if(!p){fail(ENOMEM);return 0;}allocations[i].p=p;allocations[i].n=n;allocations[i].internal=0;
 stats.live_bytes+=n;stats.blocks++;if(stats.live_bytes>stats.peak_bytes)stats.peak_bytes=stats.live_bytes;if(stats.blocks>stats.peak_blocks)stats.peak_blocks=stats.blocks;return p;
}
void free(void*p){unsigned i;if(!p)return;for(i=0;i<128&&allocations[i].p!=p;i++){}if(i==128)fatal(201);
 io->release(p);stats.live_bytes-=allocations[i].n;stats.blocks--;allocations[i].p=0;allocations[i].n=0;
}
void *calloc(size_t n,size_t s){unsigned i,total;unsigned char*p;if(n>0xffffffffu||s>0xffffffffu||(s&&n>0xffffffffu/s)){fail(ENOMEM);return 0;}total=n*s;p=malloc(total);if(p)for(i=0;i<total;i++)p[i]=0;return p;}
void *realloc(void*p,size_t n){unsigned i,j,count;unsigned char*q;if(!p)return malloc(n);if(!n){free(p);return 0;}for(i=0;i<128&&allocations[i].p!=p;i++){}if(i==128){fail(EINVAL);return 0;}q=malloc(n);if(!q)return 0;count=allocations[i].n;if(count>n)count=n;for(j=0;j<count;j++)q[j]=((unsigned char*)p)[j];free(p);return q;}
static void internal(void*p){unsigned i;if(!p)return;for(i=0;i<128;i++)if(allocations[i].p==p){allocations[i].internal=1;return;}fatal(208);}
char *strdup(const char*s){size_t n;char*p;if(!s){fail(EINVAL);return 0;}n=strlen(s);if(n==(size_t)-1){fail(ENOMEM);return 0;}p=malloc(n+1);if(p)memcpy(p,s,n+1);return p;}
char *_strdup_r(struct _reent*r,const char*s){char*p=strdup(s);if(!p)r->_errno=errno;return p;}
void *_malloc_r(struct _reent*r,size_t n){void*p=malloc(n);if(!p)r->_errno=ENOMEM;else internal(p);return p;}
void *_calloc_r(struct _reent*r,size_t n,size_t s){void*p=calloc(n,s);if(!p)r->_errno=ENOMEM;else internal(p);return p;}
void *_realloc_r(struct _reent*r,void*p,size_t n){void*q=realloc(p,n);if(!q&&n)r->_errno=errno;else internal(q);return q;}
void _free_r(struct _reent*r,void*p){(void)r;free(p);}
static int file_slot(int fd){unsigned i;for(i=0;i<4;i++)if(files[i].id==(unsigned)fd)return i;return -1;}
int _open(const char*path,int flags,...){unsigned i;if(!io||!path)return fail(EINVAL);
 if((flags&O_ACCMODE)!=O_RDONLY||(flags&(O_CREAT|O_TRUNC|O_APPEND)))return fail(EROFS);
 if(strcmp(path,iwad))return fail(ENOENT);for(i=0;i<4&&files[i].id;i++){}if(i==4)return fail(EMFILE);
 if(next_file>=32767u)return fail(EMFILE);files[i].id=++next_file;files[i].offset=0;open_files++;return files[i].id;
}
int _close(int fd){int i;if(fd==1||fd==2)return 0;i=file_slot(fd);if(i<0)return fail(EBADF);if(open_files==1&&cache.api&&!doom_cache_close(&cache))return fail(EBUSY);files[i].id=files[i].offset=0;open_files--;return 0;}
int _read(int fd,void*dst,unsigned n){int i=file_slot(fd),got;if(i<0)return fail(EBADF);if(!dst&&n)return fail(EINVAL);if(n>0x7fffffffu)return fail(EINVAL);
 if(!n)return 0;if(!cache.api&&!doom_cache_open(&cache,io))return fail(ENOMEM);got=doom_cache_read(&cache,files[i].offset,dst,n);if(got<0)return fail(EIO);files[i].offset+=got;stats.stdio_reads++;return got;
}
long _lseek(int fd,long offset,int origin){int i=file_slot(fd);long base,pos;if(i<0)return fail(EBADF);base=origin==SEEK_SET?0:origin==SEEK_CUR?(long)files[i].offset:origin==SEEK_END?(long)io->file_bytes:-1;if(base<0||offset < -base||offset>(long)io->file_bytes-base)return fail(EINVAL);pos=base+offset;files[i].offset=pos;return pos;}
int _fstat(int fd,struct stat*s){unsigned i;if(!s)return fail(EINVAL);if(fd!=1&&fd!=2&&file_slot(fd)<0)return fail(EBADF);for(i=0;i<sizeof(*s);i++)((unsigned char*)s)[i]=0;s->st_mode=(fd==1||fd==2)?S_IFCHR:S_IFREG;s->st_size=(fd==1||fd==2)?0:io->file_bytes;return 0;}
int _isatty(int fd){if(fd==1||fd==2)return 1;return fail(ENOTTY);}
int isatty(int fd){return _isatty(fd);}
int _write(int fd,const void*src,unsigned n){const unsigned char*p=src;unsigned i,index;if(fd!=1&&fd!=2)return fail(file_slot(fd)>=0?EROFS:EBADF);if((!p&&n)||n>0x7fffffffu)return fail(EINVAL);
 for(i=0;i<n;i++){if(log_count==DPL_LOG){log_start=(log_start+1)%DPL_LOG;log_count--;stats.log_dropped++;}index=(log_start+log_count)%DPL_LOG;log_ring[index]=p[i];log_count++;}stats.log_bytes+=n;return n;
}
int _unlink(const char*p){(void)p;return fail(EROFS);}int _link(const char*a,const char*b){(void)a;(void)b;return fail(EROFS);}
int mkdir(const char*p,unsigned mode){(void)p;(void)mode;return fail(EROFS);}
int system(const char*p){(void)p;return fail(ENOSYS);}
void exit(int n){
#ifdef DOOM_PLAY
 if(!n)n=210; /* menu Quit follows the owned STOP/cleanup contract */
#endif
 fatal(n);}void _exit(int n){exit(n);}void abort(void){fatal(202);}
double fabs(double x){union{double d;unsigned long long u;}v;v.d=x;v.u&=0x7fffffffffffffffull;return v.d;}
void DG_Init(void){unsigned i;if(!io||initialized)fatal(207);
#ifdef DOOM_VISIBLE
for(i=0;i<sizeof doom_platform_frames;i++)((unsigned char*)doom_platform_frames)[i]=0;
#else
for(i=0;i<64000;i++)frame[i]=0;
#endif
#ifdef DOOM_PLAY
#ifdef DOOM_PRESENT_TEST
/* Fail before level loading if mode selection differs on the target. */
if(present_mode(1)!=1)fatal(206);
if(present_mode(17)!=0)fatal(206);
if(present_mode(29)!=2)fatal(206);
if(present_mode(41)!=1)fatal(206);
#endif
present_scratch=DG_ScreenBuffer;
if(present_mode(1)&2)DG_ScreenBuffer=doom_platform_frames[0];
#endif
initialized=1;}
void DG_SetWindowTitle(const char*title){if(title){_write(1,title,strlen(title));_write(1,"\n",1);}}
unsigned DG_GetTicksMs(void){if(!io)fatal(203);doom_platform_safe();return startup?virtual_ms:io->ticks_ms();}
void DG_SleepMs(unsigned n){unsigned start;if(startup){doom_platform_safe();virtual_ms+=n;return;}if(n>0x7fffffffu)fatal(204);start=DG_GetTicksMs();stats.sleeps++;
 if(owned){for(;;){unsigned elapsed=DG_GetTicksMs()-start,remaining;if(elapsed>=n)break;remaining=n-elapsed;if(remaining>1000)remaining=1000;if(owned->wait_ms(remaining)){if(owned->owner()&&owned->stopping())fatal(210);fatal(211);}}}
 else while(DG_GetTicksMs()-start<n){} /* Preemptible clock wait; owned yield/STOP extension remains an admission gate. */}
int DG_GetKey(int*p,unsigned char*k){
#ifdef DOOM_PLAY
 const struct doom_runtime_checkpoint*t=(const void*)owned;int event;
 doom_platform_safe();event=t->mark(101,0,0,0);if(event<0)fatal(210);
 if(event>1){unsigned v=(unsigned)event-2;if(!p||!k)fatal(205);*p=(v>>8)&1;*k=v&255;
#ifdef DOOM_INPUT_TRACE
 doom_input_event(1,*p,*k);
#endif
 return 1;}
#endif
if(!p||!k)fatal(205);if(!key_count)return 0;*p=pressed[key_read];*k=keys[key_read];key_read=(key_read+1)%DPL_KEYS;key_count--;return 1;}
extern unsigned char *DG_ScreenBuffer;
void DG_DrawFrame(void){unsigned i,h=2166136261u;
#ifdef DOOM_PLAY
unsigned mode=present_mode(stats.frames+1),begin=io->ticks_ms(),wait_begin;
#ifdef DOOM_CPU_PROFILE
 present_cpu_begin=present_sample();
#endif
#else
unsigned mode=1;
#endif
#ifdef DOOM_VISIBLE
unsigned char *frame,*palette;
#ifdef DOOM_PLAY
#ifdef DOOM_DOUBLE_BUFFER
frame=doom_platform_frames[stats.frames&1];
#else
frame=doom_platform_frames[0];
#endif
#else
if(stats.frames>=2)fatal(206);frame=doom_platform_frames[stats.frames];
#endif
palette=frame+64000;
#endif
doom_platform_mark(50,0,0,0);if(!DG_ScreenBuffer)fatal(206);if(mode&2){if(frame!=DG_ScreenBuffer)fatal(206);if(mode&1)for(i=0;i<64000;i++)h=(h^frame[i])*16777619u;}
else if(mode&1){for(i=0;i<64000;i++){frame[i]=DG_ScreenBuffer[i];h=(h^frame[i])*16777619u;}}
else {for(i=0;i<64000;i++)frame[i]=DG_ScreenBuffer[i];}
stats.frame_hash=(mode&1)?h:0;h=2166136261u;for(i=0;i<256;i++){palette[3*i]=colors[i].r;palette[3*i+1]=colors[i].g;palette[3*i+2]=colors[i].b;}if(mode&1)for(i=0;i<768;i++)h=(h^palette[i])*16777619u;stats.palette_hash=(mode&1)?h:0;stats.frames++;
#ifdef DOOM_PLAY
 if(stats.frames==1)started=io->ticks_ms(); /* loading does not consume play time */
#endif
 doom_platform_mark(51,stats.frame_hash,stats.palette_hash,stats.frames);
#ifdef DOOM_PLAY
 present_record(frame,stats.frames,mode,begin);wait_begin=io->ticks_ms();
 {const struct doom_runtime_checkpoint*t=(const void*)owned;if(t->mark(100,(unsigned long)frame,65536,stats.frames)<=0)fatal(210);}
 present_previous_wait=io->ticks_ms()-wait_begin;
 /* mark(100) waited for the preceding slot's exact ACK before publishing this
  * one. The opposite slot is now free; never rotate before successful return. */
 DG_ScreenBuffer=(present_mode(stats.frames+1)&2)?doom_platform_frames[stats.frames&1]:present_scratch;
 return;
#endif
if(startup
#ifdef DOOM_VISIBLE
 &&stats.frames==2
#endif
)fatal(213);}
int doom_platform_key(int p,unsigned char k){unsigned i;if(key_count==DPL_KEYS||p<0||p>1)return 0;i=(key_read+key_count)%DPL_KEYS;keys[i]=k;pressed[i]=p;key_count++;stats.key_events++;return 1;}
unsigned doom_platform_log(void*dst,unsigned n){unsigned i;unsigned char*p=dst;if(!p&&n)return 0;if(n>log_count)n=log_count;for(i=0;i<n;i++)p[i]=log_ring[(log_start+i)%DPL_LOG];log_start=(log_start+n)%DPL_LOG;log_count-=n;return n;}
const struct doom_platform_stats *doom_platform_stats(void){return &stats;}
int doom_platform_call(void(*fn)(void)){int n;if(!io||!fn||armed||retired||stats.exited||doom_platform_checkpoint())return -1;armed=1;n=setjmp(escape);if(!n)fn();armed=0;return stats.exited?(int)stats.exit_code:0;}
int doom_platform_finish(void){unsigned i;if(armed||retired)return 0;for(i=0;i<4;i++)if(files[i].id)return 0;if(cache.api)return 0;for(i=0;i<128;i++)if(allocations[i].p&&!allocations[i].internal)return 0;
 if(fflush(stdout)||fflush(stderr)||fclose(stdout)||fclose(stderr))return 0;
 for(i=0;i<128;i++)if(allocations[i].p)free(allocations[i].p);retired=1;return !stats.blocks;}

int doom_platform_frame(void*dst,unsigned n,void*rgb,unsigned rn){unsigned i;
#ifdef DOOM_VISIBLE
unsigned char *frame=doom_platform_frames[
#ifdef DOOM_PLAY
#ifdef DOOM_DOUBLE_BUFFER
(stats.frames-1)&1
#else
0
#endif
#else
stats.frames?stats.frames-1:0
#endif
],*palette=frame+64000;
#endif
if(!stats.frames||!dst||!rgb||n<64000||rn<768)return 0;for(i=0;i<64000;i++)((unsigned char*)dst)[i]=frame[i];for(i=0;i<768;i++)((unsigned char*)rgb)[i]=palette[i];return 1;}

/* One-shot startup scope. No callback jumps while a cache read owns loans. */
void doom_platform_startup(unsigned milliseconds){startup=1;started=io->ticks_ms();budget=milliseconds;virtual_ms=0;}
void doom_platform_safe(void){if(!startup)return;if(doom_platform_checkpoint())fatal(210);if(io->ticks_ms()-started>=budget)fatal(
#ifdef DOOM_PLAY
210
#else
212
#endif
);}
int doom_platform_retire(void){unsigned i;if(armed||retired||!owned||!owned->owner())return 0;
 /* Caller has closed the WAD backend, returned all runtime loans and abandoned
  * engine globals. The image is one-shot and cannot be entered again. */
 if(cache.active)return 0;
 if(cache.api&&!doom_cache_close(&cache))return 0;
 if(fflush(stdout)||fflush(stderr)||fclose(stdout)||fclose(stderr))return 0;
 for(i=0;i<4;i++){files[i].id=files[i].offset=0;}open_files=0;
 for(i=0;i<128;i++)if(allocations[i].p)free(allocations[i].p);
 retired=1;return !stats.blocks;
}

void doom_platform_mark(unsigned stage,unsigned x,unsigned y,unsigned z){
#ifdef DOOM_CHECKPOINTS
#ifdef DOOM_PLAY
 present_mark(stage);(void)x;(void)y;(void)z;return;
#endif
 const struct doom_runtime_checkpoint*t=(const void*)owned;int rc=0;
 if(t&&owned->owner())rc=t->mark(stage,x,y,z);
 if(rc<0&&armed)fatal(210);
 if(rc<=0){/* No recursive fatal callback. */stats.exited=1;stats.exit_code=214;if(armed&&owned&&owned->owner())longjmp(escape,1);for(;;){}}
#else
 (void)stage;(void)x;(void)y;(void)z;
#endif
}

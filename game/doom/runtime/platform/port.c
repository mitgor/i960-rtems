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
static unsigned char log_ring[DPL_LOG],frame[64000],keys[DPL_KEYS],pressed[DPL_KEYS];
static unsigned log_start,log_count,key_read,key_count,armed,initialized,retired;
static unsigned char palette[768];
static jmp_buf escape;
static unsigned startup,started,budget,virtual_ms;
void doom_platform_safe(void);
#undef errno
extern int errno;
static int fail(int e){errno=e;_impure_ptr->_errno=e;return -1;}
static void fatal(int n) __attribute__((noreturn));
static void fatal(int n){stats.exited=1;stats.exit_code=(unsigned)n;if(armed&&(!owned||owned->owner()))longjmp(escape,1);for(;;){/* fatal outside an admitted call: never pretend to return */}}
int doom_platform_bind(const struct doom_runtime_v1*a,const char*path){
 if(io||!path||!*path||!a||a->magic!=DOOM_API_MAGIC||!((a->version==DOOM_API_VERSION&&a->features==DOOM_API_FEATURES&&a->max_read==512)||(a->version==DOOM_API_BATCH_VERSION&&a->features==DOOM_API_BATCH_FEATURES&&a->max_read==4096))||a->bytes!=sizeof(*a)||a->pointer_bytes!=sizeof(void*)||a->little_endian!=1||a->file_id!=1||a->file_bytes<512||a->file_bytes>268435456u||a->reserved[0]||a->reserved[1]||!a->allocate||!a->release||!a->read||!a->ticks_ms)return 0;
 io=a;iwad=path;return 1;
}
int doom_platform_bind_owned(const struct doom_runtime_owned*a,const char*path){
 if(owned||!a||a->magic!=DOOM_OWNED_MAGIC||a->version!=DOOM_OWNED_VERSION||a->bytes!=sizeof(*a)||a->features!=DOOM_OWNED_FEATURES||a->reserved||!a->owner||!a->wait_ms||!a->stopping||!a->owner()||a->stopping())return 0;
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
void exit(int n){fatal(n);}void _exit(int n){fatal(n);}void abort(void){fatal(202);}
double fabs(double x){union{double d;unsigned long long u;}v;v.d=x;v.u&=0x7fffffffffffffffull;return v.d;}
void DG_Init(void){unsigned i;if(!io||initialized)fatal(207);for(i=0;i<64000;i++)frame[i]=0;initialized=1;}
void DG_SetWindowTitle(const char*title){if(title){_write(1,title,strlen(title));_write(1,"\n",1);}}
unsigned DG_GetTicksMs(void){if(!io)fatal(203);doom_platform_safe();return startup?virtual_ms:io->ticks_ms();}
void DG_SleepMs(unsigned n){unsigned start;if(startup){doom_platform_safe();virtual_ms+=n;return;}if(n>0x7fffffffu)fatal(204);start=DG_GetTicksMs();stats.sleeps++;
 if(owned){for(;;){unsigned elapsed=DG_GetTicksMs()-start,remaining;if(elapsed>=n)break;remaining=n-elapsed;if(remaining>1000)remaining=1000;if(owned->wait_ms(remaining)){if(owned->owner()&&owned->stopping())fatal(210);fatal(211);}}}
 else while(DG_GetTicksMs()-start<n){} /* Preemptible clock wait; owned yield/STOP extension remains an admission gate. */}
int DG_GetKey(int*p,unsigned char*k){if(!p||!k)fatal(205);if(!key_count)return 0;*p=pressed[key_read];*k=keys[key_read];key_read=(key_read+1)%DPL_KEYS;key_count--;return 1;}
extern unsigned char *DG_ScreenBuffer;
void DG_DrawFrame(void){unsigned i,h=2166136261u;if(!DG_ScreenBuffer)fatal(206);for(i=0;i<64000;i++){frame[i]=DG_ScreenBuffer[i];h=(h^frame[i])*16777619u;}stats.frame_hash=h;h=2166136261u;for(i=0;i<256;i++){palette[3*i]=colors[i].r;palette[3*i+1]=colors[i].g;palette[3*i+2]=colors[i].b;}for(i=0;i<768;i++)h=(h^palette[i])*16777619u;stats.palette_hash=h;stats.frames++;if(startup)fatal(213);}
int doom_platform_key(int p,unsigned char k){unsigned i;if(key_count==DPL_KEYS||p<0||p>1)return 0;i=(key_read+key_count)%DPL_KEYS;keys[i]=k;pressed[i]=p;key_count++;stats.key_events++;return 1;}
unsigned doom_platform_log(void*dst,unsigned n){unsigned i;unsigned char*p=dst;if(!p&&n)return 0;if(n>log_count)n=log_count;for(i=0;i<n;i++)p[i]=log_ring[(log_start+i)%DPL_LOG];log_start=(log_start+n)%DPL_LOG;log_count-=n;return n;}
const struct doom_platform_stats *doom_platform_stats(void){return &stats;}
int doom_platform_call(void(*fn)(void)){int n;if(!io||!fn||armed||retired||stats.exited||doom_platform_checkpoint())return -1;armed=1;n=setjmp(escape);if(!n)fn();armed=0;return stats.exited?(int)stats.exit_code:0;}
int doom_platform_finish(void){unsigned i;if(armed||retired)return 0;for(i=0;i<4;i++)if(files[i].id)return 0;if(cache.api)return 0;for(i=0;i<128;i++)if(allocations[i].p&&!allocations[i].internal)return 0;
 if(fflush(stdout)||fflush(stderr)||fclose(stdout)||fclose(stderr))return 0;
 for(i=0;i<128;i++)if(allocations[i].p)free(allocations[i].p);retired=1;return !stats.blocks;}

int doom_platform_frame(void*dst,unsigned n,void*rgb,unsigned rn){unsigned i;if(!stats.frames||!dst||!rgb||n<64000||rn<768)return 0;for(i=0;i<64000;i++)((unsigned char*)dst)[i]=frame[i];for(i=0;i<768;i++)((unsigned char*)rgb)[i]=palette[i];return 1;}

/* One-shot startup scope. No callback jumps while a cache read owns loans. */
void doom_platform_startup(unsigned milliseconds){startup=1;started=io->ticks_ms();budget=milliseconds;virtual_ms=0;}
void doom_platform_safe(void){if(!startup)return;if(doom_platform_checkpoint())fatal(210);if(io->ticks_ms()-started>=budget)fatal(212);}
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

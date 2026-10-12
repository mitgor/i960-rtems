/* Host-only measurement platform. Not an RTEMS implementation. */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <limits.h>
#include "doomgeneric.h"
#include "doomstat.h"
#include "z_zone.h"
#include "i_video.h"
extern void DG_ZoneSample(void);
void *__real_malloc(size_t);void *__real_calloc(size_t,size_t);void *__real_realloc(void*,size_t);void __real_free(void*);
#ifdef PROFILE_ARENA
#include "runtime/host.inc"
#endif
struct allocation {void*p;size_t n;};
static struct allocation records[16384];
static size_t live,peak,largest,allocations,frees,failed,stack_peak;
static uintptr_t stack_origin;
static unsigned frames,frame_limit=2100,clock_ms,hash=2166136261u,read_calls,max_read;
static unsigned long long read_bytes;
unsigned prof_zone_peak,prof_zone_static_peak,prof_zone_cache_peak,prof_zone_size,prof_zone_blocks,prof_zone_purges;
static void remember(void*p,size_t n){unsigned i;if(!p){failed++;return;}for(i=0;i<16384&&records[i].p;i++);if(i==16384){fprintf(stderr,"profile registry full\n");abort();}records[i].p=p;records[i].n=n;live+=n;allocations++;if(live>peak)peak=live;if(n>largest)largest=n;}
static void forget(void*p){unsigned i;if(!p)return;for(i=0;i<16384;i++)if(records[i].p==p){live-=records[i].n;records[i].p=0;frees++;return;}fprintf(stderr,"untracked engine free\n");abort();}
void *__wrap_malloc(size_t n){void*p=__real_malloc(n);remember(p,n);return p;}
void *__wrap_calloc(size_t n,size_t s){void*p=__real_calloc(n,s);remember(p,n*s);return p;}
void __wrap_free(void*p){forget(p);__real_free(p);}
void *__wrap_realloc(void*p,size_t n){void*q=__real_realloc(p,n);if(q||!n){forget(p);if(q)remember(q,n);}else failed++;return q;}
char *__wrap_strdup(const char*s){size_t n=strlen(s)+1;char*p=__wrap_malloc(n);if(p)memcpy(p,s,n);return p;}
void __cyg_profile_func_enter(void*f,void*caller){char local;uintptr_t here=(uintptr_t)&local;(void)f;(void)caller;if(stack_origin>here&&stack_origin-here>stack_peak)stack_peak=stack_origin-here;}
void __cyg_profile_func_exit(void*f,void*caller){(void)f;(void)caller;}
static void report(void){const char*path=getenv("DOOM_PROFILE");FILE*f=path?fopen(path,"w"):stderr;if(!f)return;
 fprintf(f,"{\"pointer_bytes\":%u,\"frames\":%u,\"gametic\":%d,\"frame_hash\":%u,\"engine_malloc_peak\":%lu,\"engine_malloc_live\":%lu,\"largest_allocation\":%lu,\"allocations\":%lu,\"frees\":%lu,\"failed_allocations\":%lu,\"zone_reserved\":%u,\"zone_used_peak_including_headers\":%u,\"zone_nonpurgeable_peak\":%u,\"zone_cache_peak\":%u,\"zone_blocks_peak\":%u,\"zone_purges\":%u,\"wad_read_calls\":%u,\"wad_read_bytes\":%llu,\"wad_max_request\":%u,\"instrumented_engine_stack_span\":%lu}\n",(unsigned)sizeof(void*),frames,gametic,hash,(unsigned long)peak,(unsigned long)live,(unsigned long)largest,(unsigned long)allocations,(unsigned long)frees,(unsigned long)failed,prof_zone_size,prof_zone_peak,prof_zone_static_peak,prof_zone_cache_peak,prof_zone_blocks,prof_zone_purges,read_calls,read_bytes,max_read,(unsigned long)stack_peak);if(path)fclose(f);}
void DG_WadRead(unsigned requested,unsigned actual){read_calls++;read_bytes+=actual;if(requested>max_read)max_read=requested;}
static FILE *trace, *raw, *palette;
static FILE *capture_open(const char *variable, const char *mode)
{
    const char *path = getenv(variable);
    FILE *f;
    if (!path) return NULL;
    f = fopen(path, mode);
    if (!f) { perror(path); exit(2); }
    return f;
}
static void capture_close(void)
{
    int failed = 0;
    if (trace && fclose(trace)) failed = 1;
    if (raw && fclose(raw)) failed = 1;
    if (palette && fclose(palette)) failed = 1;
    if (failed) { perror("capture close"); _Exit(2); }
}
void DG_Init(void)
{
    trace = capture_open("DOOM_TRACE", "w");
    raw = capture_open("DOOM_RAW", "wb");
    palette = capture_open("DOOM_PALETTE", "wb");
    atexit(capture_close);
}
void DG_DrawFrame(void)
{
    unsigned i, one = 2166136261u;
    unsigned char rgb[768];
    DG_ZoneSample();
    for (i = 0; i < 320*200; i++) {
        hash = (hash ^ DG_ScreenBuffer[i]) * 16777619u;
        one = (one ^ DG_ScreenBuffer[i]) * 16777619u;
    }
    if (trace && fprintf(trace, "%u %d %u\n", frames, gametic, one) < 0) {
        perror("frame trace"); exit(2);
    }
    if (raw && fwrite(DG_ScreenBuffer, 1, 320*200, raw) != 320*200) {
        perror("frame capture"); exit(2);
    }
    if (palette) {
        /* Serialize channels explicitly; never depend on bitfield byte order. */
        for (i = 0; i < 256; i++) {
            rgb[3*i] = colors[i].r;
            rgb[3*i+1] = colors[i].g;
            rgb[3*i+2] = colors[i].b;
        }
        if (fwrite(rgb, 1, sizeof(rgb), palette) != sizeof(rgb)) {
            perror("palette capture"); exit(2);
        }
    }
    if (++frames >= frame_limit) { Z_CheckHeap(); exit(0); }
}
void DG_SleepMs(uint32_t ms){clock_ms+=ms;}
uint32_t DG_GetTicksMs(void){return clock_ms;}
int DG_GetKey(int*pressed,unsigned char*key){(void)pressed;(void)key;return 0;}
void DG_SetWindowTitle(const char*title){(void)title;}
#ifdef DOOM_WAD_CACHE
#include "runtime/cache/host.inc"
#endif
int main(int argc,char**argv){char stack;const char*n=getenv("DOOM_FRAMES");stack_origin=(uintptr_t)&stack;if(n)frame_limit=strtoul(n,0,10);atexit(report);
#ifdef PROFILE_ARENA
runtime_init();
#endif
#ifdef DOOM_WAD_CACHE
cache_host_init(argc,argv);
#endif
doomgeneric_Create(argc,argv);for(;;){clock_ms+=29;doomgeneric_Tick();}return 0;}

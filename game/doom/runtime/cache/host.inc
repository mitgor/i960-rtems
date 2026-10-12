/* Host-only immutable WAD server. Its snapshot is outside the simulated card
 * arena, just as the Linux host owns the real card's 28 MiB file. */
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include "cache.h"
extern int doom_wad_backend_bind(const struct doom_runtime_v1*,const char*);
extern int doom_wad_backend_close(void);
extern const struct doom_cache*doom_wad_backend_stats(void);
static struct doom_runtime_v1 cache_api;
static unsigned char*cache_host_file;
static unsigned cache_host_bytes,cache_host_requests;
static FILE *cache_trace;
void DG_WadReadAt(unsigned offset,unsigned n,unsigned got){DG_WadRead(n,got);if(cache_trace&&fprintf(cache_trace,"%u %u %u\n",offset,n,got)<0)abort();}
static void*cache_allocate(unsigned n){return __real_malloc(n);}
static void cache_release(void*p){__real_free(p);}
static unsigned cache_ticks(void){return clock_ms;}
static int cache_read(unsigned id,unsigned off,void*dst,unsigned n){
 const struct doom_cache*c=doom_wad_backend_stats();
 if(id!=1||n>cache_api.max_read||off>cache_host_bytes||dst!=c->bounce)abort();
 cache_host_requests++;if(n>cache_host_bytes-off)n=cache_host_bytes-off;memcpy(dst,cache_host_file+off,n);return n;
}
static void cache_host_finish(void){const struct doom_cache*c=doom_wad_backend_stats();const char*name=getenv("DOOM_CACHE_PROFILE");FILE*f=name?fopen(name,"w"):0;
 if(f){fprintf(f,"{\"lines\":%u,\"cache_bytes\":%u,\"bounce_bytes\":%u,\"wire_requests\":%u,\"state_bytes\":%u,\"requests\":%u,\"hits\":%u,\"misses\":%u,\"wire_bytes\":%u,\"copied_bytes\":%u,\"errors\":%u,\"arena_peak\":%u,\"arena_peak_blocks\":%u,\"reserved_image\":%u}\n",DCACHE_LINES,DCACHE_LINES*512,cache_api.max_read,cache_host_requests,(unsigned)sizeof(*c),c->reads,c->hits,c->misses,c->wire_bytes,c->copied_bytes,c->errors,runtime_heap.peak,runtime_heap.peak_blocks,RUNTIME_IMAGE_BYTES);if(fclose(f))abort();}
 if(cache_trace&&fclose(cache_trace))abort();
 if(!doom_wad_backend_close()||munmap(cache_host_file,cache_host_bytes))abort();
}
static void cache_host_init(int argc,char**argv){int i,fd;struct stat st;unsigned done=0;const char*path=0;
 for(i=1;i+1<argc;i++)if(!strcmp(argv[i],"-iwad"))path=argv[i+1];if(!path)abort();
 fd=open(path,O_RDONLY);if(fd<0||fstat(fd,&st)||st.st_size<512||st.st_size>268435456)abort();cache_host_bytes=st.st_size;
 cache_host_file=mmap(0,cache_host_bytes,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);if(cache_host_file==MAP_FAILED)abort();
 while(done<cache_host_bytes){ssize_t n=read(fd,cache_host_file+done,cache_host_bytes-done);if(n<=0)abort();done+=n;}
 if(close(fd)||mprotect(cache_host_file,cache_host_bytes,PROT_READ))abort();
 cache_api.magic=DOOM_API_MAGIC;cache_api.version=DOOM_API_VERSION;cache_api.bytes=sizeof cache_api;cache_api.features=DOOM_API_FEATURES;cache_api.pointer_bytes=sizeof(void*);cache_api.little_endian=1;cache_api.arena_bytes=8u*1048576;cache_api.max_read=512;cache_api.file_id=1;cache_api.file_bytes=cache_host_bytes;cache_api.allocate=cache_allocate;cache_api.release=cache_release;cache_api.read=cache_read;cache_api.ticks_ms=cache_ticks;
 {const char*t=getenv("DOOM_WAD_BATCH_BYTES");if(t){if(strcmp(t,"4096"))abort();cache_api.version=DOOM_API_BATCH_VERSION;cache_api.features=DOOM_API_BATCH_FEATURES;cache_api.max_read=4096;}}
 {const char*t=getenv("DOOM_WAD_TRACE");if(t){cache_trace=fopen(t,"w");if(!cache_trace)abort();}}
 if(!doom_wad_backend_bind(&cache_api,path))abort();atexit(cache_host_finish);
}

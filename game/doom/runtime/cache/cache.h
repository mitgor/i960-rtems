#ifndef DOOM_WAD_CACHE_H
#define DOOM_WAD_CACHE_H
#include "../entry/api.h"
#ifndef DCACHE_LINES
#define DCACHE_LINES 128u
#endif
#define DCACHE_LINE 512u
struct doom_cache {
 const struct doom_runtime_v1 *api;
 unsigned char *data,*bounce;
 unsigned int tags[DCACHE_LINES],valid[DCACHE_LINES];
 unsigned int lines,active,reads,hits,misses,wire_bytes,copied_bytes,errors;
 int last_error;
};
/* Single owning application task; initially zero. Copies into caller-owned
 * destinations, but only the exact bounce allocation crosses the runtime ABI. */
int doom_cache_open(struct doom_cache *,const struct doom_runtime_v1 *);
int doom_cache_read(struct doom_cache *,unsigned int,void *,unsigned int);
int doom_cache_close(struct doom_cache *);
#endif

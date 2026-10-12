/* Single-IWAD DoomGeneric backend. Engine filesystem discovery/configuration
 * remain separate; this is not a general stdio replacement. */
#include "w_file.h"
#include "cache.h"
static struct doom_cache cache;
static wad_file_t file;
static const char*bound_path;
static const struct doom_runtime_v1*bound_api;
static unsigned opened,retired;
extern wad_file_class_t stdc_wad_file;
int doom_wad_backend_bind(const struct doom_runtime_v1*a,const char*path){
 if(bound_api||!a||!path||!*path)return 0;bound_api=a;bound_path=path;return 1;
}
static wad_file_t*open_file(char*path){unsigned i;
 if(!path||opened||retired||!bound_api)return 0;
 for(i=0;path[i]&&path[i]==bound_path[i];i++){}if(path[i]!=bound_path[i])return 0;
 if(!doom_cache_open(&cache,bound_api))return 0;
 file.file_class=&stdc_wad_file;file.mapped=0;file.length=bound_api->file_bytes;opened=1;return &file;
}
static void close_file(wad_file_t*f){if(f==&file&&opened&&doom_cache_close(&cache)){opened=0;retired=1;}}
static size_t read_file(wad_file_t*f,unsigned offset,void*buffer,size_t n){int got;
 if(f!=&file||!opened||n>0xffffffffu)return 0;got=doom_cache_read(&cache,offset,buffer,(unsigned)n);
#ifdef PROFILE_HOST
 {extern void DG_WadReadAt(unsigned,unsigned,unsigned);DG_WadReadAt(offset,n,got<0?0:got);}
#endif
 return got<0?0:(size_t)got;
}
/* Host diagnostics/controlled teardown; card owner must drain before close. */
const struct doom_cache*doom_wad_backend_stats(void){return &cache;}
int doom_wad_backend_close(void){if(!opened)return 1;if(!doom_cache_close(&cache))return 0;opened=0;retired=1;return 1;}
wad_file_class_t stdc_wad_file={open_file,close_file,read_file};

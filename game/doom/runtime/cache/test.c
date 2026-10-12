#include "cache.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
static struct doom_cache cache;
static unsigned char wad[20037];
static unsigned calls,mode,allocs,fail_alloc;
static void*allocation(unsigned n){if(++allocs==fail_alloc)return 0;return malloc(n);}
static int read_at(unsigned file,unsigned offset,void*p,unsigned n){
 assert(file==1&&p==cache.bounce&&n<=512&&offset+n<=sizeof wad);calls++;
 assert(!doom_cache_close(&cache));assert(doom_cache_read(&cache,0,p,1)==-1);
 if(mode==1)return -4;if(mode==2)return (int)n-1;
 memcpy(p,wad+offset,n);return n;
}
int main(void){struct doom_runtime_v1 api={0};unsigned i;unsigned char out[20037];int got;
 for(i=0;i<sizeof wad;i++)wad[i]=(unsigned char)(i*17);
 api.magic=DOOM_API_MAGIC;api.version=DOOM_API_VERSION;api.bytes=sizeof api;api.features=DOOM_API_FEATURES;api.pointer_bytes=sizeof(void*);api.little_endian=1;api.max_read=512;api.file_id=1;api.file_bytes=sizeof wad;api.allocate=allocation;api.release=free;api.read=read_at;
 fail_alloc=2;assert(!doom_cache_open(&cache,&api)&&!cache.data&&!cache.bounce&&!cache.active);fail_alloc=0;
 assert(doom_cache_open(&cache,&api)&&!doom_cache_open(&cache,&api));
 assert(doom_cache_read(&cache,503,out,1037)==1037&&!memcmp(out,wad+503,1037));i=calls;
 assert(doom_cache_read(&cache,503,out,1037)==1037&&calls==i);
 assert(doom_cache_read(&cache,20000,out,100)==37&&!memcmp(out,wad+20000,37));
 assert(doom_cache_read(&cache,sizeof wad,out,1)==0&&doom_cache_read(&cache,sizeof wad+1,out,1)<0);
 assert(doom_cache_read(&cache,0,0,1)<0&&doom_cache_read(&cache,0,0,0)==0);
 assert(doom_cache_close(&cache)&&doom_cache_open(&cache,&api));
 assert(doom_cache_read(&cache,0,out,512)==512);mode=1;memset(out,0xa5,sizeof out);
 got=doom_cache_read(&cache,0,out,1024);assert(got==512&&cache.last_error==-4&&out[512]==0xa5);
 mode=2;assert(doom_cache_read(&cache,512,out,512)==-2&&cache.last_error==-2);mode=0;
 assert(doom_cache_read(&cache,512,out,512)==512&&!memcmp(out,wad+512,512));
 /* Random offsets, crossing lines, conflicts, EOF and unsigned overflow. */
 for(i=0;i<10000;i++){unsigned o=(i*7919u)%sizeof wad,n=(i*37u)%2000,want=sizeof wad-o;if(want>n)want=n;assert(doom_cache_read(&cache,o,out,n)==(int)want&&!memcmp(out,wad+o,want));}
 assert(doom_cache_read(&cache,0,out,~0u)==sizeof wad&&!memcmp(out,wad,sizeof wad));
 assert(doom_cache_read(&cache,~0u,out,1)==-1);assert(doom_cache_close(&cache)&&!doom_cache_close(&cache));
 puts("PASS cache: exact bounce pointer, line/EOF bounds, hits/conflicts, partial/error/timeout, reentry/active-close refusal, allocation rollback, 10000 random reads");
}

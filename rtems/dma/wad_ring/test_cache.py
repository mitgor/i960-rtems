#!/usr/bin/env python3
import subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[3]
code=r'''
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include "game/doom/runtime/cache/cache.h"
/* Include the implementation to exercise the exact helper at allocation edges. */
#include "game/doom/runtime/cache/cache.c"
static void copy_edges(void){unsigned a,b,n,i;unsigned char *s,*d;
 for(a=0;a<4;a++)for(b=0;b<4;b++)for(n=0;n<1025;n++){
  s=malloc(n+a);d=malloc(n+b);assert(s&&d);
  for(i=0;i<n+a;i++)s[i]=(i*29)^17;memset(d,0xa5,n+b);
  cache_copy(d+b,s+a,n);assert(!memcmp(d+b,s+a,n));
  for(i=0;i<b;i++)assert(d[i]==0xa5);free(s);free(d);
 }
}
static unsigned now;static unsigned ticks(void){now+=10;return now;}
static unsigned char wad[197123];static unsigned calls,maximum;
static void*alloc(unsigned n){return malloc(n);}static void release(void*p){free(p);}
static int read_wad(unsigned f,unsigned o,void*p,unsigned n){assert(f==1&&n<=maximum&&o+n<=sizeof wad);if(maximum==65536)assert(!(o&65535)&&n==((sizeof wad-o<65536)?sizeof wad-o:65536));memcpy(p,wad+o,n);calls++;return n;}
int main(void){struct doom_runtime_v1 a={0};struct doom_cache c={0};unsigned char output[70000];unsigned i,j,n,o,seed=7;
 copy_edges();
 for(i=0;i<sizeof wad;i++)wad[i]=(i*17)^(i>>9);
 a.magic=DOOM_API_MAGIC;a.version=DOOM_API_BATCH_VERSION;a.features=DOOM_API_BATCH_FEATURES;a.bytes=sizeof a;a.pointer_bytes=sizeof(void*);a.little_endian=1;a.file_id=1;a.file_bytes=sizeof wad;a.allocate=alloc;a.release=release;a.read=read_wad;a.ticks_ms=ticks;
 for(j=0;j<3;j++){maximum=j==0?512:j==1?4096:65536;a.max_read=maximum;assert(doom_cache_open(&c,&a));calls=0;
  assert(doom_cache_read(&c,500,output,100)==100&&!memcmp(output,wad+500,100));
  if(maximum==65536){assert(calls==1);assert(doom_cache_read(&c,30000,output,100)==100&&calls==1&&!memcmp(output,wad+30000,100));}
  for(i=0;i<10000;i++){seed=seed*1664525+1013904223;o=seed%sizeof wad;seed=seed*1664525+1013904223;n=seed%sizeof output;if(n>sizeof wad-o)n=sizeof wad-o;assert(doom_cache_read(&c,o,output,n)==n&&!memcmp(output,wad+o,n));}
#ifdef DOOM_WAD_PROFILE
  assert(c.profile_counts[0]==calls&&c.profile_counts[1]==calls&&c.profile_counts[2]==calls);
  for(i=0;i<4;i++)assert(c.profile_ms[i]==10*c.profile_counts[i]);
#endif
  assert(doom_cache_close(&c));
 }return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'test.c').write_text(code)
 for flags in ([],['-DDOOM_WAD_PROFILE']):
  subprocess.run(['cc',*flags,'-std=c99','-fsanitize=address,undefined','-fno-sanitize-recover=all','-I'+str(root),str(p/'test.c'),'-o',str(p/'test')],check=True)
  subprocess.run([str(p/'test')],check=True)
print('PASS 16,400 exact-edge alignment/tail copies per mode; cache: 30,000 reads across 512/4096/65536 modes; aligned read-ahead, adjacent hits, conflicts, multi-window reads and EOF exact')

#include "cache.h"
#include "w_file.h"
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
extern int doom_wad_backend_bind(const struct doom_runtime_v1*,const char*);
extern int doom_wad_backend_close(void);
extern wad_file_class_t stdc_wad_file;
static int read_at(unsigned id,unsigned off,void*p,unsigned n){unsigned i;assert(id==1&&n<=512);for(i=0;i<n;i++)((unsigned char*)p)[i]=(unsigned char)(off+i);return n;}
static void*allocate(unsigned n){return malloc(n);}
int main(void){struct doom_runtime_v1 a={0};wad_file_t*f;unsigned char dst[101];
 a.magic=DOOM_API_MAGIC;a.version=DOOM_API_VERSION;a.bytes=sizeof a;a.features=DOOM_API_FEATURES;a.pointer_bytes=sizeof(void*);a.little_endian=1;a.max_read=512;a.file_id=1;a.file_bytes=1024;a.allocate=allocate;a.release=free;a.read=read_at;
 assert(!stdc_wad_file.OpenFile("wad"));assert(doom_wad_backend_bind(&a,"wad"));assert(!doom_wad_backend_bind(&a,"other"));
 assert(!stdc_wad_file.OpenFile("other"));f=stdc_wad_file.OpenFile("wad");assert(f&&f->length==1024&&!f->mapped);assert(!stdc_wad_file.OpenFile("wad"));
 assert(stdc_wad_file.Read(f,500,dst,101)==101&&dst[0]==(unsigned char)500&&dst[100]==(unsigned char)600);
 stdc_wad_file.CloseFile(0);assert(stdc_wad_file.Read(f,1020,dst,20)==4);
 stdc_wad_file.CloseFile(f);assert(!stdc_wad_file.Read(f,0,dst,1)&&!stdc_wad_file.OpenFile("wad"));assert(doom_wad_backend_close());
 puts("PASS backend: single immutable file, path/double-open refusal, offset reads, EOF, close, stale descriptor cannot reopen");
}

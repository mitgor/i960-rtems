#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../cache/cache.h"
#include "wire.h"
static unsigned char*data;static unsigned bytes,requests,fragments;
static unsigned staging[8][136];
static struct doom_batch wire={.inbox=staging};
static unsigned crc(const unsigned char*p,unsigned n){unsigned c=~0u,i;while(n--){c^=*p++;for(i=0;i<8;i++)c=(c>>1)^(0xedb88320u&(0u-(c&1)));}return ~c;}
static void*allocate(unsigned n){return malloc(n);}
static int read_at(unsigned file,unsigned off,void*dst,unsigned n){unsigned done=0,k,count,p[136];assert(file==1&&n<=4096&&off<=bytes&&n<=bytes-off);requests++;
 assert(doom_batch_begin(&wire,off,n,bytes));
 while(done<n){memset(p,0,sizeof p);count=n-done;if(count>512)count=512;memcpy(p+8,data+off+done,count);p[0]=DOOM_BATCH_MAGIC;p[1]=wire.sequence;p[2]=1;p[3]=off+done;p[4]=count;p[6]=crc((unsigned char*)(p+8),count);p[7]=n;
 assert(!doom_batch_control(&wire,0x77,0,32+((count+3)&~3u),1));for(k=0;k<8+(count+3)/4;k++)assert(!doom_batch_control(&wire,0x78,k,p[k],1));assert(!doom_batch_control(&wire,0x79,0,0,1));done+=count;fragments++;}
 assert(doom_batch_claim(&wire));k=doom_batch_copy(&wire,dst,n);assert(k==n);doom_batch_cancel(&wire);return k;
}
int main(int argc,char**argv){FILE*f,*t;unsigned off,n,got,rows=0;unsigned char*out;struct doom_cache c={0};struct doom_runtime_v1 a={0};assert(argc==4);
 f=fopen(argv[1],"rb");assert(f);assert(!fseek(f,0,SEEK_END));bytes=ftell(f);rewind(f);data=malloc(bytes);out=malloc(bytes);assert(data&&out&&fread(data,1,bytes,f)==bytes);fclose(f);
 a.magic=DOOM_API_MAGIC;a.version=atoi(argv[3])==512?DOOM_API_VERSION:DOOM_API_BATCH_VERSION;a.features=atoi(argv[3])==512?DOOM_API_FEATURES:DOOM_API_BATCH_FEATURES;a.bytes=sizeof a;a.pointer_bytes=sizeof(void*);a.little_endian=1;a.max_read=atoi(argv[3]);a.file_id=1;a.file_bytes=bytes;a.allocate=allocate;a.release=free;a.read=read_at;
 assert(doom_cache_open(&c,&a));t=fopen(argv[2],"r");assert(t);
 while(fscanf(t,"%u %u %u",&off,&n,&got)==3){assert(got<=bytes&&doom_cache_read(&c,off,out,n)==(int)got&&!memcmp(out,data+off,got));rows++;}
 assert(feof(t));fclose(t);printf("{\"logical_reads\":%u,\"requests\":%u,\"fragments\":%u,\"hits\":%u,\"misses\":%u,\"wire_bytes\":%u,\"copied_bytes\":%u}\n",rows,requests,fragments,c.hits,c.misses,c.wire_bytes,c.copied_bytes);
 assert(doom_cache_close(&c));free(data);free(out);return 0;
}

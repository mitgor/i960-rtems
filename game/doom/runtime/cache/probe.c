#include "cache.h"
/* Real cache/runtime bridge; stack metadata, owning destination interior.
 * Cache hits and cross-line reads must match without exposing zone interiors
 * as runtime destinations. Every allocation is released before return. */
unsigned cache_entry(const struct doom_runtime_v1*a){
 struct doom_cache c;unsigned char*p;unsigned i,j,dir,n,h=2166136261u,before;int open=0;
 c.api=0;c.active=0;
 if(!a||a->file_bytes<2048)return 1;p=a->allocate(2048);if(!p)return 2;
 for(i=0;i<7;i++)p[i]=(unsigned char)(0xa0+i);
 if(!doom_cache_open(&c,a))goto bad;open=1;
 if(doom_cache_read(&c,0,p+7,12)!=12)goto bad;
 if(p[7]!='I'||p[8]!='W'||p[9]!='A'||p[10]!='D')goto bad;
 n=p[11]|(p[12]<<8)|(p[13]<<16)|((unsigned)p[14]<<24);
 dir=p[15]|(p[16]<<8)|(p[17]<<16)|((unsigned)p[18]<<24);
 if(!n||dir>a->file_bytes||n>(a->file_bytes-dir)/16||a->file_bytes-dir<512)goto bad;
 for(i=0;i<12;i++)h=(h^p[7+i])*16777619u;
 before=c.misses;
 if(doom_cache_read(&c,0,p+100,12)!=12||c.misses!=before||!c.hits)goto bad;
 for(i=0;i<12;i++)if(p[100+i]!=p[7+i])goto bad;
 if(doom_cache_read(&c,499,p+7,1111)!=1111)goto bad;
 for(i=0;i<1111;i++)h=(h^p[7+i])*16777619u;
 before=c.misses;if(doom_cache_read(&c,499,p+7,1111)!=1111||c.misses!=before)goto bad;
 if(doom_cache_read(&c,dir,p+7,512)!=512)goto bad;
 for(i=0;i<512;i++)h=(h^p[7+i])*16777619u;
 if(doom_cache_read(&c,a->file_bytes-37,p+7,128)!=37)goto bad;
 for(i=0;i<37;i++)h=(h^p[7+i])*16777619u;
 if(doom_cache_read(&c,a->file_bytes,p+7,1)!=0||doom_cache_read(&c,a->file_bytes+1,p+7,1)>=0)goto bad;
 for(j=0;j<7;j++)if(p[j]!=(unsigned char)(0xa0+j))goto bad;
 if(!doom_cache_close(&c))goto bad;open=0;a->release(p);return h;
 bad:if(open&&!doom_cache_close(&c))return 4;a->release(p);return 3;
}

#include "api.h"
/* No globals, absolute addresses, external imports or static data. The build
 * checks relocation-free identical bytes linked at two distinct addresses. */
unsigned int doom_runtime_probe(const struct doom_runtime_v1*a){
 unsigned char*p;unsigned int i,n,dir,h=2166136261u,start;int got;
 if(!a||a->magic!=DOOM_API_MAGIC||a->version!=DOOM_API_VERSION||a->bytes!=sizeof(*a)||a->features!=DOOM_API_FEATURES||a->pointer_bytes!=sizeof(void*)||a->little_endian!=1||a->max_read!=512||a->file_id!=1||a->file_bytes<512||a->reserved[0]||a->reserved[1])return 1;
 p=a->allocate(1024);if(!p)return 2;start=a->ticks_ms();
 if(a->read(1,0,p,12)!=12)goto bad;
 if(p[0]!='I'||p[1]!='W'||p[2]!='A'||p[3]!='D')goto bad;
 n=p[4]|(p[5]<<8)|(p[6]<<16)|((unsigned int)p[7]<<24);
 dir=p[8]|(p[9]<<8)|(p[10]<<16)|((unsigned int)p[11]<<24);
 if(!n||dir>a->file_bytes||n>(a->file_bytes-dir)/16||a->file_bytes-dir<512)goto bad;
 for(i=0;i<12;i++)h=(h^p[i])*16777619u;
 if(a->read(1,dir,p,512)!=512)goto bad;
 for(i=0;i<512;i++)h=(h^p[i])*16777619u;
 got=a->read(1,a->file_bytes-37,p,128);if(got!=37)goto bad;
 for(i=0;i<37;i++)h=(h^p[i])*16777619u;
 if(a->read(1,a->file_bytes,p,16)!=0||a->read(1,a->file_bytes+1,p,16)>=0||a->read(2,0,p,16)>=0||a->read(1,0,p,513)>=0||a->read(1,0,(void*)a,16)>=0)goto bad;
 if(a->ticks_ms()==start)goto bad;
 a->release(p);return h;
bad:a->release(p);return 3;
}

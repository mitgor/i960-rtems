#include "cache.h"
int doom_cache_open(struct doom_cache*c,const struct doom_runtime_v1*a){unsigned i;
 if(!c||c->api||c->active||!a||a->magic!=DOOM_API_MAGIC||a->version!=DOOM_API_VERSION||a->bytes!=sizeof(*a)||a->pointer_bytes!=sizeof(void*)||a->little_endian!=1||a->features!=DOOM_API_FEATURES||a->max_read!=DCACHE_LINE||a->file_id!=1||!a->file_bytes||a->file_bytes>268435456u||!a->allocate||!a->release||!a->read)return 0;
 c->active=1;c->data=a->allocate(DCACHE_LINES*DCACHE_LINE);
 if(!c->data){c->active=0;return 0;}c->bounce=a->allocate(DCACHE_LINE);
 if(!c->bounce){a->release(c->data);c->data=0;c->active=0;return 0;}
 c->api=a;c->reads=c->hits=c->misses=c->wire_bytes=c->copied_bytes=c->errors=0;c->last_error=0;
 for(i=0;i<DCACHE_LINES;i++)c->valid[i]=0;c->active=0;return 1;
}
int doom_cache_read(struct doom_cache*c,unsigned offset,void*dst,unsigned n){unsigned done=0,block,slot,within,count,want,i;int got;unsigned char*d=dst;
 if(!c||!c->api||c->active||offset>c->api->file_bytes||(!dst&&n))return -1;
 c->active=1;c->last_error=0;c->reads++;
 if(n>c->api->file_bytes-offset)n=c->api->file_bytes-offset;
 while(done<n){block=(offset+done)/DCACHE_LINE;slot=block%DCACHE_LINES;within=(offset+done)%DCACHE_LINE;
  if(!c->valid[slot]||c->tags[slot]!=block){
   c->misses++;want=c->api->file_bytes-block*DCACHE_LINE;if(want>DCACHE_LINE)want=DCACHE_LINE;
   got=c->api->read(1,block*DCACHE_LINE,c->bounce,want);
   if(got!=(int)want){c->last_error=got<0?got:-2;c->errors++;break;}
   for(i=0;i<want;i++)c->data[slot*DCACHE_LINE+i]=c->bounce[i];
   c->tags[slot]=block;c->valid[slot]=want;c->wire_bytes+=want;
  }else c->hits++;
  count=c->valid[slot]-within;if(count>n-done)count=n-done;
  for(i=0;i<count;i++)d[done+i]=c->data[slot*DCACHE_LINE+within+i];done+=count;c->copied_bytes+=count;
 }
 c->active=0;return done?(int)done:c->last_error;
}
int doom_cache_close(struct doom_cache*c){const struct doom_runtime_v1*a;
 if(!c||!c->api||c->active)return 0;c->active=1;a=c->api;
 a->release(c->bounce);a->release(c->data);c->bounce=c->data=0;c->api=0;c->active=0;return 1;
}

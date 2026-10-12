#include "heap.h"
#define CHUNK 1024u
static int enter(struct doom_heap *h) {
 if(!h||!h->initialized)return 0;
 if(!h->hooks.enter(h->hooks.cookie)){h->error=DH_DENIED;return 0;}
 if(h->fault||!arena_valid(h->arena)){h->fault=1;h->error=DH_CORRUPT;h->hooks.leave(h->hooks.cookie);return 0;}
 return 1;
}
static void leave(struct doom_heap*h){h->hooks.leave(h->hooks.cookie);}
static struct doom_allocation *find(struct doom_heap*h,void*p) {
 unsigned int i;for(i=0;i<ARENA_SLOTS;i++)if(h->slots[i].pointer==p)return h->slots+i;return 0;
}
/* Validate adapter metadata before using a stored handle, pointer or length. */
static int valid(struct doom_heap*h,struct doom_allocation*s) {
 unsigned int index=s->handle&255u;struct arena_slot*a;
 if(!index||index>ARENA_SLOTS)goto bad;
 a=&h->arena->slot[index-1];
 if(!a->span||a->generation!=(s->handle>>8)||a->bytes!=s->bytes||s->pointer!=h->arena->base+a->offset+16||!a->pins)goto bad;
 return 1;
bad:h->fault=1;h->error=DH_CORRUPT;return 0;
}
static struct doom_allocation *allocate(struct doom_heap*h,unsigned int n) {
 unsigned int i,handle;struct doom_allocation*s;
 if(h->stopping){h->error=DH_STOP;return 0;}
 if(!n)n=1; /* documented unique/freeable zero-size allocation */
 for(i=0;i<ARENA_SLOTS;i++)if(!h->slots[i].pointer)break;
 if(i==ARENA_SLOTS||(handle=arena_alloc(h->arena,n))==0){h->error=h->arena->poisoned?DH_CORRUPT:DH_OOM;h->fault|=h->arena->poisoned;return 0;}
 s=h->slots+i;s->pointer=arena_pin(h->arena,handle);
 if(!s->pointer){h->fault=1;h->error=DH_CORRUPT;return 0;}
 s->handle=handle;s->bytes=n;s->busy=0;h->live+=n;h->blocks++;
 if(h->live>h->peak)h->peak=h->live;if(h->blocks>h->peak_blocks)h->peak_blocks=h->blocks;
 h->error=DH_OK;return s;
}
static int release(struct doom_heap*h,struct doom_allocation*s) {
 if(!valid(h,s))return 0;
 if(s->busy||h->arena->slot[(s->handle&255u)-1].pins!=1){h->error=DH_BUSY;return 0;}
 if(!arena_unpin(h->arena,s->handle)||!arena_release(h->arena,s->handle)){h->fault=1;h->error=DH_CORRUPT;return 0;}
 h->live-=s->bytes;h->blocks--;s->pointer=0;s->handle=s->bytes=0;h->error=DH_OK;return 1;
}
int doom_heap_init(struct doom_heap*h,struct arena*a,const struct doom_heap_hooks*hooks) {
 unsigned int i;
 if(!h||h->initialized||!a||!hooks||!hooks->enter||!hooks->leave||!hooks->progress)return 0;
 if(!hooks->enter(hooks->cookie))return 0;
 if(!arena_valid(a)){hooks->leave(hooks->cookie);return 0;}
 h->arena=a;h->hooks=*hooks;h->stopping=h->fault=h->error=h->live=h->peak=h->blocks=h->peak_blocks=h->busy=0;
 for(i=0;i<ARENA_SLOTS;i++){h->slots[i].pointer=0;h->slots[i].handle=h->slots[i].bytes=h->slots[i].busy=0;}
 h->initialized=1;hooks->leave(hooks->cookie);return 1;
}
void *doom_heap_malloc(struct doom_heap*h,unsigned int n) {
 struct doom_allocation*s;void*p=0;if(!enter(h))return 0;
 s=allocate(h,n);if(s)p=s->pointer;leave(h);return p;
}
int doom_heap_free(struct doom_heap*h,void*p) {
 struct doom_allocation*s;int rc;if(!p)return 1;if(!enter(h))return 0;
 s=find(h,p);if(!s){h->error=DH_INVALID;leave(h);return 0;}
 rc=release(h,s);leave(h);return rc;
}
/* Reserve both allocations while unlocked. STOP can be signalled, but neither
 * another free nor drain may retire the live source/destination during copying. */
static void *bulk(struct doom_heap*h,void*old,unsigned int n,int zero,const char*string) {
 struct doom_allocation*src=0,*dst;unsigned int count,i,j;int ok=1;void*p;
 if(!enter(h))return 0;
 if(old){src=find(h,old);if(!src||!valid(h,src)||src->busy){if(!h->fault)h->error=src?DH_BUSY:DH_INVALID;leave(h);return 0;}}
 dst=allocate(h,n);if(!dst){leave(h);return 0;}
 dst->busy=1;if(src)src->busy=1;h->busy++;
 count=src?(src->bytes<n?src->bytes:n):n;p=dst->pointer;leave(h);
 for(i=0;i<count;i+=j){
  if(!h->hooks.progress(h->hooks.cookie)){ok=0;break;}
  j=count-i;if(j>CHUNK)j=CHUNK;
  {unsigned int k;unsigned char*d=(unsigned char*)p+i;
   const unsigned char*s=zero?0:(src?(const unsigned char*)old+i:(const unsigned char*)string+i);
   for(k=0;k<j;k++)d[k]=zero?0:s[k];}
 }
 /* Denied reentry/corruption leaves busy pins retained: completion is uncertain. */
 if(!enter(h))return 0;
 dst->busy=0;if(src)src->busy=0;h->busy--;
 if(!ok||h->stopping){release(h,dst);h->error=DH_STOP;leave(h);return 0;}
 if(src&&!release(h,src)){unsigned int error=h->error;release(h,dst);h->error=error;leave(h);return 0;}
 h->error=DH_OK;leave(h);return p;
}
void *doom_heap_calloc(struct doom_heap*h,unsigned int count,unsigned int size) {
 if(size&&count>~0u/size){if(h)h->error=DH_OOM;return 0;}
 return bulk(h,0,count*size,1,0);
}
void *doom_heap_realloc(struct doom_heap*h,void*p,unsigned int n) {
 if(!p)return doom_heap_malloc(h,n);
 if(!n){doom_heap_free(h,p);return 0;}
 return bulk(h,p,n,0,0);
}
char *doom_heap_strdup(struct doom_heap*h,const char*s) {
 unsigned int n=0;if(!s){if(h)h->error=DH_INVALID;return 0;}
 while(s[n]){if(n==0xfffffffeu){h->error=DH_OOM;return 0;}n++;}
 return bulk(h,0,n+1,0,s);
}
int doom_heap_stop(struct doom_heap*h){if(!enter(h))return 0;h->stopping=1;leave(h);return 1;}
int doom_heap_drain(struct doom_heap*h) {
 unsigned int i;if(!enter(h))return 0;
 if(!h->stopping||h->busy){h->error=DH_BUSY;leave(h);return 0;}
 /* Refuse before releasing ANY allocation if any holder remains. */
 for(i=0;i<ARENA_SLOTS;i++)if(h->slots[i].pointer){struct doom_allocation*s=h->slots+i;
  if(!valid(h,s)){leave(h);return 0;}
  if(s->busy||h->arena->slot[(s->handle&255u)-1].pins!=1){h->error=DH_BUSY;leave(h);return 0;}}
 for(i=0;i<ARENA_SLOTS;i++)if(h->slots[i].pointer&&!release(h,h->slots+i)){leave(h);return 0;}
 leave(h);return 1;
}

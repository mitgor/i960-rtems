#include "image.h"
unsigned int seg_crc32(unsigned int c,const void *data,unsigned int n) {
 const unsigned char *p=data;unsigned int i;c=~c;
 while(n--){c^=*p++;for(i=0;i<8;i++)c=(c>>1)^(0xedb88320u& (0u-(c&1)));}return ~c;
}
void seg_init(struct seg_image *s){s->state=SEG_EMPTY;s->handle=0;s->base=0;s->arena=0;}
int seg_begin(struct seg_image *s,struct arena *a,const struct manifest *m) {
 unsigned int i,j,end=0,entry=0,h;void *base;
 if(s->state!=SEG_EMPTY||m->abi!=SEG_ABI||!m->count||m->count>SEG_MAX||(m->entry&3))return 0;
 for(i=0;i<m->count;i++){const struct segment *p=&m->segment[i];unsigned int hi;
  if((p->offset&15)||!p->memory_bytes||p->file_bytes>p->memory_bytes||p->offset>a->bytes||p->memory_bytes>a->bytes-p->offset||
     (p->flags!=SEG_RX&&p->flags!=SEG_RW)||(p->flags==SEG_RX&&(p->file_bytes!=p->memory_bytes||(p->file_bytes&3))))return 0;
  hi=p->offset+p->memory_bytes;if(hi>end)end=hi;
  if(p->flags==SEG_RX&&m->entry>=p->offset&&m->entry-p->offset<p->file_bytes)entry=1;
  for(j=0;j<i;j++){const struct segment *q=&m->segment[j];if(p->offset<q->offset+q->memory_bytes&&q->offset<hi)return 0;}
 }
 if(!entry||(h=arena_alloc(a,end))==0)return 0;
 base=arena_pin(a,h);if(!base){arena_release(a,h);return 0;}
 s->arena=a;
 for(i=0;i<sizeof(*m);i++)((unsigned char*)&s->manifest)[i]=((const unsigned char*)m)[i];
 s->base=base;s->handle=h;s->state=SEG_LOADING;s->current=s->position=s->crc=0;
 for(i=0;i<SEG_MAX;i++)s->received[i]=0;return 1;
}
int seg_write(struct seg_image *s,unsigned int i,unsigned int offset,const void *data,unsigned int n) {
 const unsigned char *p=data;unsigned int j;struct segment *seg;
 if(s->state!=SEG_LOADING||i>=s->manifest.count||!p||!n||n>SEG_CHUNK||!arena_valid(s->arena))return 0;
 seg=&s->manifest.segment[i];if(offset!=s->received[i]||offset>seg->file_bytes||n>seg->file_bytes-offset)return 0;
 for(j=0;j<n;j++)s->base[seg->offset+offset+j]=p[j];s->received[i]+=n;return 1;
}
void seg_uncertain(struct seg_image *s){if(s->state!=SEG_EMPTY)s->state=SEG_QUARANTINED;}
int seg_prepare(struct seg_image *s,seg_cache_sync sync) {
 struct segment *p;unsigned int i,n;
 if(s->state==SEG_LOADING){for(i=0;i<s->manifest.count;i++)if(s->received[i]!=s->manifest.segment[i].file_bytes)return 0;s->state=SEG_VERIFYING;}
 if(s->state!=SEG_VERIFYING||!sync)return 0;
 if(!arena_valid(s->arena)){seg_uncertain(s);return 0;}
 p=&s->manifest.segment[s->current];
 if(s->position<p->file_bytes){n=p->file_bytes-s->position;if(n>SEG_CHUNK)n=SEG_CHUNK;
  s->crc=seg_crc32(s->crc,s->base+p->offset+s->position,n);s->position+=n;return 1;}
 if(s->crc!=p->crc32){seg_uncertain(s);return 0;}
 n=p->memory_bytes-s->position;if(n>SEG_CHUNK)n=SEG_CHUNK;
 for(i=0;i<n;i++)s->base[p->offset+s->position+i]=0;s->position+=n;
 if(s->position<p->memory_bytes)return 1;
 if(++s->current<s->manifest.count){s->position=s->crc=0;return 1;}
 for(i=0;i<s->manifest.count;i++){p=&s->manifest.segment[i];if(p->flags==SEG_RX&&!sync(s->base+p->offset,p->file_bytes)){seg_uncertain(s);return 0;}}
 s->state=SEG_READY;return 2;
}
void *seg_start(struct seg_image *s){if(s->state!=SEG_READY||!arena_valid(s->arena))return 0;s->state=SEG_RUNNING;return s->base+s->manifest.entry;}
static int discard(struct seg_image *s){if(!arena_unpin(s->arena,s->handle)||!arena_release(s->arena,s->handle)){seg_uncertain(s);return 0;}seg_init(s);return 1;}
int seg_complete(struct seg_image *s){if(s->state==SEG_CANCELLING)return discard(s);if(s->state!=SEG_RUNNING)return 0;s->state=SEG_READY;return 1;}
int seg_cancel(struct seg_image *s){if(s->state==SEG_EMPTY)return 1;if(s->state==SEG_QUARANTINED)return 0;
 if(s->state==SEG_RUNNING||s->state==SEG_CANCELLING){s->state=SEG_CANCELLING;return arena_cancel(s->arena,s->handle);}return discard(s);
}

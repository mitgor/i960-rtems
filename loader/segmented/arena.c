#include "arena.h"
#define GENERATION_MAX 0x00ffffffu
static struct arena_slot *lookup(struct arena *a,unsigned int h) {
 unsigned int i=(h&255u);struct arena_slot *s;
 if(!i||i>ARENA_SLOTS)return 0;
 s=&a->slot[i-1];return s->span&&s->generation==(h>>8)?s:0;
}
int arena_init(struct arena *a,void *base,unsigned int bytes) {
 unsigned int i;
 if(!a||!base||((unsigned long)base&15)||bytes<64||(bytes&15)||bytes>~0ul-(unsigned long)base)return 0;
 a->base=base;a->bytes=bytes;a->poisoned=0;
 for(i=0;i<ARENA_SLOTS;i++) {struct arena_slot *s=&a->slot[i];s->offset=s->bytes=s->span=s->generation=s->pins=s->cancelled=0;}
 return 1;
}
int arena_valid(struct arena *a) {
 unsigned int i,j,k;
 if(a->poisoned)return 0;
 for(i=0;i<ARENA_SLOTS;i++) {struct arena_slot *s=&a->slot[i];if(!s->span)continue;
  if(!s->generation||s->generation>GENERATION_MAX||s->cancelled>1||s->offset>a->bytes||s->span>a->bytes-s->offset||
     (s->offset&15)||(s->span&15)||s->span<48||!s->bytes||s->bytes>s->span-32)goto fail;
  for(j=0;j<i;j++) {struct arena_slot *t=&a->slot[j];if(t->span&&s->offset<t->offset+t->span&&t->offset<s->offset+s->span)goto fail;}
  for(k=0;k<16;k++)if(a->base[s->offset+k]!=(unsigned char)(0xa5^k)||a->base[s->offset+16+s->bytes+k]!=(unsigned char)(0x5a^k))goto fail;
 }
 return 1;
fail:a->poisoned=1;return 0;
}
unsigned int arena_alloc(struct arena *a,unsigned int bytes) {
 unsigned int i,j,off=0,span,next;struct arena_slot *s;
 if(!arena_valid(a)||!bytes||bytes>0xffffffd0u)return 0;
 span=(bytes+47u)&~15u;if(span>a->bytes)return 0;
 for(i=0;i<ARENA_SLOTS;i++)if(!a->slot[i].span&&a->slot[i].generation<GENERATION_MAX)break;
 if(i==ARENA_SLOTS)return 0;
 /* Each collision advances past a live interval. At most SLOTS collisions. */
 for(j=0;j<=ARENA_SLOTS;j++) {unsigned int k;next=off;
  if(span>a->bytes-off)return 0;
  for(k=0;k<ARENA_SLOTS;k++) {struct arena_slot *t=&a->slot[k];if(t->span&&off<t->offset+t->span&&t->offset<off+span&&next<t->offset+t->span)next=t->offset+t->span;}
  if(next==off)break;off=next;
 }
 if(j>ARENA_SLOTS)return 0;
 s=&a->slot[i];s->offset=off;s->bytes=bytes;s->span=span;s->generation++;s->pins=s->cancelled=0;
 for(j=0;j<16;j++){a->base[off+j]=0xa5^j;a->base[off+16+bytes+j]=0x5a^j;}
 return (s->generation<<8)|(i+1);
}
void *arena_pin(struct arena *a,unsigned int h) {
 struct arena_slot *s;if(!arena_valid(a)||(s=lookup(a,h))==0||s->cancelled||s->pins==~0u)return 0;
 s->pins++;return a->base+s->offset+16;
}
int arena_unpin(struct arena *a,unsigned int h) {
 struct arena_slot *s;if(!arena_valid(a)||(s=lookup(a,h))==0||!s->pins)return 0;s->pins--;return 1;
}
int arena_cancel(struct arena *a,unsigned int h) {
 struct arena_slot *s;if(!arena_valid(a)||(s=lookup(a,h))==0)return 0;s->cancelled=1;return 1;
}
int arena_release(struct arena *a,unsigned int h) {
 struct arena_slot *s;if(!arena_valid(a)||(s=lookup(a,h))==0||s->pins)return 0;s->span=0;s->bytes=0;return 1;
}

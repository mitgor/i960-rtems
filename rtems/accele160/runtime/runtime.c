#include "runtime.h"
void ar_init(struct ar_runtime *r,unsigned int epoch){
 r->parent=0;r->reservation=0;r->epoch=epoch;r->busy=r->poisoned=r->calls=0;seg_init(&r->image);
}
int ar_reserve(struct ar_runtime *r,struct arena *parent){
 unsigned int h;unsigned char *p;
 if(!r->epoch||r->reservation||r->poisoned||r->busy)return 0;
 h=arena_alloc(parent,AR_BYTES);if(!h)return 0;
 p=arena_pin(parent,h);if(!p){arena_release(parent,h);return 0;}
 r->parent=parent;r->reservation=h;
 if(!arena_init(&r->modules,p,AR_MODULE_BYTES)||!arena_init(&r->heap,p+AR_MODULE_BYTES,AR_HEAP_BYTES)){
  r->poisoned=1;return 0;
 }
 return 1;
}
int ar_valid(struct ar_runtime *r){
 if(r->poisoned||!r->reservation)return 0;
 if(!arena_valid(r->parent)||!arena_valid(&r->modules)||!arena_valid(&r->heap)){
  r->poisoned=1;seg_uncertain(&r->image);return 0;
 }
 return 1;
}
int ar_begin(struct ar_runtime *r,unsigned int board,unsigned int abi,unsigned long linked_base,const struct manifest *m){
 if(board!=AR_BOARD||abi!=AR_ABI||r->busy||!ar_valid(r))return 0;
 /* Absolute, import-free i960 images are tied to their exact allocated base.
  * No arbitrary write address or relocation/import table is accepted. */
 if(linked_base!=(unsigned long)r->modules.base+ARENA_GUARD)return 0;
 if(!seg_begin(&r->image,&r->modules,m))return 0;
 if((unsigned long)r->image.base!=linked_base){seg_cancel(&r->image);return 0;}
 return 1;
}
unsigned int ar_alloc(struct ar_runtime *r,unsigned int n){return ar_valid(r)?arena_alloc(&r->heap,n):0;}
void *ar_pin(struct ar_runtime *r,unsigned int h){return ar_valid(r)?arena_pin(&r->heap,h):0;}
int ar_unpin(struct ar_runtime *r,unsigned int h){return ar_valid(r)&&arena_unpin(&r->heap,h);}
int ar_cancel(struct ar_runtime *r,unsigned int h){return ar_valid(r)&&arena_cancel(&r->heap,h);}
int ar_release(struct ar_runtime *r,unsigned int h){return ar_valid(r)&&arena_release(&r->heap,h);}
int ar_close(struct ar_runtime *r){unsigned int i,epoch=r->epoch;
 if(!r->reservation)return !r->poisoned;
 if(r->busy||!ar_valid(r))return 0;
 for(i=0;i<ARENA_SLOTS;i++)if(r->heap.slot[i].span)return 0;
 if(!seg_cancel(&r->image))return 0;
 for(i=0;i<ARENA_SLOTS;i++)if(r->modules.slot[i].span)return 0;
 if(!arena_unpin(r->parent,r->reservation)||!arena_release(r->parent,r->reservation)){r->poisoned=1;return 0;}
 /* Retain generation history for the parent. A new service epoch is required
  * before any new child heap can be created, preventing old handle reuse. */
 ar_init(r,epoch==0xffffffffu?0:epoch+1u);return 1;
}
/* Bounded, non-destructive allocation qualification on the actual card.
 * No interrupt masking. Any mismatch retains the entire parent reservation. */
unsigned int ar_heap_proof(struct ar_runtime *r){
 unsigned int h,k,i,mask=0;unsigned char *p;
 if(!ar_valid(r)||r->busy)return 0;
 for(i=0;i<ARENA_SLOTS;i++)if(r->heap.slot[i].span)return 0;
 h=ar_alloc(r,4097);if(!h)goto fail;mask|=1;
 p=ar_pin(r,h);if(!p||((unsigned long)p&15))goto fail;mask|=2;
 for(i=0;i<4097;i++)p[i]=(unsigned char)(i*17u);
 if(!ar_cancel(r,h)||ar_pin(r,h)||ar_release(r,h))goto fail;mask|=4;
 for(i=0;i<4097;i++)if(p[i]!=(unsigned char)(i*17u))goto fail;mask|=8;
 if(!ar_unpin(r,h)||!ar_release(r,h)||ar_pin(r,h))goto fail;mask|=16;
 k=ar_alloc(r,4097);if(!k||k==h||ar_pin(r,h)||!ar_release(r,k))goto fail;mask|=32;
 if(ar_alloc(r,AR_HEAP_BYTES)||ar_alloc(r,0)||ar_alloc(r,~0u))goto fail;mask|=64;
 for(i=0;i<ARENA_SLOTS;i++)if(r->heap.slot[i].span)goto fail;
 if(!ar_valid(r))goto fail;return mask|128;
fail:r->poisoned=1;seg_uncertain(&r->image);return mask;
}

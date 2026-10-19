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

void ar_loan_init(struct ar_loan *l){l->parent=0;l->handle=l->owner=l->cancelled=l->poisoned=l->proof_handle=l->offset=l->phase=0;l->proof=0;}
static int loan_valid(struct ar_loan *l){
 if(!l->handle||l->poisoned)return 0;
 if(!arena_valid(l->parent)||!arena_valid(&l->heap)){l->poisoned=1;return 0;}return 1;
}
int ar_loan_attach(struct ar_loan *l,struct arena *p,unsigned int h,unsigned int bytes,unsigned int owner){
 unsigned int i=(h&255u);void *base;
 if(l->handle||l->poisoned||!owner||owner<=l->owner||!i||i>ARENA_SLOTS||!arena_valid(p))return 0;
 if(p->slot[i-1].generation!=(h>>8)||p->slot[i-1].bytes!=bytes||p->slot[i-1].pins!=1||p->slot[i-1].cancelled)return 0;
 base=arena_pin(p,h);if(!base)return 0;
 l->parent=p;l->handle=h;l->owner=owner;
 if(!arena_init(&l->heap,base,bytes)){l->poisoned=1;return 0;}return 1;
}
unsigned int ar_loan_alloc(struct ar_loan *l,unsigned int owner,unsigned int bytes){
 return owner==l->owner&&!l->cancelled&&loan_valid(l)?arena_alloc(&l->heap,bytes):0;
}
void *ar_loan_pin(struct ar_loan *l,unsigned int owner,unsigned int h){
 return owner==l->owner&&!l->cancelled&&loan_valid(l)?arena_pin(&l->heap,h):0;
}
int ar_loan_unpin(struct ar_loan *l,unsigned int owner,unsigned int h){
 return owner==l->owner&&loan_valid(l)&&arena_unpin(&l->heap,h);
}
int ar_loan_free(struct ar_loan *l,unsigned int owner,unsigned int h){
 return owner==l->owner&&loan_valid(l)&&arena_release(&l->heap,h);
}
int ar_loan_cancel(struct ar_loan *l,unsigned int owner){unsigned int i;
 if(owner!=l->owner||!loan_valid(l))return 0;l->cancelled=1;
 for(i=0;i<ARENA_SLOTS;i++)if(l->heap.slot[i].span)l->heap.slot[i].cancelled=1;
 return 1;
}
int ar_loan_release(struct ar_loan *l,unsigned int owner){unsigned int i;
 if(owner!=l->owner||!l->cancelled||!loan_valid(l))return 0;
 for(i=0;i<ARENA_SLOTS;i++)if(l->heap.slot[i].span)return 0;
 if(!arena_unpin(l->parent,l->handle)){l->poisoned=1;return 0;}
 ar_loan_init(l);l->owner=owner;return 1;
}
/* At most 64 KiB per call; cancellation is requested with the entire region
 * pinned. Verify the retained bytes before completion/unpin/release. */
unsigned int ar_loan_proof(struct ar_loan *l){unsigned int i,end,n;
 if(!loan_valid(l))return 0;n=l->heap.bytes-32u;
 if(!l->phase){
  l->proof_handle=ar_loan_alloc(l,l->owner,n);
  l->proof=ar_loan_pin(l,l->owner,l->proof_handle);
  if(!l->proof||ar_loan_pin(l,l->owner,l->proof_handle)!=l->proof)goto fail;l->phase=1;
 }
 if(l->phase==1||l->phase==2){
  end=l->offset+65536u;if(end>n)end=n;
  for(i=l->offset;i<end;i++){
   unsigned char v=(unsigned char)((i*17u)^(i>>12));
   if(l->phase==1)l->proof[i]=v;else if(l->proof[i]!=v)goto fail;
  }
  l->offset=end;
  if(end==n){
   l->offset=0;
   if(l->phase==1){
    if(!ar_loan_cancel(l,l->owner)||ar_loan_alloc(l,l->owner,16)||ar_loan_pin(l,l->owner,l->proof_handle)||ar_loan_release(l,l->owner)||ar_loan_free(l,l->owner,l->proof_handle))goto fail;
    l->phase=2;
   }else{
    if(!ar_loan_unpin(l,l->owner,l->proof_handle)||ar_loan_free(l,l->owner,l->proof_handle)||ar_loan_release(l,l->owner))goto fail;
    if(!ar_loan_unpin(l,l->owner,l->proof_handle)||!ar_loan_free(l,l->owner,l->proof_handle)||arena_pin(&l->heap,l->proof_handle))goto fail;
    l->phase=3;
   }
  }
 }
 return l->phase;
fail:l->poisoned=1;return 0;
}

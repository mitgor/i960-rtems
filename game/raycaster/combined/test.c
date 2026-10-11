#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "queue.h"
#include "ray.h"
static unsigned char slots[FQ_SIZE] __attribute__((aligned(16))),saved[FQ_SIZE];
static void req(unsigned char*r,unsigned op,unsigned gen,unsigned ack){
 memset(r,0,64);fq_put(r,FQ_MAGIC);fq_put(r+4,op);fq_put(r+8,1);fq_put(r+16,gen);fq_put(r+20,ack);
 if(op==1||op==4){fq_put(r+32,RAY_MAGIC);fq_put(r+36,1);fq_put(r+40,80);fq_put(r+48,1);}
}
int main(void){struct fq_state s={0},before;unsigned char in[64],out[64],*ray=calloc(1,ray_size()),*save_ray=malloc(ray_size());
 req(in,0,0,0);assert(!fq_request(&s,ray,slots,in,64,out,64,1));
 req(in,1,1,0);assert(!fq_request(&s,ray,slots,in,64,out,64,2));
 memcpy(saved,slots,FQ_SIZE);memcpy(save_ray,ray,ray_size());before=s;
 for(unsigned n=0;n<=65;n++)if(n!=64){req(in,4,2,1);assert(!fq_request(&s,ray,slots,in,n,out,64,3));assert(fq_word(out+8)==FQ_BAD);assert(!memcmp(&s,&before,sizeof(s))&&!memcmp(slots,saved,FQ_SIZE)&&!memcmp(ray,save_ray,ray_size()));}
 req(in,4,2,1);memset(out,0x77,64);assert(fq_request(&s,ray,slots,in,64,out,63,4)==2);for(unsigned i=0;i<64;i++)assert(out[i]==0x77);
 assert(!memcmp(&s,&before,sizeof(s))&&!memcmp(slots,saved,FQ_SIZE)&&!memcmp(ray,save_ray,ray_size()));
 /* Every corrupt occupied-slot byte blocks replacement, including malformed
  * READY/hash/guards. No ACK or render is allowed to consume a bad publication. */
 for(unsigned i=0;i<FQ_SLOT_SIZE;i++){
  slots[i]^=1;unsigned char damaged=slots[i];
  assert(!fq_request(&s,ray,slots,in,64,out,64,5));assert(fq_word(out+8)==FQ_CORRUPT&&slots[i]==damaged);
  slots[i]^=1;assert(!memcmp(&s,&before,sizeof(s))&&!memcmp(slots,saved,FQ_SIZE)&&!memcmp(ray,save_ray,ray_size()));
 }
 s.last=0xffffffffu;before=s;req(in,4,0,1);assert(!fq_request(&s,ray,slots,in,64,out,64,6)&&fq_word(out+8)==FQ_STALE);
 assert(!memcmp(&s,&before,sizeof(s))&&!memcmp(slots,saved,FQ_SIZE)&&!memcmp(ray,save_ray,ray_size()));
 free(ray);free(save_ray);puts("PASS: bad lengths/capacity, 5120 corrupt publication bytes and generation exhaustion preserve queue/renderer; ASan/UBSan");return 0;
}

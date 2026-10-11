#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "queue.h"
#include "ray.h"
static unsigned char slots[FQ_SIZE] __attribute__((aligned(16))),saved[FQ_SIZE];
static void req(unsigned char*r,unsigned int op,unsigned int epoch,unsigned int slot,unsigned int gen){
 memset(r,0,64);fq_put(r,FQ_MAGIC);fq_put(r+4,op);fq_put(r+8,epoch);fq_put(r+12,slot);fq_put(r+16,gen);
 if(op==1){fq_put(r+32,RAY_MAGIC);fq_put(r+36,1);fq_put(r+40,80);fq_put(r+48,1);}
}
int main(void){struct fq_state s={0},before;unsigned char in[64],out[64],*ray=calloc(1,ray_size()),*ray_before=malloc(ray_size());unsigned int i,j;
 req(in,0,1,0,0);assert(!fq_request(&s,ray,slots,in,64,out,64,1));assert(s.epoch==1&&!s.mask);
 for(i=0;i<2;i++){req(in,1,1,i,i+1);assert(!fq_request(&s,ray,slots,in,64,out,64,i+2));assert(!fq_word(out+8)&&fq_valid(slots+i*FQ_SLOT_SIZE,1,i+1,i));}
 memcpy(saved,slots,FQ_SIZE);before=s;memcpy(ray_before,ray,ray_size());
 req(in,1,1,0,3);assert(!fq_request(&s,ray,slots,in,64,out,64,4));assert(fq_word(out+8)==FQ_BUSY);
 assert(!memcmp(saved,slots,FQ_SIZE)&&!memcmp(&s,&before,sizeof(s))&&!memcmp(ray,ray_before,ray_size()));
 for(i=0;i<32;i++){
  req(in,2,1,0,1^(1u<<i));assert(!fq_request(&s,ray,slots,in,64,out,64,5));assert(fq_word(out+8)==FQ_STALE);
  assert(!memcmp(saved,slots,FQ_SIZE)&&!memcmp(&s,&before,sizeof(s)));
 }
 for(i=0;i<FQ_SLOT_SIZE;i++)for(j=0;j<8;j++){
  slots[i]^=1u<<j;assert(!fq_valid(slots,1,1,0));slots[i]^=1u<<j;
 }
 fq_put(slots+16,0);assert(!fq_valid(slots,1,1,0));req(in,3,1,0,0);
 assert(!fq_request(&s,ray,slots,in,64,out,64,6)&&fq_word(out+8)==FQ_CORRUPT);memcpy(slots,saved,FQ_SIZE);
 assert(!fq_valid(slots,2,1,0)&&!fq_valid(slots,1,2,0)&&!fq_valid(slots,1,1,1));
 req(in,2,2,0,1);assert(!fq_request(&s,ray,slots,in,64,out,64,7)&&fq_word(out+8)==FQ_STALE);
 req(in,0,2,0,0);assert(!fq_request(&s,ray,slots,in,64,out,64,8)&&fq_word(out+8)==FQ_BUSY);
 for(i=0;i<2;i++){req(in,2,1,i,i+1);assert(!fq_request(&s,ray,slots,in,64,out,64,9)&&!fq_word(out+8));}
 req(in,2,1,0,1);assert(!fq_request(&s,ray,slots,in,64,out,64,10)&&fq_word(out+8)==FQ_STALE);
 req(in,0,1,0,0);assert(!fq_request(&s,ray,slots,in,64,out,64,11)&&fq_word(out+8)==FQ_STALE);
 req(in,0,2,0,0);assert(!fq_request(&s,ray,slots,in,64,out,64,12)&&!fq_word(out+8));
 s.last=0xffffffffu;before=s;memcpy(saved,slots,FQ_SIZE);req(in,1,2,0,0);
 assert(!fq_request(&s,ray,slots,in,64,out,64,13)&&fq_word(out+8)==FQ_STALE);
 assert(!memcmp(saved,slots,FQ_SIZE)&&!memcmp(&s,&before,sizeof(s)));
 memset(out,0x77,64);assert(fq_request(&s,ray,slots,in,64,out,63,14)==2);for(i=0;i<64;i++)assert(out[i]==0x77);
 assert(!memcmp(saved,slots,FQ_SIZE)&&!memcmp(&s,&before,sizeof(s)));
 free(ray);free(ray_before);puts("PASS: two-slot backpressure, wrong/duplicate ACK, epoch reset, wrap refusal, incomplete/corrupt publication, 40960 bit corruptions, insufficient output; ASan/UBSan");return 0;
}

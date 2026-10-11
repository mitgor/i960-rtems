#include "queue.h"
#include "ray.h"
#include <stddef.h>
extern void *memset(void*,int,size_t);
static void report(struct fq_state*s,unsigned char*out,unsigned int status,unsigned int sequence){
 unsigned int i;for(i=0;i<FQ_REPLY;i++)out[i]=0;
 fq_put(out,FQ_MAGIC);fq_put(out+4,1);fq_put(out+8,status);fq_put(out+12,s->epoch);
 fq_put(out+16,s->mask);fq_put(out+20,s->last);fq_put(out+24,s->gen[0]);fq_put(out+28,s->gen[1]);
 fq_put(out+32,s->mask&1?FQ_FRAME:0);fq_put(out+36,s->mask&2?FQ_FRAME:0);fq_put(out+40,sequence);
}
unsigned int fq_request(struct fq_state*s,void*ray,unsigned char*slots,const unsigned char*in,unsigned int n,unsigned char*out,unsigned int cap,unsigned int sequence){
 unsigned int op,epoch,slot,gen,i,status=0,rc;unsigned char *p;
 unsigned char reset[32]={0},header[64];
 if(cap<FQ_REPLY)return 2;
 if(n!=64||fq_word(in)!=FQ_MAGIC){report(s,out,FQ_BAD,sequence);return 0;}
 op=fq_word(in+4);epoch=fq_word(in+8);slot=fq_word(in+12);gen=fq_word(in+16);
 if(op>3||slot>1||!epoch||fq_word(in+20)||fq_word(in+24)||fq_word(in+28)){status=FQ_BAD;goto done;}
 for(i=0;i<2;i++)if((s->mask&(1u<<i))&&!fq_valid(slots+i*FQ_SLOT_SIZE,s->epoch,s->gen[i],i)){status=FQ_CORRUPT;goto done;}
 if(op!=1){for(i=32;i<64;i++)if(in[i]){status=FQ_BAD;goto done;}}
 if(op==0){
  if(slot||gen){status=FQ_BAD;goto done;}
  if(s->mask){status=FQ_BUSY;goto done;}
  if(epoch<=s->epoch){status=FQ_STALE;goto done;}
  fq_put(reset,RAY_MAGIC);rc=ray_request(ray,reset,32,header,64);if(rc)return rc;
  memset(slots,0,FQ_SIZE);s->epoch=epoch;s->last=0;s->mask=0;s->gen[0]=s->gen[1]=0;
 }else{
  if(epoch!=s->epoch){status=FQ_STALE;goto done;}
  if(op==1){
   /* One complete bounded frame only; no arbitrary target program or address. */
   if(fq_word(in+32)!=RAY_MAGIC||fq_word(in+36)!=1||fq_word(in+40)!=80||fq_word(in+44)>15||fq_word(in+48)!=1||fq_word(in+52)||fq_word(in+56)||fq_word(in+60)){status=FQ_BAD;goto done;}
   if(s->last==0xffffffffu||gen!=s->last+1){status=FQ_STALE;goto done;}
   if(s->mask&(1u<<slot)){status=FQ_BUSY;goto done;}
   p=slots+slot*FQ_SLOT_SIZE;memset(p,0xa5,64);fq_put(p+16,0);
   rc=ray_request(ray,in+32,32,p+64,FQ_FRAME);if(rc)return rc;
   memset(p+64+FQ_FRAME,0x5a,FQ_SLOT_SIZE-64-FQ_FRAME);
   fq_put(p,FQ_MAGIC);fq_put(p+4,epoch);fq_put(p+8,gen);fq_put(p+12,FQ_FRAME);
   fq_put(p+20,fq_hash(p+64,FQ_FRAME));fq_put(p+24,~gen);fq_put(p+28,slot);
   /* Only read after runner completion/cache maintenance. This is not an
    * asynchronous DMA publication barrier or permission to poll live slots. */
   __asm__ volatile("":::"memory");
   *(volatile unsigned int*)(p+16)=FQ_READY;
   s->gen[slot]=gen;s->last=gen;s->mask|=1u<<slot;
  }else if(op==2){
   if(!(s->mask&(1u<<slot))||gen!=s->gen[slot]){status=FQ_STALE;goto done;}
   fq_put(slots+slot*FQ_SLOT_SIZE+16,0);s->mask&=~(1u<<slot);
  }else if(slot||gen){status=FQ_BAD;goto done;}
 }
 done:report(s,out,status,sequence);return 0;
}

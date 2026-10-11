#include <assert.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
typedef unsigned char u8;
#define STAGING_BASE 0xc0f2c000u
#define BIO_BASE 0xc0f9c000u
#define BIO_OFFSET 0x70000u
#define BIO_OUTPUT 4176u
#include "queue.h"
struct capture {u8*data;};
struct experiment {struct capture capture[60],stage[8];unsigned int sequence;int pending;};
static u8 response[64],slots[FQ_SIZE];
static int calls,fail,uncertain;
static int read_pair(struct experiment*d,unsigned int address,unsigned short count,unsigned int slot){
 const u8*p;int pass;
 if(address==BIO_BASE+BIO_OUTPUT){assert(count==64&&slot==54);p=response;}
 else {unsigned int i=(address-STAGING_BASE-FQ_OFFSET)/FQ_SLOT_SIZE;assert(i<2&&address==STAGING_BASE+FQ_OFFSET+i*FQ_SLOT_SIZE&&count==FQ_SLOT_SIZE&&slot==56+2*i);p=slots+i*FQ_SLOT_SIZE;}
 for(pass=0;pass<2;pass++){
  calls++;if(calls==fail){d->pending=uncertain;return uncertain?-ETIMEDOUT:-ENODATA;}
  memcpy(d->capture[slot+pass].data,p,count);
 }
 return 0;
}
#include "transport.h"
int main(void){struct experiment d={0};unsigned int i,j;unsigned char original[64];
 for(i=54;i<60;i++)d.capture[i].data=calloc(1,FQ_SLOT_SIZE);
 d.stage[6].data=calloc(1,524288);d.sequence=3;
 fq_put(response,FQ_MAGIC);fq_put(response+4,1);fq_put(response+12,9);fq_put(response+16,3);fq_put(response+20,2);fq_put(response+24,1);fq_put(response+28,2);fq_put(response+32,FQ_FRAME);fq_put(response+36,FQ_FRAME);fq_put(response+40,3);
 for(i=0;i<2;i++){u8*p=slots+i*FQ_SLOT_SIZE;memset(p,0xa5,64);memset(p+64+FQ_FRAME,0x5a,FQ_SLOT_SIZE-64-FQ_FRAME);fq_put(p,FQ_MAGIC);fq_put(p+4,9);fq_put(p+8,i+1);fq_put(p+12,FQ_FRAME);fq_put(p+16,FQ_READY);fq_put(p+20,fq_hash(p+64,FQ_FRAME));fq_put(p+24,~(i+1));fq_put(p+28,i);}
 assert(!fq_targeted(&d)&&calls==6);
 memcpy(d.stage[6].data+BIO_OFFSET+BIO_OUTPUT,response,64);memcpy(d.stage[6].data+FQ_OFFSET,slots,FQ_SIZE);assert(!fq_match_audit(&d));
 for(i=0;i<FQ_SIZE;i++){d.stage[6].data[FQ_OFFSET+i]^=1;assert(fq_match_audit(&d)==-ENODATA);d.stage[6].data[FQ_OFFSET+i]^=1;}
 for(i=0;i<64;i++){d.stage[6].data[BIO_OFFSET+BIO_OUTPUT+i]^=1;assert(fq_match_audit(&d)==-ENODATA);d.stage[6].data[BIO_OFFSET+BIO_OUTPUT+i]^=1;}
 for(uncertain=0;uncertain<2;uncertain++)for(fail=1;fail<=6;fail++){calls=0;d.pending=0;assert(fq_targeted(&d)==(uncertain?-ETIMEDOUT:-ENODATA));assert(calls==fail&&d.pending==uncertain);}
 fail=0;uncertain=0;d.pending=0;memcpy(original,response,64);
 for(i=0;i<64;i++)for(j=0;j<8;j++){
  /* Fields with semantic ranges can remain valid; publication identity,
   * capacities, reserved bytes and sequence must never silently change. */
  if(i>=8&&i<32)continue;
  response[i]^=1u<<j;assert(fq_targeted(&d)==-ENODATA);memcpy(response,original,64);
 }
 for(i=54;i<60;i++){free(d.capture[i].data);}
 free(d.stage[6].data);
 puts("PASS: six read boundaries with completed failure/timeout; 10304 targeted-vs-full byte mismatches; strict descriptor mutations");return 0;
}

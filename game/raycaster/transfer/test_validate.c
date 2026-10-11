#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define bio_response_valid slow_response
#include "baseline.h"
#undef bio_response_valid
#include "validate.h"
static unsigned char before[524288],after[524288];
static void request(void){
 unsigned i;memset(before,0,sizeof(before));
 bio_put(before+BIO_OFFSET,BIO_MAGIC);bio_put(before+BIO_OFFSET+4,1);
 bio_put(before+BIO_OFFSET+8,73);bio_put(before+BIO_OFFSET+16,BIO_OUTPUT_MAX);
 bio_put(before+BIO_OFFSET+20,BIO_PENDING);
 memset(before+BIO_OFFSET+BIO_GUARD1,0xa5,16);
 memset(before+BIO_OFFSET+BIO_OUTPUT,0xcc,BIO_OUTPUT_MAX);
 memset(before+BIO_OFFSET+BIO_GUARD2,0x5a,16);
 for(i=0;i<0x20000;i++)before[i]=(unsigned char)(i*17+9);
 assert(bio_request_valid(before+BIO_OFFSET));
 memcpy(after,before,sizeof(after));bio_put(after+BIO_OFFSET+20,0);
 bio_put(after+BIO_OFFSET+24,4864);bio_put(after+BIO_OFFSET+28,73);
 memset(after+BIO_OFFSET+BIO_OUTPUT,0x42,4864);
}
static void agree(unsigned size){assert(slow_response(before,after,size)==bio_response_valid(before,after,size));}
int main(void){unsigned i,j,n,seed=7;unsigned fields[]={20,24,28};unsigned values[]={0,1,73,74,8192,8193,0xffffffff};
 request();assert(bio_response_valid(before,after,sizeof(after)));
 /* Every immutable byte individually: independent address-contract oracle. */
 for(i=0;i<sizeof(after);i++){
  int mutable=(i>=0x20010&&i<0x6fff0)||(i>=BIO_OFFSET+BIO_OUTPUT&&i<BIO_OFFSET+BIO_OUTPUT+4864);
  if(i>=BIO_OFFSET+20&&i<BIO_OFFSET+32)continue; /* separately exercise metadata */
  after[i]^=1;
  assert(bio_response_valid(before,after,sizeof(after))==mutable);
  if(!(i%1024))agree(sizeof(after));
  after[i]^=1;
 }
 for(i=0;i<3;i++)for(j=0;j<7;j++){
  request();bio_put(after+BIO_OFFSET+fields[i],values[j]);agree(sizeof(after));agree(BIO_IMAGE_SIZE);
 }
 for(n=0;n<=BIO_OUTPUT_MAX;n++){
  request();memcpy(after+BIO_OFFSET+BIO_OUTPUT,before+BIO_OFFSET+BIO_OUTPUT,BIO_OUTPUT_MAX);
  bio_put(after+BIO_OFFSET+24,n);memset(after+BIO_OFFSET+BIO_OUTPUT,0x28,n);
  assert(bio_response_valid(before,after,sizeof(after)));
  if(!(n%127))agree(sizeof(after));
  after[BIO_OFFSET+BIO_OUTPUT+n]^=1;assert(!bio_response_valid(before,after,sizeof(after)));
 }
 for(j=0;j<512;j++){
  request();seed=seed*1664525u+1013904223u;i=seed%sizeof(after);after[i]^=0x80;agree(sizeof(after));agree(BIO_IMAGE_SIZE);
 }
 request();assert(!bio_response_valid(before,after,BIO_IMAGE_SIZE-1));
 puts("PASS: every immutable byte; all 8193 output boundaries; metadata, random corruption and prefix/full differential checks");
 return 0;
}

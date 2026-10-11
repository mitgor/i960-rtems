#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "ray.h"
unsigned int fast_size(void);
unsigned int fast_request(void*,const unsigned char*,unsigned int,unsigned char*,unsigned int);
#include "original_io.h"
#undef I960_BUFFER_IO_H
#define bio_word fast_word
#define bio_put fast_put
#define bio_request_valid fast_valid
#define bio_response_valid fast_response
#include "fast_io.h"
static void put(unsigned char*p,unsigned int x){bio_put(p,x);}
static unsigned int seed=123456789;
static unsigned int random32(void){seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;return seed;}
int main(void){
 unsigned int i,j,k,n,offset;unsigned char in[32],a[4866],b[4866];
 void *old=calloc(1,ray_size()),*fast=calloc(1,fast_size());
 assert(old&&fast&&ray_size()==fast_size());
 for(i=0;i<20000;i++){
  unsigned int op=i?random32()%4:0,pixels=random32()%2,cap=pixels?4864:64;
  memset(in,0,32);put(in,RAY_MAGIC);put(in+4,op);put(in+16,pixels);
  if(op==1){put(in+8,random32()%80+1);put(in+12,random32()%16);}
  if(op==3){put(in+20,random32()%9);put(in+24,random32()%128+1);}
  memset(a,0xa5,sizeof(a));memset(b,0xa5,sizeof(b));
  if(i%7==0&&i)in[random32()%32]^=1u<<(random32()%8);
  if(i%11==0&&i)cap--;
  assert(ray_request(old,in,32,a+1,cap)==fast_request(fast,in,32,b+1,cap));
  assert(!memcmp(a,b,sizeof(a)));assert(!memcmp(old,fast,ray_size()));
 }
 free(old);free(fast);
 /* Every byte corruption must agree with the old validator, at each alignment. */
 for(offset=0;offset<4;offset++){
  unsigned char *allocation=malloc(BIO_SIZE+offset),*p=allocation+offset;
  for(n=0;n<=BIO_INPUT_MAX;n++){
   memset(p,0,BIO_SIZE);put(p,BIO_MAGIC);put(p+4,1);put(p+8,1);put(p+12,n);
   put(p+16,BIO_OUTPUT_MAX);put(p+20,BIO_PENDING);
   memset(p+BIO_GUARD1,0xa5,16);memset(p+BIO_GUARD2,0x5a,16);memset(p+BIO_OUTPUT,0xcc,BIO_OUTPUT_MAX);
   assert(bio_request_valid(p)&&fast_valid(p));
   if(n==32)for(i=0;i<BIO_SIZE;i++)for(k=0;k<8;k++){
    p[i]^=1u<<k;assert(bio_request_valid(p)==fast_valid(p));p[i]^=1u<<k;
   }
  }
  free(allocation);
 }
 /* Exact allocated endpoints plus all lengths/alignments for the primitive. */
 for(offset=0;offset<4;offset++)for(n=0;n<260;n++){
  unsigned char *allocation=malloc(n+offset?n+offset:1),*p=allocation+offset;
  for(k=0;k<3;k++){
   unsigned char value=k==0?0:k==1?0xa5:0xcc;
   memset(p,value,n);assert(bio_uniform(p,n,value));
   for(j=0;j<n;j++){p[j]^=1;assert(!bio_uniform(p,n,value));p[j]^=1;}
  }
  free(allocation);
 }
 puts("PASS: 20000 differential requests; 396288 single-bit BIO mutations; all 4097 input lengths at four alignments; exact uniform range tests");
 return 0;
}

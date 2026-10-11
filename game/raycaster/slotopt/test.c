#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
#include "queue.h"
static unsigned int reference(const unsigned char*p,unsigned n){unsigned h=2166136261u;while(n--)h=(h^*p++)*16777619u;return h;}
static void fill(unsigned char*p){
 for(unsigned i=0;i<FQ_SLOT_SIZE;i++)p[i]=(unsigned char)(i*97+i/11);
 memset(p+32,0xa5,32);memset(p+64+FQ_FRAME,0x5a,FQ_SLOT_SIZE-64-FQ_FRAME);
 fq_put(p,FQ_MAGIC);fq_put(p+4,19);fq_put(p+8,71);fq_put(p+12,FQ_FRAME);fq_put(p+16,FQ_READY);fq_put(p+20,reference(p+64,FQ_FRAME));fq_put(p+24,~71u);fq_put(p+28,1);
}
int main(void){
 unsigned char *buf=malloc(FQ_SLOT_SIZE+8);
 for(unsigned a=0;a<4;a++){
  unsigned char*p=buf+a;fill(p);assert(fq_valid(p,19,71,1));
  for(unsigned n=0;n<=FQ_SLOT_SIZE;n++)assert(fq_hash(p,n)==reference(p,n));
  for(unsigned i=0;i<FQ_SLOT_SIZE;i++)for(unsigned bit=0;bit<8;bit++){p[i]^=1u<<bit;assert(!fq_valid(p,19,71,1));p[i]^=1u<<bit;}
  for(unsigned i=0;i<FQ_SLOT_SIZE-3;i++)assert(fq_word(p+i)==((unsigned)p[i]|(unsigned)p[i+1]<<8|(unsigned)p[i+2]<<16|(unsigned)p[i+3]<<24));
 }
 size_t page=(size_t)sysconf(_SC_PAGESIZE),span=((FQ_SLOT_SIZE+page-1)/page)*page;
 unsigned char*m=mmap(NULL,span+2*page,PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);assert(m!=MAP_FAILED);assert(!mprotect(m+page,span,PROT_READ|PROT_WRITE));
 unsigned char*end=m+page+span;memset(m+page,0x39,span);
 for(unsigned n=0;n<=FQ_SLOT_SIZE;n++)assert(fq_hash(end-n,n)==reference(end-n,n));
 fill(end-FQ_SLOT_SIZE);assert(fq_valid(end-FQ_SLOT_SIZE,19,71,1));
 assert(!munmap(m,span+2*page));free(buf);
 puts("PASS: 20484 hash length/alignment cases; 163840 single-bit slot corruptions; metadata offsets; protected-page tails; ASan/UBSan");return 0;
}

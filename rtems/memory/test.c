#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/mman.h>
#include "check.h"
extern void *word_memcpy(void*,const void*,size_t);
extern void *word_memset(void*,int,size_t);
int main(void){
 unsigned int b,k;size_t n,i;long page=sysconf(_SC_PAGESIZE);
 unsigned char *a=mmap(0,page*3,PROT_NONE,MAP_PRIVATE|MAP_ANON,-1,0);
 unsigned char *c=mmap(0,page*3,PROT_NONE,MAP_PRIVATE|MAP_ANON,-1,0);
 assert(a!=MAP_FAILED&&c!=MAP_FAILED);
 assert(!mprotect(a+page,page,PROT_READ|PROT_WRITE));
 assert(!mprotect(c+page,page,PROT_READ|PROT_WRITE));
 for(b=0;b<MEMORY_BATCHES;b++)assert(memory_check_batch(b)==0);
 for(n=0;n<=512;n++){
  unsigned char *s=a+2*page-n,*d=c+2*page-n;
  for(i=0;i<n;i++)s[i]=(unsigned char)i;
  assert(word_memcpy(d,s,n)==d);
  for(i=0;i<n;i++)assert(d[i]==(unsigned char)i);
  assert(word_memset(d,0x123,n)==d);
  for(i=0;i<n;i++)assert(d[i]==0x23);
  for(k=0;k<8;k++){
   unsigned char *middle=c+page+32+k;
   assert(word_memcpy(middle,s,n)==middle);
   for(i=0;i<n;i++)assert(middle[i]==(unsigned char)i);
   for(i=0;i<n;i++)a[page+32+k+i]=(unsigned char)(i*13);
   assert(word_memcpy(d,a+page+32+k,n)==d);
   for(i=0;i<n;i++)assert(d[i]==(unsigned char)(i*13));
  }
  /* Beginning-of-page accesses catch reads/writes before the object. */
  assert(word_memcpy(c+page,a+page,n)==c+page);
  assert(word_memset(c+page,0,n)==c+page);
 }
 munmap(a,page*3);munmap(c,page*3);
 printf("PASS: %u batches, 2112 copies + 2112 moves + 1056 clears; 513 guard-page lengths\n",MEMORY_BATCHES);
 return 0;
}

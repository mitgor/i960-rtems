#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
typedef uint64_t u64;typedef uint8_t u8;
#include "count.h"
static unsigned int slow(const u8*p,size_t n,u8 v){unsigned int r=0;while(n--)if(*p++!=v)r++;return r;}
int main(void){u8 b[280];unsigned int v,n,o,k;long page=sysconf(_SC_PAGESIZE);u8*p=mmap(0,page*3,PROT_NONE,MAP_PRIVATE|MAP_ANON,-1,0);assert(p!=MAP_FAILED);assert(!mprotect(p+page,page,PROT_READ|PROT_WRITE));
 for(v=0;v<256;v++)for(o=0;o<8;o++)for(n=0;n<=257;n++){
  for(k=0;k<sizeof(b);k++)b[k]=(k%3)?v:(u8)(k*17+n);
  assert(changed(b+o,n,v)==slow(b+o,n,v));
 }
 /* Exhaust adjacent byte values: catches incorrect zero-detection borrow masks. */
 for(n=0;n<65536;n++){
  memset(b,0xa5,sizeof(b));b[0]=(u8)n;b[1]=(u8)(n>>8);
  assert(changed(b,8,0xa5)==slow(b,8,0xa5));
 }
 for(n=0;n<=257;n++){
  memset(p+2*page-n,0xa5,n);
  assert(changed(p+2*page-n,n,0xa5)==0);
  assert(changed(p+2*page-n,n,0x5a)==n);
  assert(changed(p+page,n,0)==slow(p+page,n,0));
 }
 munmap(p,page*3);
 puts("PASS: exact byte counts, 528384 pattern/offset/length cases, 65536 adjacent-byte cases, guard pages");return 0;
}

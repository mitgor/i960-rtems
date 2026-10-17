#include <assert.h>
#include <string.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <stdio.h>
#include "copy.h"
int main(void){unsigned a,b,n,i;unsigned char*s=malloc(65664),*d=malloc(65664),*r=malloc(65664);
 assert(s&&d&&r);for(i=0;i<65664;i++)s[i]=(i*17+13)%251;
 for(a=0;a<8;a++)for(b=0;b<8;b++)for(n=0;n<2049;n+=17){
  memset(d,0xa5,65664);memset(r,0xa5,65664);dma_copy(d+32+a,s+32+b,n);memcpy(r+32+a,s+32+b,n);assert(!memcmp(d,r,65664));
 }
 for(a=0;a<8;a++)for(b=0;b<8;b++){memset(d,0xa5,65664);memset(r,0xa5,65664);dma_copy(d+32+a,s+32+b,65536);memcpy(r+32+a,s+32+b,65536);assert(!memcmp(d,r,65664));}
 {unsigned char*x=mmap(0,8192,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0),*y=mmap(0,8192,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
  assert(x!=MAP_FAILED&&y!=MAP_FAILED);memset(x,0x37,4096);assert(!mprotect(x+4096,4096,PROT_NONE)&&!mprotect(y+4096,4096,PROT_NONE));
  for(n=1;n<=4096;n++){dma_copy(y+4096-n,x+4096-n,n);assert(!memcmp(y+4096-n,x+4096-n,n));}
  munmap(x,8192);munmap(y,8192);
 }
 dma_copy(0,0,0);free(s);free(d);free(r);puts("copy alignments, full 64 KiB payloads, protected exact tails and zero length passed");
}

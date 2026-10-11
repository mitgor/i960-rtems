#include <stddef.h>
#include "check.h"
extern void *memcpy(void*,const void*,size_t);
extern void *memset(void*,int,size_t);
extern void *memmove(void*,const void*,size_t);
static const unsigned int lengths[MEMORY_LENGTHS]={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,31,32,33,63,64,65,127,128,129,255,256,257,4095,4096,4097};
static unsigned char src[4160] __attribute__((aligned(16)));
static unsigned char dst[4160] __attribute__((aligned(16)));
static unsigned char ref[4160] __attribute__((aligned(16)));
static void fill(unsigned int seed){unsigned int i;for(i=0;i<4160;i++){src[i]=(unsigned char)(i*29+seed);dst[i]=(unsigned char)(i*7+seed);ref[i]=dst[i];}}
static unsigned int equal(void){unsigned int i;for(i=0;i<4160;i++)if(dst[i]!=ref[i])return 0;return 1;}
unsigned int memory_check_batch(unsigned int batch){
 unsigned int n,s,d,i,v;unsigned char *to;const unsigned char *from;
 static const int values[4]={0,0xff,0x123,-2};
 if(batch>=MEMORY_BATCHES)return 0;
 n=lengths[batch/8];s=batch%8;
 for(d=0;d<8;d++){
  fill(batch+d);to=dst+16+d;from=src+16+s;
  for(i=0;i<n;i++)ref[16+d+i]=src[16+s+i];
  if(memcpy(to,from,n)!=to||!equal())return 1;
  for(i=0;i<4160;i++)if(src[i]!=(unsigned char)(i*29+batch+d))return 2;
  /* Forward/backward overlap, equal pointers, and distances 1..7; memmove
   * remains the original directional implementation (forward calls memcpy). */
  fill(batch+d);to=dst+16+d;from=dst+16+s;
  for(i=0;i<n;i++)ref[16+d+i]=(unsigned char)((16+s+i)*7+batch+d);
  if(memmove(to,from,n)!=to||!equal())return 3;
  /* Each clear offset/value is tested once per length, not eight times. */
  if(s==0)for(v=0;v<4;v++){
   fill(batch+d);for(i=0;i<n;i++)ref[16+d+i]=(unsigned char)values[v];
   if(memset(dst+16+d,values[v],n)!=dst+16+d||!equal())return 4;
  }
 }
 return 0;
}

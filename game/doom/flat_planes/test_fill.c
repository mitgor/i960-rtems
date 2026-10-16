#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "fill.h"
int main(void){unsigned char actual[336],expected[336];unsigned n,offset,color,cases=0;
 for(offset=0;offset<8;offset++)for(n=0;n<=320;n++)for(color=0;color<256;color+=17){
  memset(actual,0xa5,sizeof actual);memcpy(expected,actual,sizeof actual);
  memset(expected+offset,color,n);doom_flat_fill(actual+offset,n,(unsigned char)color);
  assert(!memcmp(actual,expected,sizeof actual));cases++;
 }
 printf("PASS %u bounded flat spans, unaligned heads, word bodies, tails and guards\n",cases);return 0;
}

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "span.h"
static uint32_t state=173;
static unsigned rnd(void){state^=state<<13;state^=state>>17;state^=state<<5;return state;}
int main(void){
 unsigned char source[4096],map[256],dst[672],ref[672];unsigned i,n,off,low,k;
 for(i=0;i<4096;i++)source[i]=rnd();for(i=0;i<256;i++)map[i]=rnd();
 for(low=0;low<2;low++)for(n=0;n<=320;n++)for(off=0;off<8;off++)for(k=0;k<16;k++){
  unsigned pos=rnd(),step=rnd(),p=pos,j;
  memset(dst,0x5a,sizeof dst);memset(ref,0x5a,sizeof ref);
  for(j=0;j<n;j++){unsigned char v=map[source[(p>>26)|((p>>4)&4032u)]];ref[off+j*(low+1)]=v;if(low)ref[off+j*2+1]=v;p+=step;}
  doom_span(dst+off,source,map,pos,step,n,low);assert(!memcmp(dst,ref,sizeof dst));
 }
 puts("PASS 82,176 high/low spans, all destination alignments, zero/odd/even lengths, wrap and sentinels");return 0;
}

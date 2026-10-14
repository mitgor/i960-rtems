#include "column.h"
/* Unsigned accumulation deliberately retains the i960's 32-bit wrap. Dispatch
 * wrapping/clamping and single/double stores once, outside the pixel loop. */
#define LOOP(POST, DOUBLE) do { \
 while(n--) { \
  int index=(int)frac >> 16; unsigned char pixel; \
  if(POST) { if(index<0)index=0; else if(index>=length)index=length-1; } \
  else index &=127; \
  pixel=map[source[index]]; *dst=pixel; \
  if(DOUBLE){*dst2=pixel;dst2+=320;} \
  dst+=320;frac+=step; \
 } \
} while(0)
void doom_column_c(const struct doom_column_job *j) {
 unsigned char *dst=j->dst,*dst2=j->dst2;
 const unsigned char *source=j->source,*map=j->map;
 unsigned frac=j->frac,step=j->step,n=j->count;int length=j->post_length;
 if(length>0){if(dst2)LOOP(1,1);else LOOP(1,0);}
 else {if(dst2)LOOP(0,1);else LOOP(0,0);}
}
#ifndef __i960__
/* Native sanitizer builds exercise C; real assembly is tested on the card. */
void doom_column_asm(const struct doom_column_job*j){doom_column_c(j);}
#endif
unsigned doom_column_mode,doom_column_cases;
void doom_column_begin(unsigned generation){
 static const unsigned char modes[64]={0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0};
 doom_column_mode=modes[generation&63];
}

#include <stdlib.h>
#include <stddef.h>
#include "column.h"
#include "vectors.h"
extern void doom_platform_safe(void);
/* Assembly consumes this exact 32-bit private Doom ABI. */
typedef char job_size[(sizeof(struct doom_column_job)==32)?1:-1];
typedef char job_frac[(offsetof(struct doom_column_job,frac)==16)?1:-1];
typedef char job_post[(offsetof(struct doom_column_job,post_length)==28)?1:-1];
int doom_column_selftest(void){
 unsigned i,k,mode,h;unsigned char source[256],map[256];
 unsigned char *b=malloc(64032);struct doom_column_job j;
 if(!b)return 0;
 for(i=0;i<256;i++){source[i]=(unsigned char)(i*73+19);map[i]=(unsigned char)(i*29+11);}
 j.source=source;j.map=map;doom_column_cases=0;
 for(k=0;k<sizeof(vectors)/sizeof(vectors[0]);k++){
  for(mode=1;mode<=2;mode++){
   doom_platform_safe();
   for(i=0;i<64032;i++)b[i]=0xa5;
   j.dst=b+16;j.dst2=vectors[k].dual?b+23:0;j.frac=vectors[k].frac;
   j.step=vectors[k].step;j.count=vectors[k].count;j.post_length=vectors[k].length;
   if(mode==1)doom_column_c(&j);else doom_column_asm(&j);
   h=2166136261u;for(i=0;i<64032;i++)h=(h^b[i])*16777619u;
   if(h!=vectors[k].hash){free(b);return 0;}
   doom_column_cases++;
  }
 }
 free(b);return doom_column_cases==96;
}

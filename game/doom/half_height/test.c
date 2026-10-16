#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
typedef unsigned char byte;typedef int fixed_t;
#define SCREENWIDTH 320
#define SCREENHEIGHT 200
static byte arena[64000+64],expected[sizeof arena],source[128],map[256],translation[256];
byte *ylookup[200],*dc_source=source,*dc_colormap=map,*dc_translation=translation;
int columnofs[320],dc_postlength,dc_yl,dc_yh,dc_x,dc_iscale,dc_texturemid,detailshift;
int viewheight=168,viewwidth=320,scaledviewwidth=320,centery=84;
void I_Error(const char*s){fprintf(stderr,"%s\n",s);abort();}
#include "half_height.h"
int main(void){
 unsigned cases=0;int lo,hi,d,post,tr,y,i;
 for(i=0;i<128;i++)source[i]=(i*29)&255;
 for(i=0;i<256;i++){map[i]=(i*73)&255;translation[i]=255-i;}
 for(i=0;i<320;i++)columnofs[i]=i;
 for(i=0;i<200;i++)ylookup[i]=arena+32+i*320;
 for(d=0;d<2;d++)for(post=0;post<2;post++)for(tr=0;tr<2;tr++){
  if(tr&&!post)continue;detailshift=d;viewwidth=320>>d;dc_postlength=post?17:0;
  dc_iscale=49152;dc_texturemid=82*65536;
  for(lo=0;lo<168;lo++)for(hi=lo;hi<168;hi+=7){
   dc_yl=lo;dc_yh=hi;dc_x=(lo*13)%viewwidth;
   memset(arena,0xa5,sizeof arena);memcpy(expected,arena,sizeof arena);
   for(y=lo;y<=hi;y++)if(!(y&1)){
    unsigned frac=(unsigned)dc_texturemid+(unsigned)(y-centery)*(unsigned)dc_iscale;
    int idx=(int)frac>>16;if(post){if(idx<0)idx=0;if(idx>=17)idx=16;}else idx&=127;
    byte p=source[idx];if(tr)p=translation[p];p=map[p];
    expected[32+y*320+(dc_x<<d)]=p;if(d)expected[33+y*320+(dc_x<<d)]=p;
   }
   if(tr)R_HalfTranslated();else R_HalfColumn();assert(!memcmp(arena,expected,sizeof arena));cases++;
  }
 }
 for(viewheight=1;viewheight<=200;viewheight++)for(scaledviewwidth=32;scaledviewwidth<=320;scaledviewwidth+=32){
  for(i=0;i<sizeof arena;i++)arena[i]=(i*31+i/320)&255;
  memcpy(expected,arena,sizeof arena);
  for(y=0;y+1<viewheight;y+=2)memcpy(expected+32+(y+1)*320,expected+32+y*320,scaledviewwidth);
  R_HalfExpand();assert(!memcmp(arena,expected,sizeof arena));cases++;
 }
 printf("PASS %u guarded alternate-row column and expansion cases\n",cases);
}

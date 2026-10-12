#include "wad.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
#include <limits.h>
static struct doom_wad w;
static unsigned p[136];
static unsigned crc(unsigned char*s,unsigned n){unsigned c=~0u,i;while(n--){c^=*s++;for(i=0;i<8;i++)c=(c>>1)^(0xedb88320u&(0u-(c&1)));}return ~c;}
static void setup(unsigned n){unsigned i;memset(p,0,sizeof p);assert(doom_wad_begin(&w,1,0,n,1024));p[0]=WAD_MAGIC;p[1]=w.sequence;p[2]=1;p[4]=n;for(i=0;i<n;i++)((unsigned char*)(p+8))[i]=(unsigned char)i;p[6]=crc((unsigned char*)(p+8),n);}
static unsigned send(unsigned words){unsigned i;assert(!doom_wad_control(&w,0x77,0,words*4,1));for(i=0;i<words;i++)assert(!doom_wad_control(&w,0x78,i,p[i],1));return doom_wad_control(&w,0x79,0,0,1);}
int main(void){unsigned i;unsigned char d[512],before[512];memset(d,0x95,sizeof d);memcpy(before,d,sizeof d);
 assert(!doom_wad_begin(&w,2,0,1,1024)&&!doom_wad_begin(&w,1,1025,1,1024)&&!doom_wad_begin(&w,1,0,513,1024));
 setup(512);assert(!doom_wad_begin(&w,1,0,1,1024));assert(doom_wad_control(&w,0x77,0,548,1)==~0u);assert(doom_wad_control(&w,0x77,0,32,0)==0xfffffffeu);assert(!send(136));assert(doom_wad_copy(&w,d,512)<0);assert(!memcmp(d,before,512));assert(doom_wad_claim(&w));assert(!doom_wad_claim(&w));assert(doom_wad_copy(&w,d,512)==512);for(i=0;i<512;i++)assert(d[i]==(unsigned char)i);doom_wad_cancel(&w);
 for(i=0;i<8;i++){setup(12);p[i]^=1; if(i==5||i==6){assert(!send(11));assert(doom_wad_claim(&w));memcpy(d,before,512);assert(doom_wad_copy(&w,d,512)<0);assert(!memcmp(d,before,512));}else assert(send(11)==~0u);doom_wad_cancel(&w);}
 setup(13);((unsigned char*)(p+8))[13]=1;assert(!send(12)&&doom_wad_claim(&w));assert(doom_wad_copy(&w,d,512)==-2);doom_wad_cancel(&w);
 setup(12);assert(!doom_wad_control(&w,0x75,0,0,1));assert(doom_wad_control(&w,0x76,1,0,1)==w.sequence);assert(doom_wad_control(&w,0x76,8,0,1)==~0u);
 assert(!doom_wad_control(&w,0x77,0,44,1));assert(doom_wad_control(&w,0x78,1,p[0],1)==~0u);assert(doom_wad_control(&w,0x79,0,0,1)==~0u);doom_wad_cancel(&w);
 assert(doom_wad_begin(&w,1,0,12,1024));assert(send(11)==~0u);doom_wad_cancel(&w);w.sequence=UINT_MAX;assert(!doom_wad_begin(&w,1,0,1,1024));
 puts("PASS WAD mailbox: bounds, order, immutable staging, header mutations, CRC, padding, stale generation, sequence exhaustion, cancellation");
}

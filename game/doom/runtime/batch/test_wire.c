#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "wire.h"
static unsigned staging[8][136];
static struct doom_batch w={.inbox=staging};
static unsigned p[136],out[1024];
static unsigned crc(const unsigned char*p,unsigned n){unsigned c=~0u,i;while(n--){c^=*p++;for(i=0;i<8;i++)c=(c>>1)^(0xedb88320u&(0u-(c&1)));}return ~c;}
static void packet(unsigned off,unsigned n){memset(p,0,sizeof p);p[0]=DOOM_BATCH_MAGIC;p[1]=w.sequence;p[2]=1;p[3]=off;p[4]=n;p[6]=crc((unsigned char*)(p+8),n);p[7]=w.wanted;}
static unsigned send(unsigned words){unsigned i;assert(!doom_batch_control(&w,0x77,0,words*4,1));for(i=0;i<words;i++)assert(!doom_batch_control(&w,0x78,i,p[i],1));return doom_batch_control(&w,0x79,0,0,1);}
int main(void){unsigned field,i,seq;
 for(field=0;field<8;field++){
  assert(doom_batch_begin(&w,100,1024,10000));packet(100,512);
  if(field==5||field==6){doom_batch_cancel(&w);continue;}
  p[field]^=1;assert(send(136)==~0u&&w.state==WAD_REQUEST&&w.fragments==0);doom_batch_cancel(&w);
 }
 assert(!doom_batch_begin(&w,0,0,10000)&&!doom_batch_begin(&w,0,4097,10000)&&!doom_batch_begin(&w,10000,1,10000));
 assert(doom_batch_begin(&w,0,1024,10000));seq=w.sequence;assert(!doom_batch_begin(&w,0,512,10000));packet(0,512);
 assert(doom_batch_control(&w,0x77,0,548,1)==~0u);assert(doom_batch_control(&w,0x77,0,544,0)==0xfffffffeu);
 assert(!doom_batch_control(&w,0x77,0,544,1));assert(doom_batch_control(&w,0x77,0,544,1)==~0u);assert(doom_batch_control(&w,0x78,1,0,1)==~0u);assert(doom_batch_control(&w,0x79,0,0,1)==~0u);
 for(i=0;i<136;i++)assert(!doom_batch_control(&w,0x78,i,p[i],1));assert(!doom_batch_control(&w,0x79,0,0,1));
 assert(send(136)==~0u); /* duplicated first fragment cannot advance */
 packet(512,512);assert(!send(136)&&doom_batch_claim(&w));memset(out,0xa5,sizeof out);
 assert(doom_batch_copy(&w,out,1023)==-2);for(i=0;i<1024;i++)assert(out[i]==0xa5a5a5a5);
 doom_batch_cancel(&w);assert(doom_batch_begin(&w,0,512,10000));packet(0,512);p[1]=seq;assert(send(136)==~0u);doom_batch_cancel(&w);
 assert(doom_batch_begin(&w,100,512,137));packet(100,37);((unsigned char*)(p+8))[37]=1;assert(!send(18)&&doom_batch_claim(&w));assert(doom_batch_copy(&w,out,sizeof out)==-2);doom_batch_cancel(&w);
 w.sequence=~0u;assert(!doom_batch_begin(&w,0,1,10000));
 puts("PASS batch wire: magic/sequence/file/offset/length/total, missing/reordered/duplicate words/fragments, running gate, bounds, undersized destination, EOF padding, stale sequence and wrap refusal");
}

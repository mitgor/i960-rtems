#include "wire.h"
static unsigned batch_crc(const unsigned char*p,unsigned n){unsigned c=~0u,i;while(n--){c^=*p++;for(i=0;i<8;i++)c=(c>>1)^(0xedb88320u&(0u-(c&1)));}return ~c;}
int doom_batch_begin(struct doom_batch*w,unsigned offset,unsigned n,unsigned bytes){
 if(!w->inbox||w->state||w->sequence==~0u||!n||n>DOOM_BATCH_BYTES||offset>=bytes)return 0;
 w->sequence++;w->offset=offset;w->wanted=n;w->file_bytes=bytes;w->fragments=w->words=w->expected=0;w->state=WAD_REQUEST;return 1;
}
unsigned doom_batch_control(struct doom_batch*w,unsigned op,unsigned index,unsigned value,unsigned running){unsigned *p,n,total;
 if(op==0x75){if(index)return ~0u;w->frozen[0]=DOOM_BATCH_MAGIC;w->frozen[1]=w->sequence;w->frozen[2]=w->state;w->frozen[3]=1;w->frozen[4]=w->offset;w->frozen[5]=w->wanted;w->frozen[6]=w->file_bytes;w->frozen[7]=w->rejected;return 0;}
 if(op==0x76)return index<8?w->frozen[index]:~0u;
 if(!running||w->state!=WAD_REQUEST||w->fragments>=8)return 0xfffffffeu;
 if(op==0x77){if(index||value<32||value>544||(value&3)||w->expected)return ~0u;w->expected=value/4;w->words=0;return 0;}
 p=w->inbox[w->fragments];
 if(op==0x78){if(!w->expected||index!=w->words||index>=w->expected)return ~0u;p[w->words++]=value;return 0;}
 if(op!=0x79||index||value||!w->expected||w->words!=w->expected)return ~0u;
 n=p[4];total=w->wanted;if(total>w->file_bytes-w->offset)total=w->file_bytes-w->offset;
 if(p[0]!=DOOM_BATCH_MAGIC||p[1]!=w->sequence||p[2]!=1||p[3]!=w->offset+512*w->fragments||n>512||p[7]!=w->wanted||w->expected!=8+(n+3)/4){w->rejected++;w->expected=w->words=0;return ~0u;}
 w->fragments++;w->expected=w->words=0;
 if(w->fragments==(total+511)/512||p[5])w->state=WAD_READY;
 return 0;
}
int doom_batch_claim(struct doom_batch*w){if(w->state!=WAD_READY)return 0;w->state=WAD_CONSUMING;return 1;}
int doom_batch_copy(struct doom_batch*w,void*dst,unsigned capacity){unsigned i,j,total,need,*p;unsigned char*b,*d=dst;
 if(w->state!=WAD_CONSUMING||!dst)return -1;
 total=w->wanted;if(total>w->file_bytes-w->offset)total=w->file_bytes-w->offset;
 if(total>capacity)goto bad;
 /* Validate the ENTIRE batch before publishing any destination bytes. */
 for(i=0;i<w->fragments;i++){
  p=w->inbox[i];b=(unsigned char*)(p+8);need=total-512*i;if(need>512)need=512;
  if(p[5]){if(p[5]!=1||p[4]||p[6])goto bad;return -3;}
  if(p[4]!=need||batch_crc(b,need)!=p[6])goto bad;
  for(j=need;j<((need+3)&~3u);j++)if(b[j])goto bad;
 }
 if(w->fragments!=(total+511)/512)goto bad;
 for(i=0;i<w->fragments;i++){p=w->inbox[i];b=(unsigned char*)(p+8);for(j=0;j<p[4];j++)*d++=b[j];}
 w->accepted++;return total;
 bad:w->rejected++;return -2;
}
void doom_batch_cancel(struct doom_batch*w){if(w->state==WAD_REQUEST||w->state==WAD_READY)w->cancelled++;w->state=WAD_IDLE;w->expected=w->words=w->fragments=0;}

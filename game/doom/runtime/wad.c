#include "wad.h"
static unsigned int crc32(const unsigned char*p,unsigned int n){unsigned int c=~0u,i;while(n--){c^=*p++;for(i=0;i<8;i++)c=(c>>1)^(0xedb88320u&(0u-(c&1)));}return ~c;}
int doom_wad_begin(struct doom_wad*w,unsigned int file,unsigned int offset,unsigned int n,unsigned int bytes){
 if(w->state||w->sequence==~0u||file!=1||!n||n>512||offset>bytes)return 0;
 w->sequence++;w->file=file;w->offset=offset;w->wanted=n;w->file_bytes=bytes;w->words=w->expected=0;w->state=WAD_REQUEST;return 1;
}
unsigned int doom_wad_control(struct doom_wad*w,unsigned int op,unsigned int index,unsigned int value,unsigned int running){unsigned int i;
 if(op==0x75){if(index)return ~0u;w->frozen[0]=WAD_MAGIC;w->frozen[1]=w->sequence;w->frozen[2]=w->state;w->frozen[3]=w->file;w->frozen[4]=w->offset;w->frozen[5]=w->wanted;w->frozen[6]=w->file_bytes;w->frozen[7]=w->rejected;return 0;}
 if(op==0x76)return index<8?w->frozen[index]:~0u;
 if(!running||w->state!=WAD_REQUEST)return 0xfffffffeu;
 if(op==0x77){if(index||value<32||value>544||(value&3))return ~0u;w->expected=value/4;w->words=0;return 0;}
 if(op==0x78){if(!w->expected||index!=w->words||index>=w->expected)return ~0u;w->inbox[w->words++]=value;return 0;}
 if(op==0x79){if(index||!w->expected||w->words!=w->expected)return ~0u;
  /* Only fixed wire bounds here; payload CRC/copy belongs to the task. */
  i=w->inbox[4];if(w->inbox[0]!=WAD_MAGIC||w->inbox[1]!=w->sequence||w->inbox[2]!=w->file||w->inbox[3]!=w->offset||i>512||w->expected!=8+((i+3)/4)||w->inbox[7]){w->rejected++;w->expected=w->words=0;return ~0u;}
  w->state=WAD_READY;return 0;
 }
 return ~0u;
}
int doom_wad_claim(struct doom_wad*w){if(w->state!=WAD_READY)return 0;w->state=WAD_CONSUMING;return 1;}
int doom_wad_copy(struct doom_wad*w,void*dst,unsigned int capacity){unsigned int i,n=w->inbox[4],want=w->wanted;unsigned char*p=(unsigned char*)(w->inbox+8),*d=dst;
 if(w->state!=WAD_CONSUMING||!d)return -1;
 if(w->inbox[5]){if(n||w->inbox[6]||w->inbox[5]!=1){w->rejected++;return -2;}return -3;}
 if(want>w->file_bytes-w->offset)want=w->file_bytes-w->offset;
 if(n!=want||n>capacity||crc32(p,n)!=w->inbox[6]){w->rejected++;return -2;}
 for(i=n;i<((n+3)&~3u);i++)if(p[i]){w->rejected++;return -2;}
 for(i=0;i<n;i++)d[i]=p[i];w->accepted++;return n;
}
void doom_wad_cancel(struct doom_wad*w){if(w->state==WAD_REQUEST||w->state==WAD_READY)w->cancelled++;w->state=WAD_IDLE;w->words=w->expected=0;}

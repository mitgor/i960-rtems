#include <assert.h>
#include <stdio.h>
#include <string.h>
static unsigned mode,conf,hccr,nread,nwrite,bank_reads,forbidden;
static unsigned rd(unsigned a);
static void wr(unsigned a,unsigned v);
#define QP_READ16(a) rd(a)
#define QP_WRITE16(a,v) wr(a,v)
#define QP_TICKS() 42u
#include "qlogic_dma_bank.h"
#define QP_PAUSED(r) at_qlogic_dma_bank(r)
#include "qlogic_pause.h"
static unsigned rd(unsigned a){
 static const unsigned offsets[]={0x80,0x84,0x86,0xc0,0xc4,0xc6};
 nread++;
 if(a==0x8bf00006){if(mode==1&&nwrite==2)return conf^0x100;if(mode==2&&nwrite==3)return conf|0x300;return conf;}
 if(a==0x8bf00008)return 6;
 if(conf&0x300){assert((conf&0x300)==0x300&&hccr==0x20);assert(bank_reads<12&&a==0x8bf00000+offsets[bank_reads%6]);return ++bank_reads;}
 if(a==0x8bf000c0){if(mode==3&&nwrite==3)return 0;return hccr;}
 if(a==0x8bf0000a)return 0;
 if(a==0x8bf0000c)return 2;
 if(a==0x8bf00078)return 37;
 if(a==0x8bf0007a)return 22;
 forbidden++;assert(0);return 0;
}
static void wr(unsigned a,unsigned v){
 nwrite++;
 if(nwrite==1){assert(a==0x8bf000c0&&v==0x2000);hccr=mode==4?0:0x20;return;}
 if(nwrite==2){assert(a==0x8bf00006&&v==(conf|0x300)&&hccr==0x20);conf=v;return;}
 if(nwrite==3){assert(a==0x8bf00006&&(v&0x300)==0);conf=v;return;}
 assert(nwrite==4&&a==0x8bf000c0&&v==0x3000&&(conf&0x300)==0);hccr=0;
}
static void init(unsigned *r,unsigned saved){unsigned i;
 memset(r,0,4096);conf=saved;hccr=nread=nwrite=bank_reads=forbidden=0;at_qp_attempted=0;
 r[328]=5;r[330]=0x10161077;r[331]=6;r[334]=0xfff00000;
 r[359]=14;r[358]=0xc0600d00;r[360]=0x8bf00000;
 r[363]=0xc0600df0;r[364]=256;r[365]=0xc0604df0;r[366]=128;
 r[369]=37;r[370]=0x00160016;r[390]=12;
 for(i=392;i<=398;i+=6){r[i+1]=2;r[i+2]=37;r[i+3]=22;r[i+5]=2;}
 r[415]=r[512]=0xa5a5a5a5;
}
int main(void){unsigned r[1024],i,n,payload[48];
 for(i=0;i<2;i++){
  mode=0;init(r,i?0x74:0);at_qlogic_pause(r,23,1,0);
  assert(!r[421]&&!r[468]&&nwrite==4&&bank_reads==12&&conf==(i?0x74:0)&&!hccr&&!forbidden);
  assert(r[415]==0xa5a5a5a5&&r[512]==0xa5a5a5a5);
  memcpy(payload,r+464,sizeof(payload));n=nread;at_qlogic_pause(r,23,3,1);
  assert(nread==n&&nwrite==4&&!memcmp(payload,r+464,sizeof(payload)));
 }
 for(mode=1;mode<=4;mode++){
  init(r,0x74);at_qlogic_pause(r,23,1,0);assert(r[421]);
  if(mode==1)assert(nwrite==3&&bank_reads==0&&r[468]==4);
  if(mode==2)assert(nwrite==3&&r[468]==2);
  if(mode==3)assert(nwrite==3&&r[468]==3);
  if(mode==4)assert(nwrite==1&&bank_reads==0&&r[428]==QP_POLLS);
  n=nread;at_qlogic_pause(r,23,2,0);assert(nread==n);
 }
 puts("DMA bank: full pause/select/read/restore/release order; zero saved CONF1; mismatched selection/restoration/pause; no bank reads before pause; failure latch passed");return 0;
}

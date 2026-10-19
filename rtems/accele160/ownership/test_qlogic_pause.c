#include <assert.h>
#include <stdio.h>
#include <string.h>
static unsigned reads,writes,mode,polls,pre,post;
static unsigned rd(unsigned a);
static void wr(unsigned a,unsigned v);
#define QP_READ16(a) rd(a)
#define QP_WRITE16(a,v) wr(a,v)
#define QP_TICKS() 42u
#include "qlogic_pause.h"
static unsigned rd(unsigned a){
 static const unsigned before[]={0x06,0x08,0xc0};
 static const unsigned after[]={0x06,0x08,0xc0,0x0a,0x0c,0x78,0x7a};
 static const unsigned values[]={0x44,6,0,0,2,37,22};
 reads++;
 if(!writes){assert(pre<3&&a==0x8bf00000+before[pre]);pre++;
  if(pre==1)return mode==1?0x344:0x44;
  if(pre==2)return mode==2?1:6;
  return mode==3?0x20:0;
 }
 if(writes==1){assert(a==0x8bf000c0);polls++;
  if(mode==4)return 0;
  if(mode==6)return 0x60;
  return polls>=3?0x20:0;
 }
 if(mode==5||polls<3){assert(a==0x8bf000c0);polls++;return (mode==5||polls<3)?0x20:0;}
 assert(post<7&&a==0x8bf00000+after[post]);
 if(mode==7&&post==4){post++;return 3;}
 if(mode==8&&post==0){post++;return 0x344;}
 return values[post++];
}
static void wr(unsigned a,unsigned v){assert(a==0x8bf000c0);assert(writes<2);
 assert(v==(writes?0x3000:0x2000));writes++;polls=0;}
static void init(unsigned *r){unsigned i;
 memset(r,0,1024*sizeof(*r));reads=writes=polls=pre=post=0;at_qp_attempted=0;
 r[328]=5;r[330]=0x10161077;r[331]=6;r[334]=0xfff00000;
 r[359]=14;r[358]=0xc0600d00;r[360]=0x8bf00000;
 r[363]=0xc0600df0;r[364]=256;r[365]=0xc0604df0;r[366]=128;
 r[369]=37;r[370]=0x00160016;r[390]=12;
 for(i=392;i<=398;i+=6){r[i+1]=2;r[i+2]=37;r[i+3]=22;r[i+5]=2;}
 r[415]=r[464]=0xa5a5a5a5;
}
int main(void){unsigned r[1024],i,n,before[48];
 unsigned fields[]={325,328,330,331,334,357,359,358,360,361,362,363,364,365,366,371,389,390,392,393,394,395,396,397,398,399,400,401,402,403,369,370};
 mode=0;init(r);at_qlogic_pause(r,23,1,0);
 assert(r[421]==0&&writes==2&&r[428]==3&&r[430]==3&&post==7);
 assert(r[415]==0xa5a5a5a5&&r[464]==0xa5a5a5a5);
 memcpy(before,r+416,sizeof(before));n=reads;
 at_qlogic_pause(r,23,2,0);at_qlogic_pause(r,23,3,1);
 assert(reads==n&&writes==2&&r[419]==3&&r[420]==1);
 assert(!memcmp(before+5,r+421,43*sizeof(unsigned)));
 for(i=0;i<sizeof(fields)/sizeof(fields[0]);i++){
  init(r);r[fields[i]]^=(fields[i]==331?2:1);at_qlogic_pause(r,23,1,0);
  assert(!writes&&!reads&&r[421]==1);
 }
 for(i=0;i<3;i++){
  init(r);at_qlogic_pause(r,i?23:0,i==1?2:1,i==2?1:0);assert(!reads&&!writes&&r[421]);
 }
 for(mode=1;mode<=8;mode++){
  init(r);at_qlogic_pause(r,23,1,0);
  if(mode<=3)assert(!writes&&r[421]==3);
  if(mode==4)assert(writes==1&&r[421]==4&&r[428]==QP_POLLS);
  if(mode==5)assert(writes==2&&r[421]==5&&r[430]==QP_POLLS);
  if(mode==6)assert(writes==1&&r[421]==6);
  if(mode>=7)assert(writes==2&&r[421]==6);
  n=reads;at_qlogic_pause(r,23,2,0);assert(reads==n); /* Never retry. */
 }
 puts("pause: ordered two-write transaction, 32 gates, initial-state refusals, bounded pause/release timeouts, changed-state retention and retry latch passed");return 0;
}

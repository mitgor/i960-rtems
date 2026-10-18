#include <assert.h>
#include <stdio.h>
#include <string.h>
#define SVC_SYNC() ((void)0)
#include "protocol.h"
int main(void){
 unsigned int w[1024]={0},v[24]={0},i;struct svc_state s={123,0,0,0};
 v[0]=42;w[1]=1;w[2]=123;
 for(i=1;i<=7;i++){
  w[0]=i;w[3]=i;svc_poll(&s,w,v);
  assert(w[16]==i&&w[17]==0&&w[19]>0&&w[19]<=SVC_BYTES&&w[24]==SVC_MAGIC);
  svc_poll(&s,w,v);assert(s.accepted==i);
 }
 w[0]=6;svc_poll(&s,w,v);assert(w[17]==2&&s.seq==7);
 w[0]=8;w[2]=124;svc_poll(&s,w,v);assert(w[17]==1&&s.seq==7);
 w[2]=123;w[0]=99;svc_poll(&s,w,v);assert(w[17]==2&&s.seq==7);
 w[0]=8;w[4]=0xffffffffu;svc_poll(&s,w,v);assert(w[17]==3&&s.seq==8);
 w[0]=9;w[4]=0;w[3]=99;svc_poll(&s,w,v);assert(w[17]==4&&s.seq==9);
 w[0]=10;w[3]=1;w[15]=1;svc_poll(&s,w,v);assert(w[17]==3&&s.seq==10);
 w[0]=11;w[15]=0;w[3]=2;svc_poll(&s,w,v);assert(!w[17]);
 /* Formatter capacity and no write beyond output. */
 {unsigned int n=SVC_BYTES-1;unsigned char out[SVC_BYTES+4];memset(out,0xa5,sizeof(out));svc_text(out,&n,"abcdef");assert(n==SVC_BYTES&&out[SVC_BYTES]==0xa5);}
 puts("protocol: seven commands, duplicate, epoch, sequence, length, opcode, reserved, capacity PASS");return 0;
}

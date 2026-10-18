#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "key_fifo.h"
static unsigned area[KF_WORDS+32],live[16];
static volatile unsigned *w=area+16;
static struct key_fifo_state state;
static void reset(unsigned mode){
 unsigned i;memset(area,0xa5,sizeof area);memset(live,0,sizeof live);
 kf_init(&state,w,1);w[14]=mode;assert(!kf_begin(&state,w,live,1));
 for(i=0;i<16;i++)assert(area[i]==0xa5a5a5a5u&&area[KF_WORDS+16+i]==0xa5a5a5a5u);
}
static unsigned push(unsigned value){
 unsigned seq=w[4]+1,base=16+((seq-1)&15)*4,limit=state.mode?16:1;
 if(w[4]-w[5]>=limit)return 0;
 if(state.mode){w[base]=seq;w[base+1]=state.run;w[base+2]=value;w[base+3]=~seq;}
 else live[11]=value;
 live[10]=seq;w[4]=seq;return seq;
}
static unsigned pop(void){unsigned value,available;
 assert(!kf_pop(&state,w,live,123,456,&value,&available));assert(available);return value;
}
int main(void){unsigned i,j,value,available,before,err;
 reset(1);
 for(j=0;j<5000;j++){
  for(i=0;i<16;i++)assert(push((j+i)&511));
  before=w[4];assert(!push(192)&&w[4]==before);
  for(i=0;i<16;i++)assert(pop()==((j+i)&511));
 }
 assert(state.cursor==80000&&state.maximum==16&&!state.discarded);
 assert(!kf_pop(&state,w,live,0,0,&value,&available)&&!available);
 reset(0);assert(push(429)&&!push(430));assert(pop()==429);
 /* Unpublished entries are invisible, and cannot force an ACK. */
 reset(1);w[16]=1;w[17]=1;w[18]=448;w[19]=~1u;live[10]=1;
 assert(!kf_pop(&state,w,live,0,0,&value,&available)&&!available&&!state.cursor);
 w[4]=1;assert(pop()==448);
 for(i=0;i<16;i++){
  reset(1);push(448);w[80+i]^=1;
  assert(kf_pop(&state,w,live,0,0,&value,&available)==2&&!state.cursor);
 }
 for(i=0;i<4;i++){
  reset(1);push(448);w[16+i]^=i==2?512:1;
  assert(kf_pop(&state,w,live,0,0,&value,&available)&&!state.cursor);
 }
 for(i=0;i<16;i++){
  reset(1);push(448);
  if(i==4)w[4]=17;else w[i]^=1;
  err=kf_pop(&state,w,live,0,0,&value,&available);
  assert(err&&!state.cursor);
 }
 reset(1);push(448);live[10]=0;
 assert(kf_pop(&state,w,live,0,0,&value,&available)&&!state.cursor);
 reset(1);for(i=0;i<16;i++)push(i);pop();pop();
 assert(!kf_pending(&state,w,live));kf_rearm(&state,w,live,2);
 assert(state.cursor==16&&state.discarded==14&&w[5]==16&&w[6]==14&&w[7]==2);
 assert(!kf_pop(&state,w,live,0,0,&value,&available)&&!available);
 /* Retained old-run descriptors never satisfy a new run's next sequence. */
 push(448);w[17]=1;
 assert(kf_pop(&state,w,live,0,0,&value,&available)==7&&state.cursor==16);
 reset(1);w[14]=0;
 assert(kf_pop(&state,w,live,0,0,&value,&available));
 assert(!kf_begin(&state,w,live,1)&&state.mode==0);
 reset(1);state.cursor=w[4]=w[5]=live[10]=live[12]=0xfffffffdu;
 assert(!kf_check(&state,w,live));w[4]=live[10]=0xfffffffeu;
 assert(kf_pop(&state,w,live,0,0,&value,&available)==5);
 puts("PASS actual FIFO: 80000 ordered events/wraps, full refusal, commit ordering, all header/guard/entry mutations, stale runs, explicit STOP discard, mode and sequence bounds");
 return 0;
}

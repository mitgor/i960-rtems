#include "control.h"
ctl_u32 ctl_checksum(const ctl_u32 *w,unsigned int n){
 ctl_u32 h=2166136261u;unsigned int i,j;
 for(i=0;i<n;i++)for(j=0;j<4;j++){h^=(w[i]>>(j*8))&255u;h*=16777619u;}
 return h;
}
int ctl_init(struct ctl_state*s,ctl_u32 epoch){
 if(!epoch)return 0;s->epoch=epoch;s->sequence=0;s->heartbeat=0;s->stopped=0;return 1;
}
void ctl_tick(struct ctl_state*s){if(!s->stopped)s->heartbeat++;}
int ctl_poll(struct ctl_state*s,volatile ctl_u32*req,volatile ctl_u32*resp,const struct ctl_hooks*h){
 ctl_u32 frame[CTL_WORDS],reply[CTL_WORDS],seq,error=CTL_OK,value=0;unsigned int i;
 if(!h||!h->barrier||!h->quiesce)return 0;
 seq=req[0];if(!seq||seq==s->sequence)return 0;
 h->barrier(h->arg);for(i=0;i<CTL_WORDS;i++)frame[i]=req[i];h->barrier(h->arg);
 if(req[0]!=seq||frame[0]!=seq)return 0;
 if(frame[1]!=CTL_MAGIC||frame[2]!=CTL_VERSION||frame[6]!=ctl_checksum(frame,6))error=CTL_BAD_FRAME;
 for(i=7;i<CTL_WORDS;i++)if(frame[i])error=CTL_BAD_FRAME;
 if(!error&&frame[3]!=s->epoch)error=CTL_BAD_EPOCH;
 if(!error&&(s->sequence==0xffffffffu||seq!=s->sequence+1))error=CTL_BAD_SEQUENCE;
 if(!error){
  if(frame[4]>CTL_STOP)error=CTL_BAD_OPERATION;
  else if(s->stopped&&frame[4]!=CTL_STATUS&&frame[4]!=CTL_STOP)error=CTL_STOPPED;
  else if(frame[4]==CTL_PING)value=frame[5];
  else if(frame[4]==CTL_STOP&&!s->stopped){
   if(h->quiesce(h->arg))s->stopped=1;else error=CTL_NOT_QUIESCENT;
  }
  /* Valid epoch/sequence requests are consumed, including failed operations. */
  s->sequence=seq;
 }
 for(i=0;i<CTL_WORDS;i++)reply[i]=0;
 reply[0]=seq;reply[1]=CTL_MAGIC;reply[2]=CTL_VERSION;reply[3]=s->epoch;
 reply[4]=error;reply[5]=value;reply[6]=s->stopped;reply[7]=s->heartbeat;
 reply[8]=ctl_checksum(reply,8);
 resp[0]=0;h->barrier(h->arg);
 for(i=1;i<CTL_WORDS;i++)resp[i]=reply[i];
 h->barrier(h->arg);resp[0]=seq;h->barrier(h->arg);return 1;
}

/* Tick-owned renewable execution lease. Software protocol, not a DMA lease. */
#ifndef EXEC_LEASE_H
#define EXEC_LEASE_H
#define LEASE_TTL 512u
#define LEASE_CAP 24000u
struct execution_lease {unsigned int state,epoch,start,grant,last,seq,seen,reason,stop,maxgap,rejects;};
static void lease_init(struct execution_lease*l,unsigned int epoch,unsigned int tick){
 l->state=1;l->epoch=epoch;l->start=l->last=tick;l->grant=l->seq=l->seen=l->reason=l->stop=l->maxgap=l->rejects=0;
}
/* Returns an acknowledgement word, or zero. Deadline wins over late renewal. */
static unsigned int lease_poll(struct execution_lease*l,unsigned int tick,unsigned int token){unsigned int gap=tick-l->last,n=token&65535,tag=token&0xffff0000u;
 if(l->state==3)return 0;
 if(gap>l->maxgap)l->maxgap=gap;
 if(tick-l->start>=LEASE_CAP||gap>=LEASE_TTL){l->reason=tick-l->start>=LEASE_CAP?3:2;l->state=3;l->stop=tick;return 0;}
 if(token==l->seen)return 0;l->seen=token;
 if(token==(0x61000000u|l->epoch)&&l->state==1){l->state=2;l->grant=l->last=tick;return 0x62000000u|l->epoch;}
 if(tag==0x63000000u&&l->state==2&&n==l->seq+1&&n){l->seq=n;l->last=tick;return 0x64000000u|n;}
 if(token==(0x72000000u|l->epoch)&&l->state==2){l->reason=1;l->state=3;l->stop=tick;return 0;}
 if(token)l->rejects++;return 0;
}
#endif

/* Serialized by the supervisor or the real mutex owner at priority 31.
 * Software leases model references only; they do not describe hardware DMA. */
#ifndef OWN_POLICY_H
#define OWN_POLICY_H
#define OWN_IDLE 0u
#define OWN_HELD 1u
#define OWN_CANCEL 2u
#define OWN_RETIRED 3u
#define OWN_QUARANTINE 4u
#define OWN_OK 0u
#define OWN_STALE 1u
#define OWN_BUSY 2u
#define OWN_STATE 3u
#define OWN_REFUSED 4u
#define OWN_DEFERRED 5u
struct ownership {unsigned int epoch,phase,committed,staged,refs,ticket,next_ticket,acks,rejects,aborts,commits;};
static unsigned int own_reject(struct ownership*p,unsigned int rc){p->rejects++;return rc;}
static unsigned int own_epoch(struct ownership*p,unsigned int e){return e&&e==p->epoch;}
static unsigned int own_begin(struct ownership*p,unsigned int e,unsigned int value){
 if(!own_epoch(p,e))return own_reject(p,OWN_STALE);
 if(p->phase!=OWN_IDLE)return own_reject(p,OWN_STATE);
 p->phase=OWN_HELD;p->staged=value;return 0;
}
static unsigned int own_cancel(struct ownership*p,unsigned int e){
 if(!own_epoch(p,e))return own_reject(p,OWN_STALE);
 if(p->phase!=OWN_HELD&&p->phase!=OWN_CANCEL)return own_reject(p,OWN_STATE);
 p->phase=OWN_CANCEL;return 0;
}
static unsigned int own_lease(struct ownership*p,unsigned int e){
 if(!own_epoch(p,e))return own_reject(p,OWN_STALE);
 if(p->phase!=OWN_HELD||p->refs)return own_reject(p,OWN_BUSY);
 if(p->next_ticket==0xffffffffu)return own_reject(p,OWN_STATE);
 p->ticket=++p->next_ticket;p->refs=1;return 0;
}
static unsigned int own_complete(struct ownership*p,unsigned int e,unsigned int ticket){
 if(!own_epoch(p,e)||!p->refs||ticket!=p->ticket)return own_reject(p,OWN_STALE);
 p->refs=0;return 0;
}
static unsigned int own_finish(struct ownership*p,unsigned int e,unsigned int commit){
 if(!own_epoch(p,e))return own_reject(p,OWN_STALE);
 if(p->phase!=(commit?OWN_HELD:OWN_CANCEL))return own_reject(p,OWN_STATE);
 if(p->refs)return OWN_DEFERRED;
 if(commit){p->committed=p->staged;p->commits++;}else{p->staged=p->committed;p->aborts++;}
 p->phase=OWN_RETIRED;p->acks++;return 0;
}
static unsigned int own_restart(struct ownership*p,unsigned int e){
 if(!own_epoch(p,e))return own_reject(p,OWN_STALE);
 if(p->phase!=OWN_RETIRED||p->refs||p->epoch==0xffffffffu)return own_reject(p,OWN_STATE);
 p->epoch++;p->phase=OWN_IDLE;return 0;
}
static unsigned int own_quarantine(struct ownership*p,unsigned int e){
 if(!own_epoch(p,e))return own_reject(p,OWN_STALE);
 if(p->phase!=OWN_CANCEL)return own_reject(p,OWN_STATE);
 p->phase=OWN_QUARANTINE;return 0;
}
#endif

#include <assert.h>
#include <string.h>
#include "policy.h"
#include "report.h"
int main(void){struct ownership p={1,0,10,10,0,0,0,0,0,0,0};unsigned int i,ticket,old;
 for(i=0;i<1000;i++){
  old=p.epoch;assert(!own_begin(&p,old,99));assert(own_begin(&p,old,88)==OWN_STATE);
  assert(!own_lease(&p,old));ticket=p.ticket;assert(own_lease(&p,old)==OWN_BUSY);
  assert(!own_cancel(&p,old));assert(own_finish(&p,old,0)==OWN_DEFERRED);
  assert(own_complete(&p,old,ticket+1)==OWN_STALE);assert(p.refs&&p.phase==OWN_CANCEL);
  assert(!own_complete(&p,old,ticket));assert(own_complete(&p,old,ticket)==OWN_STALE);
  assert(!own_finish(&p,old,0));assert(p.committed==10&&p.staged==10&&p.acks==i+1);
  assert(!own_restart(&p,old));assert(own_begin(&p,old,1)==OWN_STALE);
 }
 assert(!own_begin(&p,p.epoch,77));assert(!own_cancel(&p,p.epoch));assert(!own_quarantine(&p,p.epoch));
 assert(own_restart(&p,p.epoch)==OWN_STATE);assert(own_finish(&p,p.epoch,0)==OWN_STATE);
 {unsigned int w[64]={0};w[0]=0x314e574f;w[1]=w[2]=1;w[3]=11;w[5]=w[6]=1;w[17]=1;w[18]=10;w[19]=11;w[20]=12;w[23]=w[24]=w[25]=2;w[34]=1;w[40]=0x1f0000;w[45]=5;w[48]=7;
 assert(ownership_report_valid(w,1,11));
 for(i=23;i<=25;i++){w[i]=0;assert(!ownership_report_valid(w,1,11));w[i]=2;}
 w[10]=1;assert(!ownership_report_valid(w,1,11));w[10]=0;w[35]=1;assert(!ownership_report_valid(w,1,11));w[35]=0;w[48]=3;assert(!ownership_report_valid(w,1,11));w[48]=7;w[5]=2;assert(!ownership_report_valid(w,1,11));
 }
 /* No ABA via wrap, and cancellation replay cannot duplicate acknowledgement. */
 {struct ownership q={0xffffffffu,OWN_RETIRED,1,1,0,0,0,0,0,0,0};
 assert(own_restart(&q,q.epoch)==OWN_STATE);assert(q.epoch==0xffffffffu);
 q.epoch=1;q.phase=OWN_IDLE;assert(!own_begin(&q,1,2));q.next_ticket=0xffffffffu;
 assert(own_lease(&q,1)==OWN_STATE);assert(!q.refs);
 assert(!own_cancel(&q,1));assert(!own_cancel(&q,1));assert(!own_finish(&q,1,0));
 assert(own_finish(&q,1,0)==OWN_STATE);assert(q.acks==1&&q.aborts==1);
 }
 return 0;
}

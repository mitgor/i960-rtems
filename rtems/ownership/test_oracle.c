/* Native transition oracle using the exact target ownership policy. */
#include <stdio.h>
#include <string.h>
#include "policy.h"
int main(void){struct ownership p={1,0,0x10203040,0x10203040,0,0,0,0,0,0,0};unsigned int req[4],out[20],rc,final=0,started=0,done=0,seen=0,value=0,other=0,other_value=0;
 while(fread(req,sizeof(req),1,stdin)==1){unsigned int op=req[1],e=req[2],v=req[3];rc=0;
  if(op==0){}
  else if(op==10){other++;other_value=other_value*1664525u+1013904223u;}
  else if(!own_epoch(&p,e))rc=own_reject(&p,OWN_STALE);
  else switch(op){
   case 1:rc=own_begin(&p,e,v);break;
   case 2:if(p.phase!=OWN_HELD||started!=done)rc=own_reject(&p,OWN_STATE);else{value=v;started++;}break;
   case 3:rc=own_cancel(&p,e);break;
   case 4:case 12:rc=own_finish(&p,e,op==12);if(!rc&&started!=done){seen=p.committed;p.committed=p.staged=value;done++;}break;
   case 5:rc=own_lease(&p,e);break;
   case 6:rc=own_complete(&p,e,v);break;
   case 7:rc=(p.phase==OWN_HELD||p.phase==OWN_CANCEL||p.phase==OWN_QUARANTINE)?23:own_reject(&p,OWN_STATE);break;
   case 8:rc=own_restart(&p,e);break;
   case 9:rc=own_quarantine(&p,e);break;
   case 11:if(p.refs||(p.phase!=OWN_IDLE&&p.phase!=OWN_RETIRED&&p.phase!=OWN_QUARANTINE))rc=own_reject(&p,OWN_BUSY);else final=1;break;
   default:rc=own_reject(&p,OWN_STATE);
  }
  memset(out,0,sizeof(out));out[0]=rc;out[1]=final;memcpy(out+2,&p,11*sizeof(unsigned int));out[13]=started;out[14]=done;out[15]=seen;out[16]=other;out[17]=other_value;out[18]=p.epoch;
  if(fwrite(out,sizeof(out),1,stdout)!=1)return 1;
 }
 return 0;
}

/* Single-owner raw lwIP module. Call only from the owning RTEMS task.
 * op0 initializes pristine BSS; op1 advances timers; op2 accepts ONE IP packet
 * and drains bounded length-prefixed output; op3 returns counters.
 * A fatal assertion parks the module: the supervisor must retain its storage.
 * This entry is a trusted bounded application ABI, not process isolation. */
#include "../../net/network.h"
#include "app_service.h"
static unsigned int initialized,elapsed;
unsigned int http_uptime_seconds(void){return elapsed/1000u;}
void bounded_fatal(unsigned int code){
 volatile unsigned int retained_code=code;
 for(;;){(void)retained_code;__asm__ volatile("":::"memory");}
}
unsigned int accele_net_entry(unsigned int op,unsigned int ms,const unsigned char *in,
 unsigned int n,unsigned char *out,unsigned int cap){
 if(ms>1000u||n>1500u||cap>2048u||(!in&&n)||(!out&&cap))return 0xffffffffu;
 if(op==0){if(initialized||n)return 0xffffffffu;network_init();initialized=1;return 0;}
 if(!initialized)return 0xffffffffu;
 if(op==1){if(n)return 0xffffffffu;elapsed+=ms;as_step(ms);network_step(ms,0,0);return 0;}
 if(op==2&&n>=4&&as_word(in)==AS_MAGIC){elapsed+=ms;as_step(ms);network_step(ms,0,0);return as_call(in,n,out,cap);}
 if(op==2){if(cap<1504u)return 0xffffffffu;elapsed+=ms;as_step(ms);network_step(ms,in,n);return network_output(out,cap);}
 if(op==3){if(n||cap<24u)return 0xffffffffu;return network_report(out);}
 return 0xffffffffu;
}

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "lifetime.h"
typedef unsigned int rtems_id;
#define RTEMS_EVENT_0 1
static unsigned int regs[0x1400/4];
static unsigned int *reg(unsigned int a){if(a==0x1324)regs[a/4]=0;return &regs[a/4];}
#define REG(a) (*reg(a))
static unsigned int ticks,switch_fault,switch_stop,switch_active[2];
static unsigned int _Thread_Dispatch_disable_level=1,_ISR_Nest_level=1;
static uintptr_t _Thread_Executing=0x1234;
static struct irq_lifetime life[2];
static unsigned int events;
static int rtems_event_send(unsigned int id,unsigned int event){assert(id==17&&event==1);events++;return 0;}
#define CHECK(x) assert((x)==0)
static void bounded_fatal(unsigned int x){(void)x;abort();}
#include "stop_target.h"
static void reset(void){memset(regs,0,sizeof(regs));memset(life,0,sizeof(life));memset(stop_diag,0,sizeof(stop_diag));
 stop_epoch=0x1234;stop_controller=17;switch_fault=switch_stop=ticks=events=0;REG(0x1328)=0x1fb;REG(0x1334)=0xff;
}
int main(void){unsigned int i;
 reset();assert(stop_mu_start()==0);for(i=0;i<2;i++){life[i].owner=0x1234+i;life[i].low=0x1000;life[i].high=0x2000;assert(lifetime_enter(&life[i],0x1234+i,0x1100,0,0,0xf2));}
 for(ticks=1;ticks<=8;ticks++)stop_mu_poll();assert(REG(0x131c)==0x71001234);
 REG(0x1314)=0x72001235;stop_mu_poll();assert(!events&&!switch_stop);
 REG(0x1314)=0x72001234;stop_mu_poll();assert(events==1&&switch_stop&&stop_diag[3]==9);
 stop_mu_poll();assert(events==1); /* repeated token cannot wake twice */
 for(i=0;i<2;i++)assert(lifetime_leave(&life[i],0x1234+i,0x1100,0,0,0xf2));REG(0x1314)=0x74001234;
 stop_mu_finish();assert(!switch_fault&&stop_diag[12]&&stop_diag[13]==0x4d554f4b);
 assert(!REG(0x1314)&&!REG(0x131c));
 reset();REG(0x1314)=1;assert(stop_mu_start()==1);
 reset();REG(0x1328)=0;stop_mu_poll();assert(switch_fault==8192);
 reset();stop_mu_finish();assert(switch_fault==16384&&!stop_diag[12]);
 puts("STOP1 target: ownership refusal, stale/duplicate tokens, stop event, drained release and release timeout passed");
}

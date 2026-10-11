/* Persistent RTEMS state, bounded asynchronous epochs, explicit dependency graph. */
#include <string.h>
#include <rtems/system.h>
#include <rtems/config.h>
#include <rtems/init.h>
#include <rtems/rtems/tasks.h>
#include <rtems/rtems/clock.h>
#include <rtems/rtems/event.h>
#include <rtems/rtems/options.h>
#include <rtems/rtems/sem.h>
#include <rtems/score/thread.h>
#include <rtems/score/isr.h>
#include "buffer_io.h"
#include "../switch/lifetime.h"
#include "../ownership/policy.h"
#include "../irq/timer_hw.h"
#include "../persistirq/graph.h"
#include "lease.h"
extern unsigned char _bss_start[],_bss_end[];
extern void bounded_escape(unsigned int) __attribute__((noreturn));
extern void switch_probe(unsigned int*,unsigned int);
static unsigned char workspace[49152] __attribute__((aligned(16)));
static unsigned char stacks[6][8320] __attribute__((aligned(16)));
static unsigned int allocated,sizes[6],initialized,finalized,generation,phase,op,arg,request_gen,sequence,callbacks;
unsigned char switch_irq_areas[2][8192] __attribute__((aligned(16)));
volatile unsigned int switch_threads[2],switch_active[2],switch_fault,owner_checkpoint,other_checkpoint;
static volatile unsigned int ticks,two_live,handoffs,done[2],sampled_high[2];
static struct irq_lifetime life[2];
unsigned int switch_records[2][70];
static struct ownership resource;
static struct dep_graph graph;
static Semaphore_Control*mutex[2];static rtems_id locks[2],ids[4],controller;static Thread_Control*threads[4];
static unsigned int starts[4],b_done,c_done,b_seen,c_seen,value1=0x11223344,deferred,retired_tick;
static volatile unsigned int critical_phase,case_diag[20];
static struct execution_lease execution;
static unsigned int hw_checks,hw_drift,timer0_reload;
static unsigned int diag[352],ready_tick,stop_tick,epoch_start,clean_epochs,async_epochs,follow_epochs,quarantine_hash[4];
void bounded_fatal(unsigned int code){stop_timer();bounded_escape(0xf0000000u|code);}
#define CHECK(x) do{unsigned int rc=(x);if(rc)bounded_fatal(0x10000+__LINE__*256+rc);}while(0)
#define REQUIRE(x) do{if(!(x))bounded_fatal(0x90000+__LINE__);}while(0)
static unsigned int hash(unsigned int p,unsigned int n){unsigned int h=2166136261u;while(n--)h=(h^*(volatile unsigned char*)p++)*16777619u;return h;}
static unsigned int progress(unsigned int i){return REG((unsigned int)&switch_records[i][69]);}
static void*stack_alloc(unsigned int n){unsigned int i=allocated++;REQUIRE(i<6&&n<=8192);sizes[i]=n;memset(stacks[i],0xa5,8320);return stacks[i]+16;}
static void stack_free(void*p){bounded_fatal(0x91000);}
static void idle_error(void){bounded_fatal(0xdead);}
static void pump(void){rtems_task_priority old;CHECK(rtems_task_set_priority(RTEMS_SELF,3,&old));CHECK(rtems_task_set_priority(RTEMS_SELF,1,&old));}
/* All firmware interrupt sources stay masked during the parked callback.
 * Timer 0 and all DMA/SCSI engines remain outside this lease. */
static void stop_mu_poll(void){unsigned int ack;
 hw_checks++;
 if(REG(0x1328)!=0x1fb||REG(0x1334)!=0xff||REG(0xff008504)!=0x2000||REG(0xff008528)!=0xf80000||REG(0x3c)!=(unsigned int)timer_isr||REG(0xff000310)!=20000||REG(0xff008510)!=0x6000||REG(0xff000300)!=timer0_reload){hw_drift++;switch_fault|=8192;}
 if(!ready_tick&&ticks-epoch_start==8){ready_tick=ticks;lease_init(&execution,sequence,ticks);REG(0x131c)=0x71000000u|sequence;(void)REG(0x131c);}
 if(!ready_tick||stop_tick)return;
 ack=lease_poll(&execution,ticks,REG(0x1314));
 if(ack){REG(0x131c)=ack;(void)REG(0x131c);}
 if(execution.state==3){stop_tick=ticks;REG(0x1324)=2;(void)REG(0x1324);CHECK(rtems_event_send(controller,RTEMS_EVENT_0));}
}
static void wait_ticks(unsigned int start,unsigned int n){unsigned int budget=1000000;priority20();while(ticks-start<n&&--budget)__asm__ volatile("":::"memory");mask31();REQUIRE(budget);}
static void critical(void){wait_ticks(epoch_start,16);_Thread_Disable_dispatch();_Thread_Disable_dispatch();
 critical_phase=1;case_diag[1]=ticks;case_diag[9]=life[1].entries;wait_ticks(case_diag[1],12);case_diag[2]=ticks;case_diag[5]=_Thread_Dispatch_disable_level;
 _Thread_Enable_dispatch();case_diag[6]=_Thread_Dispatch_disable_level;critical_phase=2;wait_ticks(case_diag[2],12);case_diag[3]=ticks;case_diag[7]=_Thread_Dispatch_disable_level;case_diag[10]=life[1].entries;critical_phase=0;
 _Thread_Enable_dispatch();case_diag[4]=ticks;case_diag[8]=_Thread_Dispatch_disable_level;
}
static void stop_critical_observe(void){if(!critical_phase)return;case_diag[12+critical_phase]++;
 if((unsigned int)_Thread_Executing!=switch_threads[0]||_Thread_Dispatch_disable_level!=3-critical_phase||_ISR_Nest_level)case_diag[15]++;
 if(_Context_Switch_necessary)case_diag[16]++;
}
static void measure(unsigned int id){unsigned int sp,base=(unsigned int)switch_irq_areas[id];
 __asm__ volatile("mov sp,%0":"=r"(sp));
 if(sp<base+192||sp>base+8128)switch_fault|=1;
 if(sp>sampled_high[id])sampled_high[id]=sp;
}
void switch_irq_enter(unsigned int id,unsigned int fp){
 measure(id);
 if(!lifetime_enter(&life[id],(unsigned int)_Thread_Executing,fp,REG(fp-16),REG(fp-12),REG(fp-8)))switch_fault|=2;
 if(life[0].live&&life[1].live)two_live++;
}
void switch_irq_body(void){
 _ISR_Nest_level++;_Thread_Dispatch_disable_level++;

 ticks++;
 stop_mu_poll();
 CHECK(rtems_clock_tick());
 _Thread_Dispatch_disable_level--;_ISR_Nest_level--;
 stop_critical_observe();

 if(_Context_Switch_necessary&&!_Thread_Dispatch_disable_level){
  if(_Thread_Heir!=_Thread_Executing)handoffs++;
  _Thread_Dispatch(); /* This call may stay suspended on this owner's C stack. */
 }
}
void switch_irq_leave(unsigned int id,unsigned int fp){unsigned int i,tc,*save=(unsigned int*)(switch_irq_areas[id]+64);
 measure(id);
 if(!lifetime_leave(&life[id],(unsigned int)_Thread_Executing,fp,REG(fp-16),REG(fp-12),REG(fp-8)))switch_fault|=4;
 for(i=0;i<64;i++)if(switch_irq_areas[id][i]!=0xa5||switch_irq_areas[id][8128+i]!=0xa5)switch_fault|=8;
 __asm__ volatile("modtc 0,0,%0":"=r"(tc));if((tc^save[16])&0x0f000000)switch_fault|=16;
}
static void deep_probe(unsigned int n,unsigned int id){volatile unsigned int pad[16];unsigned int i;
 for(i=0;i<16;i++)pad[i]=id*65536+n*256+i;
 if(n)deep_probe(n-1,id);else switch_probe(switch_records[id],0x19600000u+id*0x10000000u);
 for(i=0;i<16;i++)if(pad[i]!=id*65536+n*256+i)switch_fault|=32;
}
static void B(rtems_task_argument);static void C(rtems_task_argument);static void Worker(rtems_task_argument);
static void launch(unsigned int i){REQUIRE(!life[i==0?0:1].live||i==1||i==2);
 if(starts[i]){REQUIRE(threads[i]->current_state==STATES_SUSPENDED&&!threads[i]->resource_count);CHECK(rtems_task_restart(ids[i],i==3?1:0));}
 else CHECK(rtems_task_start(ids[i],i==1?B:i==2?C:Worker,i==3?1:0));starts[i]++;
}
static void C(rtems_task_argument ignored){CHECK(graph_wait(&graph,2,1));CHECK(rtems_semaphore_obtain(locks[1],RTEMS_WAIT,WATCHDOG_NO_TIMEOUT));CHECK(graph_claim(&graph,2,1));
 REQUIRE(b_done);c_seen=value1;value1=0x44000000u|generation;c_done=1;CHECK(graph_release(&graph,2,1));CHECK(rtems_semaphore_release(locks[1]));CHECK(rtems_task_suspend(RTEMS_SELF));bounded_fatal(0x92000);
}
static void B(rtems_task_argument ignored){CHECK(rtems_semaphore_obtain(locks[1],RTEMS_NO_WAIT,0));CHECK(graph_claim(&graph,1,1));launch(2);
 CHECK(graph_wait(&graph,1,0));CHECK(rtems_semaphore_obtain(locks[0],RTEMS_WAIT,WATCHDOG_NO_TIMEOUT));CHECK(graph_claim(&graph,1,0));
 REQUIRE(resource.phase==OWN_RETIRED&&!resource.refs&&resource.committed==resource.staged);
 b_seen=resource.committed;resource.committed=resource.staged=0x22000000u|generation;value1=0x33000000u|generation;b_done=1;
 CHECK(graph_release(&graph,1,0));CHECK(rtems_semaphore_release(locks[0]));CHECK(graph_release(&graph,1,1));CHECK(rtems_semaphore_release(locks[1]));CHECK(rtems_task_suspend(RTEMS_SELF));bounded_fatal(0x92001);
}
static void Worker(rtems_task_argument id){unsigned int i,rc,*r=switch_records[id];
 REQUIRE((unsigned int)_Thread_Executing==switch_threads[id]);switch_records[id][69]=1000000;
 if(!id){CHECK(own_begin(&resource,generation,0xdead0000u|generation));CHECK(rtems_semaphore_obtain(locks[0],RTEMS_NO_WAIT,0));CHECK(graph_claim(&graph,0,0));CHECK(own_lease(&resource,generation));launch(1);if(arg)critical();}
 deep_probe(16,id);REQUIRE(r[69]&&(id?other_checkpoint:owner_checkpoint));
 for(i=0;i<16;i++)if(r[i]!=r[16+i])switch_fault|=128;
 for(i=0;i<16;i++)if(i!=2&&i!=3&&i!=5&&r[32+i]!=r[48+i])switch_fault|=256;
 if(r[64]!=r[65]||r[66]!=r[67]||r[68])switch_fault|=512;
 REQUIRE(!switch_active[id]&&!life[id].live&&life[id].entries==life[id].returns);
 if(!id){do{_Thread_Disable_dispatch();rc=own_finish(&resource,generation,0);
  if(!rc){CHECK(graph_release(&graph,0,0));CHECK(rtems_semaphore_release(locks[0]));retired_tick=ticks;}
  _Thread_Enable_dispatch();if(rc==OWN_DEFERRED){deferred++;CHECK(rtems_task_wake_after(1));}else REQUIRE(!rc);
 }while(rc==OWN_DEFERRED);}
 done[id]=1;if(id)CHECK(rtems_event_send(controller,RTEMS_EVENT_1));CHECK(rtems_task_suspend(RTEMS_SELF));bounded_fatal(0x93000);
}
static void retained(void){struct irq_lifetime*l=&life[0];unsigned int j;
 REQUIRE(switch_active[0]&&l->live&&l->entries==l->returns+1&&threads[0]->current_state==STATES_SUSPENDED);
 REQUIRE(REG(l->frame-16)==l->pc&&REG(l->frame-12)==l->ac&&REG(l->frame-8)==l->vector);
 for(j=0;j<15;j++)REQUIRE(REG((unsigned int)switch_irq_areas[0]+64+j*4)==0x19600000u+j);
}
static void hashes(unsigned int*out){out[0]=hash(life[0].low,8192);out[1]=hash((unsigned int)switch_irq_areas[0],8192);out[2]=hash((unsigned int)threads[1]->Start.Initial_stack.area,8192);out[3]=hash((unsigned int)threads[2]->Start.Initial_stack.area,8192);}
static void check_quarantine(void){unsigned int h[4],i;retained();hashes(h);for(i=0;i<4;i++)REQUIRE(h[i]==quarantine_hash[i]);REQUIRE(graph.owner[0]==0&&graph.owner[1]==1&&graph.wait[1]==1&&graph.wait[2]==2&&graph.closed==7);}
static void finish_mu(void){unsigned int budget=1000000;
 REQUIRE(!switch_fault&&!armed&&!_ISR_Nest_level&&!_Thread_Dispatch_disable_level);
 REG(0x131c)=0x75000000u|sequence;(void)REG(0x131c);while(REG(0x1314)!=(0x74000000u|sequence)&&--budget){}REQUIRE(budget);
 REG(0x1314)=0;(void)REG(0x1314);REG(0x131c)=0;(void)REG(0x131c);REG(0x1324)=2;(void)REG(0x1324);
 REQUIRE(REG(0x1328)==0x1fb&&REG(0x1334)==0xff&&!REG(0x1314)&&!REG(0x131c)&&!(REG(0x1324)&2));
}
static void run_epoch(void){unsigned int i,n,ticket,before;rtems_event_set events;
 REQUIRE(REG(0x1328)==0x1fb&&REG(0x1334)==0xff&&!REG(0x1314)&&!REG(0x131c)&&!(REG(0x1324)&2)&&!(REG(0x1330)&2));
 memset((void*)case_diag,0,sizeof(case_diag));case_diag[0]=arg;ready_tick=stop_tick=critical_phase=0;epoch_start=ticks;diag[9]=ticks;async_epochs++;hw_checks=hw_drift=0;timer0_reload=REG(0xff000300);
 if(op==3){check_quarantine();follow_epochs++;}
 else{
  REQUIRE(!life[0].live&&!life[1].live&&!mutex[0]->Core_control.mutex.holder&&!mutex[1]->Core_control.mutex.holder);
  if(generation)CHECK(own_restart(&resource,generation));generation++;REQUIRE(generation==resource.epoch);
  graph_reset(&graph);b_done=c_done=b_seen=c_seen=deferred=retired_tick=0;done[0]=0;owner_checkpoint=0;memset(switch_records[0],0,sizeof(switch_records[0]));
 }
 done[1]=0;other_checkpoint=0;memset(switch_records[1],0,sizeof(switch_records[1]));CHECK(start_timer());
 if(op!=3)launch(0);launch(3);
 CHECK(rtems_event_receive(RTEMS_EVENT_0,RTEMS_EVENT_ANY|RTEMS_WAIT,LEASE_CAP+1024,&events));diag[12]=ticks;case_diag[11]=ticks;case_diag[12]=_Thread_Dispatch_disable_level;REQUIRE(stop_tick);
 if(op!=3){
  REQUIRE(graph.owner[0]==0&&graph.owner[1]==1&&graph.wait[1]==1&&graph.wait[2]==2&&threads[1]->current_state==STATES_WAITING_FOR_MUTEX&&threads[2]->current_state==STATES_WAITING_FOR_MUTEX);
  diag[282]=graph_wait(&graph,0,1);REQUIRE(diag[282]==G_CYCLE&&!graph.wait[0]);diag[49]=graph_freeze(&graph,1);REQUIRE(diag[49]==7);
  diag[283]=graph_wait(&graph,0,1);REQUIRE(diag[283]==G_CLOSED&&!graph.wait[0]);
  for(i=0;i<2;i++){diag[280+i]=rtems_semaphore_release(locks[i]);REQUIRE(diag[280+i]==RTEMS_NOT_OWNER_OF_RESOURCE);}
  CHECK(own_cancel(&resource,generation));ticket=resource.ticket;
  diag[284]=own_complete(&resource,generation-1,ticket);diag[285]=own_complete(&resource,generation,ticket+1);REQUIRE(diag[284]==OWN_STALE&&diag[285]==OWN_STALE&&resource.refs);
  if(op==1){
   owner_checkpoint=1;for(n=0;n<8&&!deferred;n++)CHECK(rtems_task_wake_after(1));REQUIRE(deferred&&resource.refs&&!b_done&&!c_done);
   CHECK(rtems_task_wake_after(2));CHECK(own_complete(&resource,generation,ticket));diag[13]=ticks;
   diag[286]=own_complete(&resource,generation,ticket);REQUIRE(diag[286]==OWN_STALE);
   for(n=0;n<8&&(!done[0]||!b_done||!c_done);n++)CHECK(rtems_task_wake_after(1));REQUIRE(done[0]&&b_done&&c_done&&!resource.refs&&!life[0].live);
   phase=1;clean_epochs++;
  }else{
   before=progress(0);CHECK(rtems_task_wake_after(4));REQUIRE(progress(0)&&progress(0)!=before);CHECK(own_quarantine(&resource,generation));
   for(i=0;i<3;i++)CHECK(rtems_task_suspend(ids[i]));phase=2;diag[15]=ticks;retained();hashes(quarantine_hash);
   CHECK(rtems_task_wake_after(4));check_quarantine();
  }
 }
 diag[88]=progress(1);other_checkpoint=1;
 CHECK(rtems_event_receive(RTEMS_EVENT_1,RTEMS_EVENT_ANY|RTEMS_WAIT,8,&events));pump();diag[16]=ticks;
 REQUIRE(done[1]&&!life[1].live&&!switch_active[1]&&threads[3]->current_state==STATES_SUSPENDED);diag[89]=progress(1);stop_timer();
 if(phase==2)check_quarantine();
 for(n=0;n<1000;n++){REQUIRE(!_ISR_Nest_level&&!_Thread_Dispatch_disable_level&&_Thread_Heir==_Thread_Executing&&!_Context_Switch_necessary);diag[90]++;}
 finish_mu();
}
static unsigned int process(void){unsigned int i;
 if(op==1||op==2){if(phase==2||arg!=0)return OWN_STATE;if(request_gen!=generation+1||generation>=65534)return OWN_STALE;run_epoch();return 0;}
 if(request_gen!=generation)return OWN_STALE;
 if(op==3){if(phase!=2)return OWN_STATE;run_epoch();return 0;}
 if(op==4)return own_complete(&resource,request_gen,arg);
 if(op==5){if(resource.refs||!generation)return OWN_BUSY;for(i=0;i<4;i++)REQUIRE(threads[i]->current_state&STATES_SUSPENDED);finalized=1;phase=3;return 0;}
 if(op==6)return phase==2?OWN_STATE:OWN_OK;
 return op==0?0:OWN_STATE;
}
static void report(unsigned int rc){unsigned int i,j,h[4],mask=0;unsigned char*out=(unsigned char*)BIO_BASE+BIO_OUTPUT;
 for(i=0;i<allocated;i++){for(j=0;j<16;j++)REQUIRE(stacks[i][j]==0xa5);for(j=16+sizes[i];j<8320;j++)REQUIRE(stacks[i][j]==0xa5);}
 for(i=0;i<2;i++)for(j=0;j<64;j++)REQUIRE(switch_irq_areas[i][j]==0xa5&&switch_irq_areas[i][8128+j]==0xa5);
 if(resource.phase==OWN_QUARANTINE)check_quarantine();
 diag[0]=0x31515250;diag[1]=1;diag[2]=rc;diag[3]=op;diag[4]=sequence;diag[5]=generation;diag[6]=phase;diag[7]=finalized;diag[8]=ticks;
 diag[10]=ready_tick;diag[11]=stop_tick;diag[14]=retired_tick;diag[17]=switch_fault;diag[18]=switch_active[0];diag[19]=switch_active[1];diag[20]=_ISR_Nest_level;diag[21]=_Thread_Dispatch_disable_level;diag[22]=armed;
 diag[23]=REG(0xff008504);diag[24]=REG(0xff008528);diag[25]=REG(0x3c);diag[26]=saved_vector;diag[27]=REG(0xff000310);diag[28]=REG(0xff000314);diag[29]=REG(0xff000318);diag[30]=REG(0xff008500);diag[31]=++callbacks;
 memcpy(diag+32,&resource,44);diag[43]=value1;diag[44]=b_seen;diag[45]=c_seen;diag[46]=b_done;diag[47]=c_done;diag[48]=deferred;
 for(i=0;i<2;i++){diag[50+i]=graph.owner[i];diag[76+i]=mutex[i]->Core_control.mutex.holder_id;diag[78+i]=mutex[i]->Core_control.mutex.nest_count;}
 for(i=0;i<4;i++){diag[52+i]=graph.wait[i];diag[56+i]=threads[i]->current_state;diag[60+i]=ids[i];diag[64+i]=threads[i]->resource_count;diag[68+i]=starts[i];diag[72+i]=(unsigned int)threads[i]->Start.Initial_stack.area;if(threads[i]->current_state&STATES_SUSPENDED)mask|=1u<<i;}
 if(resource.phase==OWN_QUARANTINE){hashes(h);for(i=0;i<4;i++){diag[80+i]=quarantine_hash[i];diag[84+i]=h[i];}}
 diag[49]=graph.closed;diag[91]=allocated;
 for(i=0;i<2;i++){unsigned int*s=(unsigned int*)&life[i];for(j=0;j<10;j++)diag[96+i*82+j]=s[j];diag[106+i*82]=(unsigned int)switch_irq_areas[i];diag[107+i*82]=sampled_high[i];for(j=0;j<70;j++)diag[108+i*82+j]=switch_records[i][j];}
 memcpy(diag+260,(const void*)case_diag,80);diag[288]=(unsigned int)&resource;diag[289]=(unsigned int)&graph;diag[290]=(unsigned int)_Thread_Executing;diag[291]=(unsigned int)_Thread_Heir;diag[292]=mask;diag[293]=clean_epochs;diag[294]=async_epochs;diag[295]=follow_epochs;
 diag[296]=arg;diag[297]=two_live;diag[298]=handoffs;diag[316]=request_gen;diag[317]=arg;diag[318]=0x514f4b31;diag[319]=sequence;
 diag[320]=0x3145534c;diag[321]=1;diag[322]=execution.state;diag[323]=execution.reason;diag[324]=execution.grant;diag[325]=execution.last;diag[326]=execution.seq;diag[327]=execution.rejects;diag[328]=execution.stop-execution.last;diag[329]=execution.maxgap;diag[330]=hw_checks;diag[331]=hw_drift;
 diag[332]=0x2000;diag[333]=0xf80000;diag[334]=(unsigned int)timer_isr;diag[335]=saved_vector;diag[336]=20000;diag[337]=timer0_reload;diag[338]=REG(0xff000300);diag[339]=REG(0xff008510);diag[340]=0xc0f2c000;diag[341]=0xc0f9bff0;diag[342]=REG(0x1328);diag[343]=REG(0x1334);diag[344]=LEASE_CAP;diag[345]=LEASE_TTL;diag[346]=execution.start;diag[347]=execution.stop;diag[348]=execution.epoch;diag[349]=15;diag[350]=0;diag[351]=0;
 for(i=0;i<352;i++)bio_put(out+i*4,diag[i]);bio_put((unsigned char*)BIO_BASE+20,0);bio_put((unsigned char*)BIO_BASE+24,1408);bio_put((unsigned char*)BIO_BASE+28,sequence);
}
static void Init(rtems_task_argument unused){unsigned int i;Objects_Locations location;
 memset(switch_irq_areas,0xa5,sizeof(switch_irq_areas));graph_reset(&graph);resource.epoch=1;resource.committed=resource.staged=0x10203040;
 for(i=0;i<2;i++){CHECK(rtems_semaphore_create(0x4c4f4330+i,1,RTEMS_BINARY_SEMAPHORE|RTEMS_PRIORITY|RTEMS_INHERIT_PRIORITY,0,&locks[i]));mutex[i]=_Semaphore_Get(locks[i],&location);REQUIRE(location==OBJECTS_LOCAL);_Thread_Enable_dispatch();}
 for(i=0;i<4;i++){CHECK(rtems_task_create(0x574b5230+i,2,8192,RTEMS_TIMESLICE|RTEMS_INTERRUPT_LEVEL(31),RTEMS_DEFAULT_ATTRIBUTES,&ids[i]));threads[i]=_Thread_Get(ids[i],&location);REQUIRE(location==OBJECTS_LOCAL);_Thread_Enable_dispatch();}
 for(i=0;i<2;i++){Thread_Control*t=threads[i?3:0];switch_threads[i]=(unsigned int)t;life[i].owner=(unsigned int)t;life[i].low=(unsigned int)t->Start.Initial_stack.area;life[i].high=life[i].low+8192;}
 controller=_Thread_Executing->Object.id;
 for(;;){unsigned char*b=(unsigned char*)BIO_BASE;unsigned int rc;
  sequence=bio_word(b+8);request_gen=bio_word(b+BIO_INPUT+4);op=bio_word(b+BIO_INPUT+8);arg=bio_word(b+BIO_INPUT+12);diag[90]=0;
  rc=process();report(rc);_CPU_Context_switch(&_Thread_Executing->Registers,&_Thread_BSP_context);REQUIRE(!finalized);
 }
}
static rtems_initialization_tasks_table tasks[]={{0x494e4954,8192,1,RTEMS_DEFAULT_ATTRIBUTES,Init,RTEMS_INTERRUPT_LEVEL(31),0}};
static rtems_api_configuration_table api={5,0,2,0,0,0,0,0,1,tasks};
static rtems_configuration_table config={workspace,sizeof(workspace),0,10000,1,0,0,0,0,0,0,0,&api,0,0};
static rtems_cpu_table cpu={0,0,0,idle_error,1,2048,2048,0,stack_alloc,stack_free};
void _ISR_Handler(void){bounded_fatal(0x40000);}
void _CPU_ISR_install_raw_handler(unsigned int v,proc_ptr n,proc_ptr*o){bounded_fatal(0x40000|v);}
unsigned int bounded_main(unsigned int a){unsigned char*p=(unsigned char*)a;if(a!=BIO_BASE||!bio_request_valid(p)||bio_word(p+16)<1408||bio_word(p+12)!=16||bio_word(p+BIO_INPUT)!=0x31515250||finalized)return 1;
 if(!initialized){for(p=_bss_start;p<_bss_end;p++)*p=0;initialized=1;rtems_initialize_executive(&config,&cpu);}else _CPU_Context_switch(&_Thread_BSP_context,&_Thread_Executing->Registers);return 0;
}

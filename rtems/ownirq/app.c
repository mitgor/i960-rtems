/* Bounded asynchronous ownership experiment; separate from production autonet. */
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
extern unsigned char _bss_start[],_bss_end[];
extern void bounded_escape(unsigned int) __attribute__((noreturn));
extern void switch_probe(unsigned int*,unsigned int);
static unsigned char workspace[49152] __attribute__((aligned(16)));
static unsigned char stacks[5][8320] __attribute__((aligned(16)));
static unsigned int allocated,sizes[5],initialized,mode,epoch;
unsigned char switch_irq_areas[2][8192] __attribute__((aligned(16)));
volatile unsigned int switch_threads[2],switch_active[2],switch_fault,switch_stop,owner_checkpoint;
static volatile unsigned int ticks,two_live,handoffs,done[2],sampled_high[2];
static struct irq_lifetime life[2];
unsigned int switch_records[2][70];
static struct ownership resource;
static Semaphore_Control *mutex;
static rtems_id mutex_id,owner_id,other_id,waiter_id,controller;
static Thread_Control *waiter;
static unsigned int wait_started,wait_done,wait_seen,deferred,retired_tick;
static volatile unsigned int critical_phase,case_diag[20];
static unsigned int diag[256],ready_tick,stop_tick;
void bounded_fatal(unsigned int code){stop_timer();bounded_escape(0xf0000000u|code);}
#define CHECK(x) do{unsigned int rc=(x);if(rc)bounded_fatal(0x10000+__LINE__*256+rc);}while(0)
#define REQUIRE(x) do{if(!(x))bounded_fatal(0x90000+__LINE__);}while(0)
static unsigned int hash(unsigned int p,unsigned int n){unsigned int h=2166136261u;while(n--)h=(h^*(volatile unsigned char*)p++)*16777619u;return h;}
static unsigned int progress(unsigned int i){return REG((unsigned int)&switch_records[i][69]);}
static unsigned int is_clean(void){return mode<=2;}
static void*stack_alloc(unsigned int n){unsigned int i=allocated++;REQUIRE(i<5&&n<=8192);sizes[i]=n;memset(stacks[i],0xa5,8320);return stacks[i]+16;}
static void stack_free(void*p){bounded_fatal(0x91000);}
static void idle_error(void){bounded_fatal(0xdead);}
static void stop_mu_poll(void){unsigned int selected=mode==2?2:1;
 if(REG(0x1328)!=0x1fb||REG(0x1334)!=0xff){switch_fault|=8192;return;}
 if(!ready_tick&&(((mode<=2||mode==4)&&critical_phase==selected)||((mode==3||mode==5)&&ticks==16))){ready_tick=ticks;REG(0x131c)=0x71000000u|epoch;(void)REG(0x131c);}
 if(REG(0x1314)==(0x72000000u|epoch)&&!stop_tick){
  stop_tick=ticks;case_diag[17]=critical_phase;REG(0x1324)=2;(void)REG(0x1324);
  switch_stop=1;CHECK(rtems_event_send(controller,RTEMS_EVENT_0));
 }
}
/* Case 1/2: READY only inside the requested nested critical level. Keep the
 * same owner and B's suspended continuation until both levels are released. */
static void stop_wait_ticks(unsigned int start,unsigned int n){unsigned int budget=1000000;
 priority20();while(ticks-start<n&&--budget)__asm__ volatile("":::"memory");
 mask31();if(!budget)bounded_fatal(0x58000);
}
static void stop_critical(void){
 stop_wait_ticks(0,16); /* both workers have accumulated IRQ continuations */
 _Thread_Disable_dispatch();_Thread_Disable_dispatch();
 critical_phase=1;case_diag[1]=ticks;case_diag[9]=life[1].entries;
 stop_wait_ticks(case_diag[1],12);
 case_diag[2]=ticks;case_diag[5]=_Thread_Dispatch_disable_level;
 _Thread_Enable_dispatch();case_diag[6]=_Thread_Dispatch_disable_level;
 critical_phase=2;stop_wait_ticks(case_diag[2],12);
 case_diag[3]=ticks;case_diag[7]=_Thread_Dispatch_disable_level;
 case_diag[10]=life[1].entries;critical_phase=0;
 _Thread_Enable_dispatch();case_diag[4]=ticks;case_diag[8]=_Thread_Dispatch_disable_level;
}
static void stop_critical_observe(void){
 if(!critical_phase)return;
 case_diag[12+critical_phase]++;
 if((unsigned int)_Thread_Executing!=switch_threads[0]||
    _Thread_Dispatch_disable_level!=3-critical_phase||_ISR_Nest_level)case_diag[15]++;
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
 #ifdef I960_DEFER_TEST
 if(defer_phase && _Thread_Dispatch_disable_level>deferral[16])deferral[16]=_Thread_Dispatch_disable_level;
#endif
 ticks++;
 stop_mu_poll();
 CHECK(rtems_clock_tick());
 _Thread_Dispatch_disable_level--;_ISR_Nest_level--;
 stop_critical_observe();
#ifdef I960_DEFER_TEST
 if(defer_phase){
  deferral[9+defer_phase]++;
  if((unsigned int)_Thread_Executing!=deferral[2])deferral[1]|=1;
  if(_Thread_Dispatch_disable_level!=3-defer_phase)deferral[1]|=2;
  if(_ISR_Nest_level)deferral[1]|=4;
  if(_Context_Switch_necessary)deferral[12]++;
  if(_Thread_Heir!=_Thread_Executing)deferral[13]++;
 }
#endif
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
static void Waiter(rtems_task_argument arg){waiter=_Thread_Executing;wait_started=1;
 CHECK(rtems_semaphore_obtain(mutex_id,RTEMS_WAIT,WATCHDOG_NO_TIMEOUT));
 REQUIRE(resource.phase==OWN_RETIRED&&!resource.refs&&resource.staged==resource.committed);
 wait_seen=resource.committed;resource.committed=resource.staged=0x55667788;wait_done=1;
 CHECK(rtems_semaphore_release(mutex_id));CHECK(rtems_task_suspend(RTEMS_SELF));bounded_fatal(0x92000);
}
static void Worker(rtems_task_argument id){unsigned int *r=switch_records[id],i,rc;
 switch_threads[id]=(unsigned int)_Thread_Executing;life[id].owner=switch_threads[id];
 life[id].low=(unsigned int)_Thread_Executing->Start.Initial_stack.area;life[id].high=life[id].low+_Thread_Executing->Start.Initial_stack.size;
 switch_records[id][69]=1000000;
 if(!id){CHECK(own_begin(&resource,epoch,0xdeadbeef));CHECK(rtems_semaphore_obtain(mutex_id,RTEMS_NO_WAIT,0));CHECK(own_lease(&resource,epoch));
  CHECK(rtems_task_start(waiter_id,Waiter,0));
  if(mode<=2||mode==4)stop_critical();
 }
 deep_probe(16,id);
 REQUIRE(id==0&&is_clean()&&owner_checkpoint&&r[69]);
 for(i=0;i<16;i++)if(r[i]!=r[16+i])switch_fault|=128;
 for(i=0;i<16;i++)if(i!=2&&i!=3&&i!=5&&r[32+i]!=r[48+i])switch_fault|=256;
 if(r[64]!=r[65]||r[66]!=r[67]||r[68])switch_fault|=512;
 REQUIRE(!switch_active[0]&&!life[0].live&&life[0].entries==life[0].returns);
 do{_Thread_Disable_dispatch();rc=own_finish(&resource,epoch,0);
  if(!rc){CHECK(rtems_semaphore_release(mutex_id));retired_tick=ticks;}
  _Thread_Enable_dispatch();
  if(rc==OWN_DEFERRED){deferred++;CHECK(rtems_task_wake_after(1));}
  else REQUIRE(!rc);
 }while(rc==OWN_DEFERRED);
 done[id]=1;CHECK(rtems_task_suspend(RTEMS_SELF));bounded_fatal(0x93000);
}
static void retained(unsigned int i){struct irq_lifetime*l=&life[i];unsigned int j;
 REQUIRE(switch_active[i]&&l->live&&l->entries==l->returns+1);
 REQUIRE(REG(l->frame-16)==l->pc&&REG(l->frame-12)==l->ac&&REG(l->frame-8)==l->vector);
 for(j=0;j<15;j++)REQUIRE(REG((unsigned int)switch_irq_areas[i]+64+j*4)==0x19600000u+i*0x10000000u+j);
}
static void finish_mu(void){unsigned int budget=1000000;
 REQUIRE(!switch_fault&&!armed&&!_ISR_Nest_level&&!_Thread_Dispatch_disable_level);
 REG(0x131c)=0x75000000u|epoch;(void)REG(0x131c);
 while(REG(0x1314)!=(0x74000000u|epoch)&&--budget){}
 REQUIRE(budget);diag[253]=budget;
 REG(0x1314)=0;(void)REG(0x1314);REG(0x131c)=0;(void)REG(0x131c);REG(0x1324)=2;(void)REG(0x1324);
 REQUIRE(REG(0x1328)==0x1fb&&REG(0x1334)==0xff&&!REG(0x1314)&&!REG(0x131c)&&!(REG(0x1324)&2));diag[254]=0x4d554f4b;
}
static void Init(rtems_task_argument arg){unsigned int i,j,n,ticket,before,other_after;Objects_Locations location;rtems_event_set events;
 memset(switch_irq_areas,0xa5,sizeof(switch_irq_areas));resource.epoch=epoch;resource.committed=resource.staged=0x10203040;
 CHECK(rtems_semaphore_create(0x4c4f434b,1,RTEMS_BINARY_SEMAPHORE|RTEMS_PRIORITY|RTEMS_INHERIT_PRIORITY,0,&mutex_id));
 mutex=_Semaphore_Get(mutex_id,&location);REQUIRE(location==OBJECTS_LOCAL);_Thread_Enable_dispatch();
 CHECK(rtems_task_create(0x4f574e52,2,8192,RTEMS_TIMESLICE|RTEMS_INTERRUPT_LEVEL(31),RTEMS_DEFAULT_ATTRIBUTES,&owner_id));
 CHECK(rtems_task_create(0x4f544852,2,8192,RTEMS_TIMESLICE|RTEMS_INTERRUPT_LEVEL(31),RTEMS_DEFAULT_ATTRIBUTES,&other_id));
 CHECK(rtems_task_create(0x57414954,2,8192,RTEMS_INTERRUPT_LEVEL(31),RTEMS_DEFAULT_ATTRIBUTES,&waiter_id));
 CHECK(rtems_task_start(owner_id,Worker,0));CHECK(rtems_task_start(other_id,Worker,1));controller=_Thread_Executing->Object.id;
 REQUIRE(REG(0x1328)==0x1fb&&REG(0x1334)==0xff&&!REG(0x1314)&&!REG(0x131c)&&!(REG(0x1324)&2)&&!(REG(0x1330)&2));
 CHECK(start_timer());CHECK(rtems_event_receive(RTEMS_EVENT_0,RTEMS_EVENT_ANY|RTEMS_WAIT,128,&events));
 diag[9]=ticks;REQUIRE(stop_tick&&wait_started&&!wait_done&&waiter&&(waiter->current_state&STATES_WAITING_FOR_MUTEX));
 REQUIRE(mutex->Core_control.mutex.holder_id==owner_id&&resource.refs==1);
 CHECK(own_cancel(&resource,epoch));diag[10]=ticks;ticket=resource.ticket;
 diag[51]=own_complete(&resource,epoch,ticket+1);REQUIRE(diag[51]==OWN_STALE&&resource.refs);
 diag[53]=own_complete(&resource,epoch-1,ticket);REQUIRE(diag[53]==OWN_STALE&&resource.refs);
 diag[54]=rtems_semaphore_release(mutex_id);REQUIRE(diag[54]==RTEMS_NOT_OWNER_OF_RESOURCE&&mutex->Core_control.mutex.holder_id==owner_id);
 if(is_clean()){
  owner_checkpoint=1;
  for(n=0;n<8&&!deferred;n++)CHECK(rtems_task_wake_after(1));REQUIRE(deferred&&resource.refs&&!wait_done&&resource.phase==OWN_CANCEL);
  CHECK(rtems_task_wake_after(2));REQUIRE(resource.refs&&!wait_done&&!resource.acks);
  CHECK(own_complete(&resource,epoch,ticket));diag[11]=ticks;
  diag[52]=own_complete(&resource,epoch,ticket);REQUIRE(diag[52]==OWN_STALE);
  for(n=0;n<8&&(!done[0]||!wait_done);n++)CHECK(rtems_task_wake_after(1));
  REQUIRE(done[0]&&wait_done&&wait_seen==0x10203040&&!mutex->Core_control.mutex.holder&&resource.acks==1);
 }else{
  /* Bounded grace: owner and unrelated task keep running despite STOP. */
  before=progress(0);CHECK(rtems_task_wake_after(4));REQUIRE(progress(0)>0&&progress(0)<before);
  CHECK(own_quarantine(&resource,epoch));CHECK(rtems_task_suspend(owner_id));CHECK(rtems_task_suspend(waiter_id));diag[13]=ticks;
  retained(0);diag[56]=hash(life[0].low,8192);diag[58]=hash((unsigned int)switch_irq_areas[0],8192);
  case_diag[18]=hash((unsigned int)waiter->Start.Initial_stack.area,8192);before=progress(0);
  REQUIRE(own_restart(&resource,epoch)==OWN_STATE&&own_finish(&resource,epoch,0)==OWN_STATE);
  if(mode!=5){CHECK(own_complete(&resource,epoch,ticket));diag[11]=ticks;diag[52]=own_complete(&resource,epoch,ticket);REQUIRE(diag[52]==OWN_STALE);}
  diag[55]=before;
 }
 /* Keep interrupt-driven unrelated work alive after retirement/quarantine. */
 diag[14]=progress(1);CHECK(rtems_task_wake_after(4));other_after=progress(1);REQUIRE(other_after>0&&other_after<diag[14]);
 if(!is_clean()){
  retained(0);diag[57]=hash(life[0].low,8192);diag[59]=hash((unsigned int)switch_irq_areas[0],8192);case_diag[19]=hash((unsigned int)waiter->Start.Initial_stack.area,8192);
  REQUIRE(progress(0)==diag[55]&&diag[56]==diag[57]&&diag[58]==diag[59]&&case_diag[18]==case_diag[19]&&!wait_done);
 }
 CHECK(rtems_task_suspend(other_id));stop_timer();retained(1);diag[15]=progress(1);
 REQUIRE(diag[15]==other_after);
 for(n=0;n<10000;n++){REQUIRE(progress(1)==other_after&&!_ISR_Nest_level&&!_Thread_Dispatch_disable_level&&_Thread_Heir==_Thread_Executing&&!_Context_Switch_necessary);diag[16]++;}
 for(i=0;i<allocated;i++){
  for(j=0;j<16;j++)REQUIRE(stacks[i][j]==0xa5);
  for(j=16+sizes[i];j<8320;j++)REQUIRE(stacks[i][j]==0xa5);
 }
 for(i=0;i<2;i++)for(j=0;j<64;j++)REQUIRE(switch_irq_areas[i][j]==0xa5&&switch_irq_areas[i][8128+j]==0xa5);
 finish_mu();
 diag[0]=0x3149524f;diag[1]=1;diag[2]=switch_fault;diag[3]=mode;diag[4]=epoch;diag[5]=ticks;diag[6]=two_live;diag[7]=handoffs;diag[8]=stop_tick;
 diag[12]=retired_tick;diag[17]=armed;diag[18]=REG(0xff008504);diag[19]=REG(0xff008528);diag[20]=REG(0x3c);diag[21]=saved_vector;
 diag[22]=REG(0xff000310);diag[23]=REG(0xff000314);diag[24]=REG(0xff000318);diag[25]=REG(0xff008500);diag[26]=_ISR_Nest_level;diag[27]=_Thread_Dispatch_disable_level;
 diag[28]=mutex->Core_control.mutex.holder_id;diag[29]=mutex->Core_control.mutex.nest_count;diag[30]=((Thread_Control*)switch_threads[0])->resource_count;diag[31]=waiter->resource_count;
 diag[32]=((Thread_Control*)switch_threads[0])->current_state;diag[33]=waiter->current_state;diag[34]=((Thread_Control*)switch_threads[1])->current_state;
 diag[35]=wait_started;diag[36]=wait_done;diag[37]=wait_seen;diag[38]=resource.acks;diag[39]=deferred;
 /* i960 rounds this 44-byte field list to sizeof=48. Never copy ABI padding. */
 memcpy(diag+40,&resource,11*sizeof(unsigned int));case_diag[0]=mode;case_diag[11]=diag[9];case_diag[12]=0;memcpy(diag+60,(const void*)case_diag,80);
 for(i=0;i<2;i++){unsigned int *s=(unsigned int*)&life[i];for(j=0;j<10;j++)diag[80+i*82+j]=s[j];diag[90+i*82]=(unsigned int)switch_irq_areas[i];diag[91+i*82]=sampled_high[i];for(j=0;j<70;j++)diag[92+i*82+j]=switch_records[i][j];}
 diag[244]=owner_id;diag[245]=waiter_id;diag[246]=other_id;diag[247]=(unsigned int)_Thread_Executing;diag[248]=(unsigned int)_Thread_Heir;
 diag[249]=switch_active[0];diag[250]=switch_active[1];diag[251]=done[0];diag[252]=done[1];diag[255]=0x514f4b31;
 for(i=0;i<256;i++)bio_put((unsigned char*)BIO_BASE+BIO_OUTPUT+i*4,diag[i]);
 bio_put((unsigned char*)BIO_BASE+20,0);bio_put((unsigned char*)BIO_BASE+24,sizeof(diag));bio_put((unsigned char*)BIO_BASE+28,bio_word((unsigned char*)BIO_BASE+8));
 _CPU_Context_switch(&_Thread_Executing->Registers,&_Thread_BSP_context);bounded_fatal(0x94000);
}
static rtems_initialization_tasks_table tasks[]={{0x494e4954,8192,1,RTEMS_DEFAULT_ATTRIBUTES,Init,RTEMS_INTERRUPT_LEVEL(31),0}};
static rtems_api_configuration_table api={4,0,1,0,0,0,0,0,1,tasks};
static rtems_configuration_table config={workspace,sizeof(workspace),0,10000,1,0,0,0,0,0,0,0,&api,0,0};
static rtems_cpu_table cpu={0,0,0,idle_error,1,2048,2048,0,stack_alloc,stack_free};
void _ISR_Handler(void){bounded_fatal(0x40000);}
void _CPU_ISR_install_raw_handler(unsigned int v,proc_ptr n,proc_ptr*o){bounded_fatal(0x40000|v);}
unsigned int bounded_main(unsigned int arg){unsigned char*p=(unsigned char*)arg;
 if(arg!=BIO_BASE||!bio_request_valid(p)||bio_word(p+16)<1024||bio_word(p+12)!=12||bio_word(p+BIO_INPUT)!=0x31505453||initialized)return 1;
 for(p=_bss_start;p<_bss_end;p++)*p=0;
 epoch=bio_word((unsigned char*)BIO_BASE+BIO_INPUT+4);mode=bio_word((unsigned char*)BIO_BASE+BIO_INPUT+8);if(!epoch||epoch>65535||mode<1||mode>5)return 1;
 initialized=1;rtems_initialize_executive(&config,&cpu);return 0;
}

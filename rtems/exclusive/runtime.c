/* Real RTEMS scheduling inside the callback-free parked firmware IRQ.
 * A bounded controller drains both task-owned ISR continuations before return. */
#include <string.h>
#include <rtems/system.h>
#include <rtems/config.h>
#include <rtems/init.h>
#include <rtems/rtems/tasks.h>
#include <rtems/rtems/clock.h>
#include <rtems/rtems/event.h>
#include <rtems/rtems/options.h>
#include <rtems/score/thread.h>
#include <rtems/score/isr.h>
#include "../switch/lifetime.h"
#ifdef I960_RESIDENT_NET
#define EXCLUSIVE_MAX_TICKS 60000u
#else
#define EXCLUSIVE_MAX_TICKS 6000u
#endif
#define R(a) (*(volatile unsigned int*)(a))
extern void exclusive_timer_isr(void);
static unsigned char workspace[49152] __attribute__((aligned(16)));
static unsigned char stacks[4][8320] __attribute__((aligned(16)));
unsigned char switch_irq_areas[2][8192] __attribute__((aligned(16)));
volatile unsigned int switch_threads[2],switch_active[2],switch_fault;
static struct irq_lifetime life[2];
static unsigned int allocated,sizes[4],initialized,limit,handoffs;
static volatile unsigned int ticks,stop,progress[2],done[2],fault;
static Context_Control fatal_context;
static unsigned int resident,resident_epoch,resident_state,stop_reason,snapshot[64],snapshot_id,stop_sent;
static rtems_id controller;
extern void exclusive_engine_report(unsigned int*);
void exclusive_report(unsigned int*);
#ifdef I960_RESIDENT_NET
void bounded_fatal(unsigned int);
#include "../residentnet/net_runtime.h"
#endif
static void control_poll(void){unsigned int token=R(0x1314),index;
 if(!resident||((token&65535)!=resident_epoch))return;
 #ifdef I960_RESIDENT_NET
 if(resident_net_control(token))return;
#endif
 if(token==(0x90000000u|resident_epoch)){
  memset(snapshot,0,sizeof(snapshot));snapshot[0]=0x31525845;snapshot[1]=++snapshot_id;snapshot[2]=resident_state;snapshot[3]=stop_reason;
  exclusive_report(snapshot+4);exclusive_engine_report(snapshot+36);
  snapshot[53]=R(0xff008504);snapshot[54]=R(0x3c);snapshot[55]=(unsigned int)exclusive_timer_isr;snapshot[56]=resident_epoch;
#ifdef I960_RESIDENT_NET
  resident_net_report(snapshot);
#endif
  R(0x1314)=0;R(0x131c)=0x95000000u|resident_epoch;
 }else if((token&0xff000000u)==0x91000000u){
  index=(token>>16)&255;if(index>=64)return;
  R(0x1318)=snapshot[index];(void)R(0x1318);R(0x1314)=0;R(0x131c)=0x92000000u|(index<<16)|resident_epoch;
 }else if(token==(0x93000000u|resident_epoch)){
  R(0x1314)=0;if(resident_state==1){stop_reason=1;stop_sent=1;}
  R(0x131c)=0x94000000u|resident_epoch;
 }
 (void)R(0x131c);R(0x1324)=2;(void)R(0x1324);
}
static void mask(void){unsigned int v=31u<<16;__asm__ volatile("lda 0x1f0000,g0;modpc 0,g0,%0":"+r"(v)::"g0","memory");}
static void enable(void){unsigned int v=20u<<16;__asm__ volatile("lda 0x1f0000,g0;modpc 0,g0,%0":"+r"(v)::"g0","memory");}
void bounded_fatal(unsigned int code){mask();fault=code;R(0xff008504)=0;_CPU_Context_switch(&fatal_context,&_Thread_BSP_context);for(;;){}}
#define CHECK(x) do{unsigned int e=(x);if(e)bounded_fatal(0x10000+__LINE__*256+e);}while(0)
static void*stack_alloc(unsigned int n){unsigned int i=allocated++;if(i>=4||n>8192)bounded_fatal(0x51000);sizes[i]=n;memset(stacks[i],0xa5,8320);return stacks[i]+16;}
static void stack_free(void*p){bounded_fatal(0x51001);}
static void idle_error(void){bounded_fatal(0xdead);}
void switch_irq_enter(unsigned int id,unsigned int fp){if(!lifetime_enter(&life[id],(unsigned int)_Thread_Executing,fp,R(fp-16),R(fp-12),R(fp-8)))switch_fault|=1;}
void switch_irq_body(void){
 _ISR_Nest_level++;_Thread_Dispatch_disable_level++;ticks++;control_poll();if(stop_sent){stop_sent=0;CHECK(rtems_event_send(controller,RTEMS_EVENT_0));}CHECK(rtems_clock_tick());
 _Thread_Dispatch_disable_level--;_ISR_Nest_level--;
 if(_Context_Switch_necessary&&!_Thread_Dispatch_disable_level){if(_Thread_Heir!=_Thread_Executing)handoffs++;_Thread_Dispatch();}
}
void switch_irq_leave(unsigned int id,unsigned int fp){unsigned int j;
 if(!lifetime_leave(&life[id],(unsigned int)_Thread_Executing,fp,R(fp-16),R(fp-12),R(fp-8)))switch_fault|=2;
 for(j=0;j<64;j++)if(switch_irq_areas[id][j]!=0xa5||switch_irq_areas[id][8128+j]!=0xa5)switch_fault|=4;
}
static void Worker(rtems_task_argument id){
 switch_threads[id]=(unsigned int)_Thread_Executing;life[id].owner=switch_threads[id];
 life[id].low=(unsigned int)_Thread_Executing->Start.Initial_stack.area;life[id].high=life[id].low+8192;
 enable();while(!stop){
#ifdef I960_RESIDENT_NET
  if(!id){mask();control_poll();resident_net_step();enable();}
#endif
  progress[id]++;
 }mask();done[id]=1;CHECK(rtems_task_suspend(RTEMS_SELF));bounded_fatal(0x53000);
}
static void Init(rtems_task_argument arg){rtems_id ids[2];rtems_task_priority old;unsigned int i,j;
 memset(switch_irq_areas,0xa5,sizeof(switch_irq_areas));
 for(i=0;i<2;i++){CHECK(rtems_task_create(0x45584330+i,2,8192,RTEMS_TIMESLICE|RTEMS_INTERRUPT_LEVEL(31),RTEMS_DEFAULT_ATTRIBUTES,&ids[i]));CHECK(rtems_task_start(ids[i],Worker,i));}
 #ifdef I960_RESIDENT_NET
 resident_net_init();
#endif
 controller=_Thread_Executing->Object.id;initialized=1;_CPU_Context_switch(&_Thread_Executing->Registers,&_Thread_BSP_context);
 if(resident){rtems_event_set e;unsigned int rc;rtems_status_code status;
  resident_state=1;status=rtems_event_receive(RTEMS_EVENT_0,RTEMS_EVENT_ANY|RTEMS_WAIT,limit,&e);rc=status;
  if(rc==RTEMS_TIMEOUT)stop_reason=2;else if(rc!=RTEMS_SUCCESSFUL)bounded_fatal(0x55000|rc);
 }else CHECK(rtems_task_wake_after(limit));stop=1;
 CHECK(rtems_task_set_priority(RTEMS_SELF,3,&old));mask();
 if(!done[0]||!done[1]||switch_active[0]||switch_active[1]||!lifetime_drained(life))switch_fault|=8;
 if(_ISR_Nest_level||_Thread_Dispatch_disable_level)switch_fault|=16;
 for(i=0;i<allocated;i++){for(j=0;j<16;j++)if(stacks[i][j]!=0xa5)switch_fault|=32;for(j=16+sizes[i];j<8320;j++)if(stacks[i][j]!=0xa5)switch_fault|=32;}
 if(resident){R(0xff008504)=0;resident_state=2;for(;;)control_poll();}
 _CPU_Context_switch(&_Thread_Executing->Registers,&_Thread_BSP_context);bounded_fatal(0x54000);
}
static rtems_initialization_tasks_table tasks[]={{0x494e4954,8192,1,RTEMS_DEFAULT_ATTRIBUTES,Init,RTEMS_INTERRUPT_LEVEL(31),0}};
static rtems_api_configuration_table api={3,0,0,0,0,0,0,0,1,tasks};
static rtems_configuration_table config={workspace,sizeof(workspace),0,10000,1,0,0,0,0,0,0,0,&api,0,0};
static rtems_cpu_table cpu={0,0,0,idle_error,1,2048,2048,0,stack_alloc,stack_free};
void _ISR_Handler(void){bounded_fatal(0x40000);}
void _CPU_ISR_install_raw_handler(unsigned int v,proc_ptr n,proc_ptr*o){bounded_fatal(0x40000|v);}
unsigned int exclusive_init(void){rtems_initialize_executive(&config,&cpu);return fault;}
unsigned int exclusive_run(unsigned int n){unsigned int vector=R(0x3c),mask_before=R(0xff008504);
 if(!initialized||ticks||fault||!n||n>EXCLUSIVE_MAX_TICKS)return 1;limit=n;
 R(0xff008504)=0;R(0x3c)=(unsigned int)exclusive_timer_isr;R(0xff008504)=0x2000;
 _CPU_Context_switch(&_Thread_BSP_context,&_Thread_Executing->Registers);mask();
 R(0xff008504)=0;R(0x3c)=vector;R(0xff008504)=mask_before;
 return fault|switch_fault;
}
void exclusive_report(unsigned int*w){unsigned int i;
 w[0]=fault;w[1]=ticks;w[2]=progress[0];w[3]=progress[1];w[4]=done[0];w[5]=done[1];w[6]=handoffs;w[7]=switch_fault;
 w[8]=life[0].entries;w[9]=life[0].returns;w[10]=life[1].entries;w[11]=life[1].returns;
 for(i=0;i<2;i++){unsigned int j,*p=(unsigned int*)&life[i];for(j=0;j<10;j++)w[12+i*10+j]=p[j];}
}

void exclusive_resident(unsigned int n,unsigned int epoch){
 if(!initialized||ticks||fault||!n||n>EXCLUSIVE_MAX_TICKS)for(;;){}
 resident=1;resident_epoch=epoch;limit=n;
 R(0xff008504)=0;R(0x3c)=(unsigned int)exclusive_timer_isr;R(0xff008504)=0x2000;
 _CPU_Context_switch(&_Thread_BSP_context,&_Thread_Executing->Registers);
 /* Failure quarantine: never return to firmware, even if fatal context escapes. */
 mask();R(0xff008504)=0;resident_state=3;for(;;)control_poll();
}

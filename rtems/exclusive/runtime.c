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
#ifdef I960_OWNED_MIB
#define EXCLUSIVE_MAX_TICKS 360000u
#else
#define EXCLUSIVE_MAX_TICKS 180000u
#endif
#else
#define EXCLUSIVE_MAX_TICKS 6000u
#endif
#define R(a) (*(volatile unsigned int*)(a))
extern void exclusive_timer_isr(void);
#ifdef I960_OWNED_MIB
#include "../residentnet/large_ram.h"
#ifdef I960_RESIDENT_UPLOAD
#include "../residentnet/upload.h"
#include "../residentnet/doom_heap_shared.h"
#endif
#define workspace ((unsigned char*)LARGE_WORKSPACE)
#define WORKSPACE_BYTES 262144u
#define TASK_BYTES 65536u
#define STACK_BYTES (TASK_BYTES+128u)
#define stacks ((unsigned char (*)[STACK_BYTES])LARGE_STACKS)
#else
#define WORKSPACE_BYTES 49152u
#define TASK_BYTES 8192u
#define STACK_BYTES 8320u
static unsigned char workspace[WORKSPACE_BYTES] __attribute__((aligned(16)));
static unsigned char stacks[4][STACK_BYTES] __attribute__((aligned(16)));
#endif
unsigned char switch_irq_areas[2][8192] __attribute__((aligned(16)));
volatile unsigned int switch_threads[2],switch_active[2],switch_fault;
static struct irq_lifetime life[2];
static unsigned int allocated,sizes[4],initialized,limit,handoffs;
static volatile unsigned int ticks,stop,progress[2],done[2],fault;
static Context_Control fatal_context;
static unsigned int resident,resident_epoch,resident_state,stop_reason,snapshot[64],snapshot_id,stop_sent;
static rtems_id controller;
#ifdef I960_RESIDENT_UPLOAD
unsigned int upload_stopping(void){return stop||stop_sent||resident_state!=1;}
unsigned int upload_time(void){return ticks;}
#endif
extern void exclusive_engine_report(unsigned int*);
void exclusive_report(unsigned int*);
#ifdef I960_RESIDENT_NET
void bounded_fatal(unsigned int);
static void mask(void),enable(void);
#include "../residentnet/net_runtime.h"
#endif
static void control_poll(void){unsigned int token=R(0x1314),index;
 if(!resident||((token&65535)!=resident_epoch))return;
 #ifdef I960_RESIDENT_NET
#ifdef I960_RESIDENT_UPLOAD
 if((token>>24)>=0x70&&(token>>24)<=0x74){
  R(0x1318)=upload_control(token>>24,(token>>16)&255,R(0x1310),resident_state==1);(void)R(0x1318);
  R(0x1314)=0;R(0x131c)=token|0x08000000u;(void)R(0x131c);R(0x1324)=2;(void)R(0x1324);return;
 }
#endif
 if(resident_net_control(token))return;
#endif
#ifdef I960_OWNED_MIB
 if(token==(0x98000000u|resident_epoch)){
  exclusive_large_report(snapshot);R(0x1314)=0;R(0x131c)=0x99000000u|resident_epoch;
  (void)R(0x131c);R(0x1324)=2;(void)R(0x1324);return;
 }
#endif
#ifdef I960_HEAP_SHARED
 if(token==(0x96000000u|resident_epoch)){
  resident_heap_diagnostics(snapshot);R(0x1314)=0;R(0x131c)=0x97000000u|resident_epoch;
  (void)R(0x131c);R(0x1324)=2;(void)R(0x1324);return;
 }
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
#ifdef I960_OWNED_MIB
void exclusive_drain_poll(void){
 if(!done[0]||!done[1]||switch_active[0]||switch_active[1])bounded_fatal(0x57005);
 control_poll();
}
#endif
static void mask(void){unsigned int v=31u<<16;__asm__ volatile("lda 0x1f0000,g0;modpc 0,g0,%0":"+r"(v)::"g0","memory");}
static void enable(void){unsigned int v=20u<<16;__asm__ volatile("lda 0x1f0000,g0;modpc 0,g0,%0":"+r"(v)::"g0","memory");}
void bounded_fatal(unsigned int code){mask();fault=code;R(0xff008504)=0;_CPU_Context_switch(&fatal_context,&_Thread_BSP_context);for(;;){}}
#define CHECK(x) do{unsigned int e=(x);if(e)bounded_fatal(0x10000+__LINE__*256+e);}while(0)
static void*stack_alloc(unsigned int n){unsigned int i=allocated++;if(i>=4||n>TASK_BYTES)bounded_fatal(0x51000);sizes[i]=n;memset(stacks[i],0xa5,STACK_BYTES);return stacks[i]+16;}
static void stack_free(void*p){bounded_fatal(0x51001);}
static void idle_error(void){bounded_fatal(0xdead);}
void switch_irq_enter(unsigned int id,unsigned int fp){if(!lifetime_enter(&life[id],(unsigned int)_Thread_Executing,fp,R(fp-16),R(fp-12),R(fp-8)))switch_fault|=1;}
void switch_irq_body(void){
#ifdef I960_HEAP_SHARED
 resident_heap_irq_sample();
#endif
 _ISR_Nest_level++;_Thread_Dispatch_disable_level++;ticks++;control_poll();if(stop_sent){stop_sent=0;CHECK(rtems_event_send(controller,RTEMS_EVENT_0));}CHECK(rtems_clock_tick());
 _Thread_Dispatch_disable_level--;_ISR_Nest_level--;
 if(_Context_Switch_necessary&&!_Thread_Dispatch_disable_level){if(_Thread_Heir!=_Thread_Executing)handoffs++;_Thread_Dispatch();}
}
void switch_irq_leave(unsigned int id,unsigned int fp){unsigned int j;
 if(!lifetime_leave(&life[id],(unsigned int)_Thread_Executing,fp,R(fp-16),R(fp-12),R(fp-8)))switch_fault|=2;
 for(j=0;j<64;j++)if(switch_irq_areas[id][j]!=0xa5||switch_irq_areas[id][8128+j]!=0xa5)switch_fault|=4;
}
#ifdef I960_FAULT_OWNER
extern void exclusive_fault_inject(void);
#endif
#ifdef I960_GENERAL_HEAP
#include "../residentnet/general_heap.h"
#endif
#ifdef I960_OWNED_MIB
#include <rtems/score/wkspace.h>
static unsigned int stack_checks[2],workspace_checked,workspace_freed;
static unsigned int*workspace_proof;
static unsigned int workspace_proof_address;

void exclusive_stack_report(unsigned int*w){unsigned int i;w[0]=allocated;for(i=0;i<4;i++)w[1+i]=sizes[i];w[5]=stack_checks[0];w[6]=stack_checks[1];w[8]=workspace_proof_address;w[9]=131072;w[10]=workspace_checked;w[11]=workspace_freed;}
#endif
static void Worker(rtems_task_argument id){
#ifdef I960_OWNED_MIB
 volatile unsigned char proof[12288];unsigned int pi,last_proof=~0u;
 for(pi=0;pi<sizeof(proof);pi++)proof[pi]=(unsigned char)(pi^id);
#endif
 switch_threads[id]=(unsigned int)_Thread_Executing;life[id].owner=switch_threads[id];
 life[id].low=(unsigned int)_Thread_Executing->Start.Initial_stack.area;life[id].high=life[id].low+TASK_BYTES;
 enable();while(!stop){
#ifdef I960_OWNED_MIB
  /* Both runnable workers service the same serialized PIO channel. A CPU-bound
   * heap worker must not force every host word to wait for the next timer IRQ. */
  if(id){mask();control_poll();enable();}
#endif
#ifdef I960_RESIDENT_NET
  if(!id){mask();control_poll();
#ifdef I960_QUEUE_RECLAIM
   enable();resident_net_step();
#else
   resident_net_step();enable();
#endif
  }
#endif
#ifdef I960_FAULT_OWNER
  if(resident&&!id&&ticks>=100)exclusive_fault_inject();
#endif
#ifdef I960_GENERAL_HEAP
  if(resident){resident_heap_step(id,ticks);if(!id&&ticks>=100)resident_heap_inject();}
#endif
#ifdef I960_OWNED_MIB
  if(ticks/100!=last_proof){last_proof=ticks/100;for(pi=0;pi<sizeof(proof);pi++)if(proof[pi]!=(unsigned char)(pi^id))bounded_fatal(0x57001);stack_checks[id]++;}
#endif
#ifdef I960_RESIDENT_UPLOAD
  if(id)upload_step();
#ifdef I960_DOOM_SHARED
  else doom_shared_peer_step();
#endif
#endif
  progress[id]++;
 }mask();
#ifdef I960_GENERAL_HEAP
 if(resident)resident_heap_drain(id);
#endif
 done[id]=1;CHECK(rtems_task_suspend(RTEMS_SELF));bounded_fatal(0x53000);
}
static void Init(rtems_task_argument arg){rtems_id ids[2];rtems_task_priority old;unsigned int i,j;
 memset(switch_irq_areas,0xa5,sizeof(switch_irq_areas));
#ifdef I960_DOOM_SHARED
 doom_shared_init();
#endif
 for(i=0;i<2;i++){CHECK(rtems_task_create(0x45584330+i,2,TASK_BYTES,RTEMS_TIMESLICE|RTEMS_INTERRUPT_LEVEL(31),RTEMS_DEFAULT_ATTRIBUTES,&ids[i]));CHECK(rtems_task_start(ids[i],Worker,i));}
 #ifdef I960_RESIDENT_NET
 resident_net_init();
#endif
#ifdef I960_OWNED_MIB
 workspace_proof=_Workspace_Allocate(131072);workspace_proof_address=(unsigned int)workspace_proof;
 if(workspace_proof_address<LARGE_WORKSPACE||workspace_proof_address>LARGE_WORKSPACE+WORKSPACE_BYTES-131072)bounded_fatal(0x57002);
 for(i=0;i<32768;i++)workspace_proof[i]=i^0x574b5350u;
#endif
 controller=_Thread_Executing->Object.id;initialized=1;_CPU_Context_switch(&_Thread_Executing->Registers,&_Thread_BSP_context);
 if(resident){rtems_event_set e;unsigned int rc;rtems_status_code status;
  resident_state=1;status=rtems_event_receive(RTEMS_EVENT_0,RTEMS_EVENT_ANY|RTEMS_WAIT,limit,&e);rc=status;
  if(rc==RTEMS_TIMEOUT)stop_reason=2;else if(rc!=RTEMS_SUCCESSFUL)bounded_fatal(0x55000|rc);
 }else CHECK(rtems_task_wake_after(limit));stop=1;
 CHECK(rtems_task_set_priority(RTEMS_SELF,3,&old));mask();
 if(!done[0]||!done[1]||switch_active[0]||switch_active[1]||!lifetime_drained(life))switch_fault|=8;
 if(_ISR_Nest_level||_Thread_Dispatch_disable_level)switch_fault|=16;
 for(i=0;i<allocated;i++){for(j=0;j<16;j++)if(stacks[i][j]!=0xa5)switch_fault|=32;for(j=16+sizes[i];j<STACK_BYTES;j++){
#ifdef I960_OWNED_MIB
 if(!(j&1023))exclusive_drain_poll();
#endif
 if(stacks[i][j]!=0xa5)switch_fault|=32;}}
 #ifdef I960_OWNED_MIB
 for(i=0;i<32768;i++){if(!(i&1023))exclusive_drain_poll();if(workspace_proof[i]!=(i^0x574b5350u))bounded_fatal(0x57003);}
 #ifdef I960_DOOM_SHARED
 doom_shared_quiesce(!switch_fault&&done[0]&&done[1]&&!switch_active[0]&&!switch_active[1]&&lifetime_drained(life)&&!_ISR_Nest_level&&!_Thread_Dispatch_disable_level);
#endif
 if(!exclusive_large_finish()){switch_fault|=64;exclusive_abort();}
 workspace_checked=131072;
 if(!_Workspace_Free(workspace_proof))bounded_fatal(0x57004);workspace_freed=1;workspace_proof=0;
#endif
 if(resident){R(0xff008504)=0;resident_state=2;for(;;)control_poll();}
 _CPU_Context_switch(&_Thread_Executing->Registers,&_Thread_BSP_context);bounded_fatal(0x54000);
}
static rtems_initialization_tasks_table tasks[]={{0x494e4954,TASK_BYTES,1,RTEMS_DEFAULT_ATTRIBUTES,Init,RTEMS_INTERRUPT_LEVEL(31),0}};
#ifdef I960_DOOM_SHARED
#define ARENA_MUTEXES 1
#else
#define ARENA_MUTEXES 0
#endif
static rtems_api_configuration_table api={3,0,ARENA_MUTEXES,0,0,0,0,0,1,tasks};
static rtems_configuration_table config={workspace,WORKSPACE_BYTES,0,10000,1,0,0,0,0,0,0,0,&api,0,0};
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

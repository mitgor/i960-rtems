/* AcceleRAID 160: bounded STOP-ignoring two-worker RTEMS containment. */
#include <rtems/system.h>
#include <rtems/rtems/tasks.h>
#include <rtems/rtems/clock.h>
#include <rtems/config.h>
#include <rtems/init.h>
#include <rtems/score/context.h>
#include <rtems/score/thread.h>
#include <rtems/score/isr.h>
#include <stddef.h>
#include "lifetime.h"
extern unsigned char _bss_start[],_bss_end[],switch_irq_areas[3][8192];
extern void bounded_escape(unsigned int) __attribute__((noreturn));
extern void lease_invalidate_dcache(void),timer_isr(void);
#define REG(a) (*(volatile unsigned int *)(a))
#define STOP 0x504f5453u
#define TIME 0x454d4954u
static unsigned char workspace[49152] __attribute__((aligned(16)));
static volatile unsigned int done[2],stop_seen,deadline,loops[2],result;
static volatile unsigned int ticks,irq_sp[3],handoffs,two_live;
volatile unsigned int switch_threads[3],switch_active[3],switch_fault,switch_stop;
static struct irq_lifetime life[3];
static unsigned int saved_mask,saved_map,saved_vector,saved_reload,saved_count;
static volatile unsigned int armed,restoration;
static rtems_id worker_id[2];
static volatile unsigned int * const control=(volatile unsigned int *)0xc000fa40u;
typedef char context_pc_offset[(offsetof(Context_Control,pc)==8)?1:-1];
typedef char context_g8_offset[(offsetof(Context_Control,g8)==12)?1:-1];
static void mask31(void){unsigned int level=31u<<16;
 __asm__ volatile("lda 0x1f0000,g0; modpc 0,g0,%0":"+r"(level)::"g0","memory");
}
static void priority0(void){unsigned int level=0u;
 __asm__ volatile("lda 0x1f0000,g0; modpc 0,g0,%0":"+r"(level)::"g0","memory");
}
static void clear_tip1(void){unsigned int old=0;
 __asm__ volatile("lda 0xff008500,g0; lda 0x2000,g1; atmod g0,g1,%0"
                  :"+r"(old)::"g0","g1","memory");
}
static unsigned int preflight(void){
 REG(0xc000fa70u)=REG(0xff008500u);
 REG(0xc000fa74u)=REG(0xff008504u);
 REG(0xc000fa78u)=REG(0xff008528u);
 if(REG(0xff008510u)!=0x6000u)return 1u;
 if(REG(0xff008520u)!=0x4444u)return 2u;
 if(REG(0xff008524u)!=0x6754u)return 3u;
 if(REG(0xff008528u)!=0x80000u)return 4u;
 if(REG(0xff008504u)!=0x10c7u)return 5u;
 /* Stock timer 0 can be pending while RTEMS starts at priority 31. Only
  * timer 1 (our borrowed source) must be clear. Preserve other pending bits. */
 if(REG(0xff008500u)&0x2000u)return 6u;
 if(REG(0xff000310u)!=0u)return 7u;
 if(REG(0xff000314u)!=0u)return 8u;
 if(REG(0x4u)!=0xaaaaaaaau)return 9u;
 if(REG(0x20u)!=0xc0000418u)return 10u;
 if(REG(0x3cu)!=0xe0000ff0u)return 11u;
 if(REG(0xff000318u)!=0u)return 12u;
 if(REG(0xff000310u)!=0u)return 13u;
 if(REG(0xff000314u)!=0u)return 14u;
 if(REG(0xff008500u)&0x2000u)return 15u;
 if(REG(0xff008504u)!=0x10c7u)return 16u;
 if(REG(0xff008528u)!=0x80000u)return 17u;
 if(REG(0x4u)!=0xaaaaaaaau)return 18u;
 return 0u;
}
static void stop_timer(void){
 if(!armed)return;
 mask31();
 REG(0xff008504u)=0u;
 REG(0xff000318u)=0u;
 clear_tip1();
 REG(0xff008528u)=saved_map;
 REG(0x4u)=saved_vector;
 REG(0xff000310u)=saved_reload;
 REG(0xff000314u)=saved_count;
 REG(0xff008504u)=saved_mask;
 armed=0u;
 restoration=(REG(0xff008504u)==saved_mask &&
              REG(0xff008528u)==saved_map && REG(0x4u)==saved_vector &&
              REG(0xff000310u)==saved_reload &&
              REG(0xff000314u)==saved_count &&
              !(REG(0xff008500u)&0x2000u) &&
              REG(0xff000318u)==0u);
}
void bounded_fatal(unsigned int code){stop_timer();bounded_escape(0xf0000000u|code);}
#define CHECK(x) do {unsigned int e=(x);if(e)bounded_fatal(0x10000u+__LINE__*256u+e);}while(0)
#define ASSERT(x) do {if(!(x))bounded_fatal(0x20000u+__LINE__);}while(0)

static void measure(unsigned int id){unsigned int sp,base=(unsigned int)switch_irq_areas[id];
 __asm__ volatile("mov sp,%0":"=r"(sp));irq_sp[id]=sp;
 if(sp<base+192u||sp>=base+8128u)switch_fault|=1u;
}
void switch_irq_enter(unsigned int id,unsigned int frame){
 measure(id);
 if(!lifetime_enter(&life[id],(unsigned int)_Thread_Executing,frame,
                    REG(frame-16),REG(frame-12),REG(frame-8)))switch_fault|=2u;
 if(life[1].live&&life[2].live)two_live++;
}
void switch_irq_body(void){
 _ISR_Nest_level++;_Thread_Dispatch_disable_level++;
 ticks++;
 if(rtems_clock_tick())switch_fault|=8u;
 _Thread_Dispatch_disable_level--;_ISR_Nest_level--;
 if(_Context_Switch_necessary&&!_Thread_Dispatch_disable_level){
  if(_Thread_Heir!=_Thread_Executing)handoffs++;
  _Thread_Dispatch(); /* Can remain suspended on this owner's ISR stack. */
 }
}
void switch_irq_leave(unsigned int id,unsigned int frame){unsigned int i,tc,*save;
 measure(id);
 if(!lifetime_leave(&life[id],(unsigned int)_Thread_Executing,frame,
                    REG(frame-16),REG(frame-12),REG(frame-8)))switch_fault|=4u;
 for(i=0;i<64;i++)if(switch_irq_areas[id][i]!=0xa5u||
                        switch_irq_areas[id][8128+i]!=0xa5u)switch_fault|=16u;
 save=(unsigned int*)(switch_irq_areas[id]+64);
 __asm__ volatile("modtc 0,0,%0":"=r"(tc));
 if((tc^save[16])&0x0f000000u)switch_fault|=32u;
}
static void arm_timer(void){unsigned int error=preflight();
 REG(0xc000fa64u)=error;
 if(error)bounded_fatal(0x50000u|error);
 saved_mask=REG(0xff008504u);
 saved_map=REG(0xff008528u);
 saved_vector=REG(0x4u);
 saved_reload=REG(0xff000310u);
 saved_count=REG(0xff000314u);
 mask31();
 REG(0xff008504u)=0u;
 REG(0x4u)=(unsigned int)timer_isr;
 REG(0xff008528u)=0x00180000u;
 /* 100 MHz / 8 / 125000 = 100 Hz, matching RTEMS 10000 us/tick. */
 REG(0xff000310u)=125000u;
 REG(0xff000314u)=125000u;
 REG(0xff008504u)=0x2000u;
 armed=1u;
 REG(0xff000318u)=0x36u;
}

static unsigned int contain_hash(unsigned int base,unsigned int size){
 unsigned int h=2166136261u,i;
 for(i=0;i<size;i++)h=(h^*(volatile unsigned char*)(base+i))*16777619u;
 return h;
}
static void Worker(rtems_task_argument id){unsigned int i,old;
 switch_threads[id+1]=(unsigned int)_Thread_Executing;
 life[id+1].owner=switch_threads[id+1];
 life[id+1].low=(unsigned int)_Thread_Executing->Start.Initial_stack.area;
 life[id+1].high=life[id+1].low+_Thread_Executing->Start.Initial_stack.size;
 CHECK(rtems_task_mode(RTEMS_INTERRUPT_LEVEL(0),RTEMS_INTERRUPT_MASK,&old));
 priority0();
 /* Deliberately never read STOP or switch_stop, yield, or call RTEMS. */
 for(i=0;i<100000000u;i++){
  loops[id]=i;
  __asm__ volatile("":::"memory");
 }
 switch_fault|=0x100u;done[id]=1u;
 CHECK(rtems_task_suspend(RTEMS_SELF));
 bounded_fatal(0x30001u+id);
}
static void Init(rtems_task_argument nonce){rtems_task_priority old;
 unsigned int i,j,at_stop[2],at_suspend[2],stack_hash[2],irq_hash[2];
 Thread_Control *t[2];
 (void)nonce;
 for(i=0;i<sizeof(switch_irq_areas);i++)((unsigned char*)switch_irq_areas)[i]=0xa5;
 switch_threads[0]=(unsigned int)_Thread_Executing;
 life[0].owner=switch_threads[0];
 life[0].low=(unsigned int)_Thread_Executing->Start.Initial_stack.area;
 life[0].high=life[0].low+_Thread_Executing->Start.Initial_stack.size;
 CHECK(rtems_task_create(0x574b5230u,2,8192,RTEMS_TIMESLICE|RTEMS_INTERRUPT_LEVEL(31),
                         RTEMS_DEFAULT_ATTRIBUTES,&worker_id[0]));
 CHECK(rtems_task_create(0x574b5231u,2,8192,RTEMS_TIMESLICE|RTEMS_INTERRUPT_LEVEL(31),
                         RTEMS_DEFAULT_ATTRIBUTES,&worker_id[1]));
 CHECK(rtems_task_start(worker_id[0],Worker,0));
 CHECK(rtems_task_start(worker_id[1],Worker,1));
 arm_timer();priority0();
 for(i=0;i<60u;i++){
  CHECK(rtems_task_wake_after(2));priority0();
  lease_invalidate_dcache();
  if(ticks>=6u&&handoffs>=2u&&life[1].entries&&life[2].entries)
   control[4]=0x59444152u;
  if(control[3]==STOP){
   if(control[0]!=0x3145534cu||control[1]!=0x161610d1u||control[2]!=1u)
    switch_fault|=0x200u;
   else {stop_seen=1u;break;}
  }
  if(switch_fault)break;
 }
 deadline=i;
 if(!stop_seen&&i==60u)control[4]=TIME;
 at_stop[0]=loops[0];at_stop[1]=loops[1];
 /* Both workers ignore STOP: show four more timer ticks of progress. */
 CHECK(rtems_task_wake_after(4));priority0();
 at_suspend[0]=loops[0];at_suspend[1]=loops[1];
 if(at_suspend[0]<=at_stop[0]||at_suspend[1]<=at_stop[1])
  switch_fault|=0x400u;
 CHECK(rtems_task_suspend(worker_id[0]));
 CHECK(rtems_task_suspend(worker_id[1]));
 mask31();stop_timer();
 t[0]=(Thread_Control*)switch_threads[1];
 t[1]=(Thread_Control*)switch_threads[2];
 if(!t[0]||!t[1]||done[0]||done[1]||
    switch_active[0]||!switch_active[1]||!switch_active[2]||
    !life[1].live||!life[2].live||
    life[1].entries!=life[1].returns+1u||
    life[2].entries!=life[2].returns+1u||
    _ISR_Nest_level||_Thread_Dispatch_disable_level||
    _Thread_Heir!=_Thread_Executing||_Context_Switch_necessary)
  switch_fault|=0x800u;
 for(i=0;i<2;i++){
  if(t[i] && (t[i]->current_state!=STATES_SUSPENDED||t[i]->suspend_count!=1u))
   switch_fault|=0x1000u;
  if(life[i+1].frame<life[i+1].low+16u||
     life[i+1].frame>life[i+1].high-64u||
     REG(life[i+1].frame-16)!=life[i+1].pc||
     REG(life[i+1].frame-12)!=life[i+1].ac||
     REG(life[i+1].frame-8)!=life[i+1].vector||life[i+1].vector!=0x12u)
   switch_fault|=0x2000u;
  for(j=0;j<64;j++)if(switch_irq_areas[i+1][j]!=0xa5u||
                        switch_irq_areas[i+1][8128+j]!=0xa5u)
   switch_fault|=0x4000u;
  stack_hash[i]=contain_hash(life[i+1].low,life[i+1].high-life[i+1].low);
  irq_hash[i]=contain_hash((unsigned int)switch_irq_areas[i+1],8192);
 }
 for(i=0;i<10000u;i++){
  if(loops[0]!=at_suspend[0]||loops[1]!=at_suspend[1]||
     t[0]->current_state!=STATES_SUSPENDED||
     t[1]->current_state!=STATES_SUSPENDED||
     t[0]->suspend_count!=1u||t[1]->suspend_count!=1u||
     (unsigned int)_Thread_Executing!=switch_threads[0]||
     _Thread_Heir!=_Thread_Executing||_Context_Switch_necessary||
     _ISR_Nest_level||_Thread_Dispatch_disable_level)
   switch_fault|=0x8000u;
 }
 for(i=0;i<2;i++)
  if(stack_hash[i]!=contain_hash(life[i+1].low,life[i+1].high-life[i+1].low)||
     irq_hash[i]!=contain_hash((unsigned int)switch_irq_areas[i+1],8192))
   switch_fault|=0x10000u;
 if(!restoration||switch_fault||ticks<10u||handoffs<2u||!two_live)
  bounded_fatal(0x61000u|switch_fault);
 {volatile unsigned int *trace=(volatile unsigned int*)(switch_irq_areas[0]+4096);
  trace[0]=0x324e5443u;trace[1]=ticks;trace[2]=handoffs;trace[3]=two_live;
  trace[4]=at_stop[0];trace[5]=at_stop[1];
  trace[6]=at_suspend[0];trace[7]=at_suspend[1];
  trace[8]=loops[0];trace[9]=loops[1];trace[10]=deadline;
  trace[11]=life[1].entries;trace[12]=life[1].returns;
  trace[13]=life[2].entries;trace[14]=life[2].returns;
  trace[15]=switch_active[1];trace[16]=switch_active[2];
  trace[17]=t[0]->current_state;trace[18]=t[1]->current_state;
  trace[19]=t[0]->suspend_count;trace[20]=t[1]->suspend_count;
  trace[21]=life[1].frame;trace[22]=life[2].frame;
  trace[23]=life[1].vector;trace[24]=life[2].vector;
  trace[25]=10000u;trace[26]=stack_hash[0];trace[27]=stack_hash[1];
  trace[28]=irq_hash[0];trace[29]=irq_hash[1];
  trace[30]=switch_fault;trace[31]=restoration;
 }
 if(stop_seen){control[5]=0x214b4341u;control[6]=0x161610d1u;control[7]=1u;}
 result=stop_seen?STOP:TIME;
 rtems_shutdown_executive(0);
}
static rtems_initialization_tasks_table tasks[]={{0x494e4954,4096,1,
 RTEMS_DEFAULT_ATTRIBUTES,Init,RTEMS_INTERRUPT_LEVEL(31),0}};
static rtems_api_configuration_table api={4,0,2,0,0,0,0,0,1,tasks};
static rtems_configuration_table config={workspace,sizeof(workspace),0,
 10000,1,0,0,0,0,0,0,0,&api,0,0};
static rtems_cpu_table cpu={0,0,0,0,1,2048,2048,0,0,0};
void _ISR_Handler(void){bounded_fatal(0x40000u);}
void _CPU_ISR_install_raw_handler(unsigned int v,proc_ptr n,proc_ptr*o){
 bounded_fatal(0x40000u|v);
}
unsigned int bounded_main(unsigned int report_addr,unsigned int nonce){
 volatile unsigned int *report=(volatile unsigned int *)report_addr;
 unsigned char *p;
 if(report_addr!=0xc000fa20u||nonce!=0x161610d1u)return 0xbad00001u;
 for(p=_bss_start;p<_bss_end;p++)*p=0;
 if(control[0]!=0x3145534cu||control[1]!=nonce||
    control[2]!=1u||control[3]!=0)return 0xbad00002u;
 rtems_initialize_executive(&config,&cpu);
 if(done[0]||done[1]||!restoration||switch_fault||
    result!=(stop_seen?STOP:TIME))return 0xbad00003u;
 report[0]=0x314e5552u;
 report[1]=nonce;
 report[2]=0x31454e4fu;
 report[6]=result;
 REG(0xc000fa70u)=ticks;
 REG(0xc000fa74u)=switch_active[1]|(switch_active[2]<<1);
 REG(0xc000fa78u)=handoffs;
 REG(0xc000fa7cu)=restoration;
 return 0;
}

/* Finite two-task RTEMS lease after stock operation 13 returns.
 * The worker owns work; Init supervises its drain and whole-instance exit. */
#include <rtems/system.h>
#include <rtems/rtems/tasks.h>
#include <rtems/rtems/timer.h>
#include <rtems/rtems/clock.h>
#include <rtems/config.h>
#include <rtems/init.h>
#include <rtems/score/thread.h>
#include <rtems/score/isr.h>
extern unsigned char _bss_start[],_bss_end[],irq_owned_area[];
extern void timer_isr(void),timer_invalidate_dcache(void);
extern unsigned int escape_context[];
extern void bounded_escape(unsigned int) __attribute__((noreturn));
#define REG(a) (*(volatile unsigned int *)(a))
#define ENTER 0x52544e45u
#define HALT  0x544c4148u
#define ACTIVE 0x49544341u
#define HALTED 0x544c4148u
#define EXPIRED 0x45505845u
#define MAX_TICKS 300u
volatile unsigned int irq_active[2],irq_fault,resident_phase;
static volatile unsigned int ticks,entries,entered_ticks,irq_sp[2],frame,frame_pc,frame_ac,frame_vector;
static volatile unsigned int clock_fired,clock_tick,clock_after_enter;
static volatile unsigned int task_started,task_done,task_progress,task_sp;
static volatile unsigned int task_thread,task_stack_low,task_stack_high;
static volatile unsigned int task_irq_count,stop_tick,task_result,dispatch_task_base;
static volatile unsigned int worker_started,worker_done,worker_progress,worker_sp;
static volatile unsigned int worker_thread,worker_stack_low,worker_stack_high;
static volatile unsigned int worker_irq_count,worker_result,worker_id_word;
static unsigned char workspace[36864] __attribute__((aligned(16)));
static rtems_id clock_id,worker_id,init_id;
static rtems_interrupt_level bsp_level;
static void Init(rtems_task_argument nonce);
static void Worker(rtems_task_argument nonce);
static rtems_initialization_tasks_table tasks[]={{0x494e4954u,4096,3,
 RTEMS_DEFAULT_ATTRIBUTES,Init,RTEMS_INTERRUPT_LEVEL(0),0}};
static rtems_api_configuration_table api={2,1,0,0,0,0,0,0,1,tasks};
static rtems_configuration_table config={workspace,sizeof(workspace),0,
 10000,1,0,0,0,0,0,0,0,&api,0,0};
static rtems_cpu_table cpu={0,0,0,0,1,2048,2048,0,0,0};
static unsigned int saved_mask,saved_map,saved_vector,saved_reload,saved_count,saved_pc;
static volatile unsigned int armed,restoration,state;
static volatile unsigned int * const side=(volatile unsigned int *)0xc000fa40u;
static volatile unsigned int * const diag=(volatile unsigned int *)0xc000fa60u;
void bounded_fatal(unsigned int code){
 diag[7]=0xf0000000u|code;
 if(resident_phase){irq_fault|=0x80000000u;return;}
 bounded_escape(0xf0000000u|code);
}
void _ISR_Handler(void){irq_fault|=0x100u;}
void _CPU_ISR_install_raw_handler(unsigned int v,proc_ptr n,proc_ptr*o){
 (void)v;(void)n;(void)o;irq_fault|=0x200u;
}
static void clock_callback(rtems_id id,void *arg){
 (void)arg;
 if(id!=clock_id||clock_fired)irq_fault|=0x400u;
 clock_tick=ticks;clock_fired=1u;
 clock_after_enter=(entries&&frame>=0xc0000100u&&frame<0xc0710000u);
 if(!clock_after_enter)irq_fault|=0x800u;
}
static void mask31(void){unsigned int level=31u<<16;
 __asm__ volatile("lda 0x1f0000,g0; modpc 0,g0,%0":"+r"(level)::"g0","memory");
}
static void clear_tip1(void){unsigned int old=0;
 __asm__ volatile("lda 0xff008500,g0; lda 0x2000,g1; atmod g0,g1,%0"
                  :"+r"(old)::"g0","g1","memory");
}
static unsigned int preflight(void){
 if(REG(0xff008510u)!=0x6000u||REG(0xff008520u)!=0x4444u||
    REG(0xff008524u)!=0x6754u||REG(0xff008528u)!=0x80000u||
    REG(0xff008504u)!=0x10c7u||(REG(0xff008500u)&0x2000u))return 1u;
 if(REG(0xff000310u)||REG(0xff000314u)||REG(0x4u)!=0xaaaaaaaau||
    REG(0x20u)!=0xc0000418u||REG(0x3cu)!=0xe0000ff0u)return 2u;
 if(REG(0xff000318u))return 3u;
 if(REG(0xff000310u)||REG(0xff000314u)||
    (REG(0xff008500u)&0x2000u)||REG(0xff008504u)!=0x10c7u||
    REG(0xff008528u)!=0x80000u||REG(0x4u)!=0xaaaaaaaau)return 4u;
 return 0u;
}
static void stop_timer(void){
 if(!armed)return;
 mask31();REG(0xff008504u)=0;REG(0xff000318u)=0;clear_tip1();
 REG(0xff008528u)=saved_map;REG(0x4u)=saved_vector;
 REG(0xff000310u)=saved_reload;REG(0xff000314u)=saved_count;
 REG(0xff008504u)=saved_mask;armed=0;
 restoration=(REG(0xff008504u)==saved_mask&&
              REG(0xff008528u)==saved_map&&REG(0x4u)==saved_vector&&
              REG(0xff000310u)==saved_reload&&
              REG(0xff000314u)==saved_count&&
              !(REG(0xff008500u)&0x2000u)&&REG(0xff000318u)==0&&
              irq_active[1]==0u&&task_done==1u&&worker_done==1u&&
              worker_started==1u&&irq_fault==0u);
}
static void Worker(rtems_task_argument nonce){unsigned int sp,low,high,old,error;
 (void)nonce;
 __asm__ volatile("mov sp,%0":"=r"(sp));
 worker_sp=sp;worker_thread=(unsigned int)_Thread_Executing;
 low=(unsigned int)_Thread_Executing->Start.Initial_stack.area;
 high=low+_Thread_Executing->Start.Initial_stack.size;
 worker_stack_low=low;worker_stack_high=high;
 if(sp<low||sp>=high||resident_phase!=1u)irq_fault|=0x4000u;
 error=rtems_task_mode(RTEMS_NO_PREEMPT,RTEMS_PREEMPT_MASK,&old);
 if(error!=RTEMS_SUCCESSFUL)irq_fault|=0x8000u;
 worker_started=1u;state=ACTIVE;side[4]=ACTIVE;
 for(;;){unsigned int i;
  timer_invalidate_dcache();
  for(i=0;i<256u;i++){
   worker_progress++;
   if(irq_fault){worker_result=EXPIRED;break;}
   if(side[0]==0x3145534cu&&side[1]==0x161610d1u&&side[2]==1u&&
      side[3]==HALT){worker_result=HALTED;break;}
   if(ticks>=MAX_TICKS){worker_result=EXPIRED;break;}
  }
  if(worker_result)break;
 }
 stop_tick=ticks;worker_done=1u;
 /* No-preempt keeps Init from running until this task has suspended itself. */
 if(rtems_task_resume(init_id)!=RTEMS_SUCCESSFUL)irq_fault|=0x10000u;
 /* Suspension makes this worker non-runnable before Init reclaims the grant. */
 if(rtems_task_suspend(RTEMS_SELF)!=RTEMS_SUCCESSFUL)irq_fault|=0x10000u;
 irq_fault|=0x20000u;
 for(;;){}
}
static void Init(rtems_task_argument nonce){unsigned int sp,low,high,error;
 (void)nonce;
 __asm__ volatile("mov sp,%0":"=r"(sp));
 task_sp=sp;task_thread=(unsigned int)_Thread_Executing;
 low=(unsigned int)_Thread_Executing->Start.Initial_stack.area;
 high=low+_Thread_Executing->Start.Initial_stack.size;
 task_stack_low=low;task_stack_high=high;
 if(sp<low||sp>=high||resident_phase!=1u)irq_fault|=0x1000u;
 dispatch_task_base=_Thread_Dispatch_disable_level;
 task_started=1u;
 init_id=_Thread_Executing->Object.id;
 if(!init_id)irq_fault|=0x400000u;
 error=rtems_task_create(0x574b5231u,4,4096,
       RTEMS_DEFAULT_MODES,RTEMS_DEFAULT_ATTRIBUTES,&worker_id);
 if(error!=RTEMS_SUCCESSFUL){irq_fault|=0x40000u;worker_result=EXPIRED;worker_done=1u;}
 else {
  worker_id_word=worker_id;
  error=rtems_task_start(worker_id,Worker,0);
  if(error!=RTEMS_SUCCESSFUL){irq_fault|=0x80000u;worker_result=EXPIRED;worker_done=1u;}
 }
 if(!worker_done){
  task_progress=1u;
  if(rtems_task_suspend(RTEMS_SELF)!=RTEMS_SUCCESSFUL)irq_fault|=0x100000u;
 }
 if(!worker_done||!worker_started||!worker_progress||
    (unsigned int)_Thread_Executing!=task_thread||
    worker_result==0u||_ISR_Nest_level||_Thread_Dispatch_disable_level)
  irq_fault|=0x200000u;
 task_result=worker_result?worker_result:EXPIRED;
 mask31();task_done=1u;
 /* Shutdown switches back to the retained firmware-IRQ continuation. */
 rtems_shutdown_executive(0);
 irq_fault|=0x2000u;
 for(;;){} /* Returning here would violate continuation ownership. */
}
void timer_interrupt(unsigned int fp,unsigned int slot){
 unsigned int sp,pc,ac,vector;
 __asm__ volatile("mov sp,%0":"=r"(sp));irq_sp[slot]=sp;
 if(sp<(unsigned int)irq_owned_area+slot*8192u+192u||
    sp>=(unsigned int)irq_owned_area+slot*8192u+4096u)irq_fault|=1u;
 if((fp&15u)||fp<0xc0000100u||fp>=0xc0722000u){irq_fault|=2u;return;}
 pc=REG(fp-16u);ac=REG(fp-12u);vector=REG(fp-8u);
 if(vector!=0x12u)irq_fault|=4u;
 if(slot==1u){
  unsigned int executing=(unsigned int)_Thread_Executing;
  if(!task_started||
     !((executing==task_thread&&fp>=task_stack_low&&fp<task_stack_high)||
       (executing==worker_thread&&worker_started&&
        fp>=worker_stack_low&&fp<worker_stack_high)))irq_fault|=8u;
  if(executing==worker_thread)worker_irq_count++;
  task_irq_count++;
  _ISR_Nest_level++;_Thread_Dispatch_disable_level++;
  ticks++;if(rtems_clock_tick()!=RTEMS_SUCCESSFUL)irq_fault|=16u;
  _Thread_Dispatch_disable_level--;_ISR_Nest_level--;
  if(_Thread_Dispatch_disable_level!=dispatch_task_base||_ISR_Nest_level)
   irq_fault|=32u;
  if(REG(fp-16u)!=pc||REG(fp-12u)!=ac||REG(fp-8u)!=vector)irq_fault|=64u;
  return;
 }
 if(fp>=0xc0710000u){irq_fault|=128u;return;}
 _ISR_Nest_level++;_Thread_Dispatch_disable_level++;
 ticks++;if(rtems_clock_tick()!=RTEMS_SUCCESSFUL)irq_fault|=256u;
 _Thread_Dispatch_disable_level--;_ISR_Nest_level--;
 timer_invalidate_dcache();
 if(!entries&&side[3]==ENTER&&side[0]==0x3145534cu&&
    side[1]==0x161610d1u&&side[2]==1u){
  side[3]=0u;entries=1u;entered_ticks=ticks;
  frame=fp;frame_pc=pc;frame_ac=ac;frame_vector=vector;
 }
 if(clock_fired&&entries&&!irq_fault){
  resident_phase=1u;
  rtems_initialize_executive_late(bsp_level);
  /* Reached only after the RTEMS task shut itself down at priority 31. */
  if(!task_started||!task_done||irq_active[1])irq_fault|=512u;
  stop_timer();state=task_result;
 }else if(ticks>=MAX_TICKS||irq_fault){
  /* Admission did not transfer to a task. Retain grant on any fault. */
  stop_timer();state=EXPIRED;
 }
 if(!armed){volatile unsigned int *trace=(volatile unsigned int*)(irq_owned_area+3072);
  trace[0]=0x4b535452u;trace[1]=ticks;trace[2]=entries;
  trace[3]=entered_ticks;trace[4]=frame;trace[5]=frame_pc;
  trace[6]=frame_ac;trace[7]=frame_vector;trace[8]=irq_sp[0];
  trace[9]=irq_fault;trace[10]=restoration;trace[11]=state;
  REG(fp-16u)=(pc&~0x1f0000u)|(saved_pc&0x1f0000u);
  trace[12]=REG(fp-16u);trace[13]=saved_pc;trace[14]=pc;
  trace[15]=clock_fired;trace[16]=clock_tick;trace[17]=clock_after_enter;
  trace[18]=task_started;trace[19]=task_done;trace[20]=task_progress;
  trace[21]=task_thread;trace[22]=task_sp;trace[23]=task_stack_low;
  trace[24]=task_stack_high;trace[25]=task_irq_count;
  trace[26]=irq_sp[1];trace[27]=stop_tick;trace[28]=resident_phase;
  trace[29]=_ISR_Nest_level;trace[30]=_Thread_Dispatch_disable_level;
  trace[31]=task_result;trace[32]=irq_active[1];
  trace[33]=worker_started;trace[34]=worker_done;
  trace[35]=worker_progress;trace[36]=worker_thread;
  trace[37]=worker_sp;trace[38]=worker_stack_low;
  trace[39]=worker_stack_high;trace[40]=worker_irq_count;
  trace[41]=worker_result;trace[42]=worker_id_word;
  side[5]=frame;side[6]=irq_fault;side[7]=restoration;side[4]=state;
  diag[4]=ticks;diag[5]=irq_sp[0];diag[6]=task_progress;diag[7]=restoration;
 }
}
unsigned int bounded_main(unsigned int report_addr,unsigned int nonce){
 volatile unsigned int *report=(volatile unsigned int*)report_addr;
 unsigned char *p;unsigned int error;
 if(report_addr!=0xc000fa20u||nonce!=0x161610d1u)return 0xbad00001u;
 for(p=_bss_start;p<_bss_end;p++)*p=0;
 if(side[0]!=0x3145534cu||side[1]!=nonce||side[2]!=1u||
    side[3]!=0u)return 0xbad00002u;
 error=preflight();diag[1]=error;if(error)return 0xbad10000u|error;
 bsp_level=rtems_initialize_executive_early(&config,&cpu);
 if(!_Thread_Executing||!_Thread_Heir)return 0xbad20001u;
 error=rtems_timer_create(0x434c4b31u,&clock_id);
 if(error!=RTEMS_SUCCESSFUL)return 0xbad20002u|error;
 /* Twenty RTEMS ticks leave time for the firmware callback to return and
  * for the host to issue ENTER. A callback before ENTER is a hard fault. */
 error=rtems_timer_fire_after(clock_id,20,clock_callback,0);
 if(error!=RTEMS_SUCCESSFUL)return 0xbad20003u|error;
 saved_pc=escape_context[2];
 diag[6]=saved_pc;
 saved_mask=REG(0xff008504u);saved_map=REG(0xff008528u);
 saved_vector=REG(0x4u);saved_reload=REG(0xff000310u);
 saved_count=REG(0xff000314u);
 mask31();REG(0xff008504u)=0u;REG(0x4u)=(unsigned int)timer_isr;
 REG(0xff008528u)=0x00180000u;
 /* 100 MHz / 8 / 125000 -> 10 ms period, maximum 1.28 s. */
 REG(0xff000310u)=125000u;REG(0xff000314u)=125000u;
 REG(0xff008504u)=0x2000u;armed=1u;REG(0xff000318u)=0x36u;
 side[4]=0x59444152u; /* READY: arm finished; op13 still returning. */
 report[0]=0x314e5552u;report[1]=nonce;report[2]=0x31454e4fu;
 report[6]=0x4d524141u; /* AARM: accepted asynchronous arm. */
 return 0;
}

/* AcceleRAID 160: bounded RTEMS wake driven by owned timer-1 interrupts.
 * The ISR advances the clock but defers task dispatch to a task boundary. */
#include <rtems/system.h>
#include <rtems/rtems/tasks.h>
#include <rtems/rtems/clock.h>
#include <rtems/config.h>
#include <rtems/init.h>
#include <rtems/score/context.h>
#include <rtems/score/thread.h>
#include <rtems/score/isr.h>
#include <stddef.h>

extern unsigned char _bss_start[],_bss_end[],irq_owned_area[];
extern void bounded_escape(unsigned int) __attribute__((noreturn));
extern void lease_invalidate_dcache(void),timer_isr(void);
#define REG(a) (*(volatile unsigned int *)(a))
#define STOP 0x504f5453u
#define TIME 0x454d4954u
static unsigned char workspace[32768] __attribute__((aligned(16)));
static volatile unsigned int done,stop_seen,polls,worker_sp,result;
static volatile unsigned int ticks,wake_tick,irq_sp;
volatile unsigned int irq_active,irq_fault;
static unsigned int saved_mask,saved_map,saved_vector,saved_reload,saved_count;
static volatile unsigned int armed,restoration;
static rtems_id worker_id;
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
              REG(0xff000318u)==0u && irq_active==0u && irq_fault==0u);
}
void bounded_fatal(unsigned int code){stop_timer();bounded_escape(0xf0000000u|code);}
#define CHECK(x) do {unsigned int e=(x);if(e)bounded_fatal(0x10000u+__LINE__*256u+e);}while(0)
#define ASSERT(x) do {if(!(x))bounded_fatal(0x20000u+__LINE__);}while(0)

void timer_interrupt(void){unsigned int sp;
 __asm__ volatile("mov sp,%0":"=r"(sp));
 irq_sp=sp;
 if(sp<(unsigned int)irq_owned_area+192u ||
    sp>=(unsigned int)irq_owned_area+4096u)irq_fault=2u;
 _ISR_Nest_level++;
 _Thread_Dispatch_disable_level++;
 ticks++;
 if(rtems_clock_tick())irq_fault=3u;
 _Thread_Dispatch_disable_level--;
 _ISR_Nest_level--;
 REG(0xc000fa70u)=ticks;
 REG(0xc000fa74u)=sp;
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

static void Worker(rtems_task_argument nonce){unsigned int i,sp,previous;
 volatile unsigned int * const trace=(volatile unsigned int *)irq_owned_area;
 unsigned int pc_start,pc_end;
 __asm__ volatile("mov sp,%0":"=r"(sp));worker_sp=sp;
 CHECK(rtems_task_mode(RTEMS_INTERRUPT_LEVEL(0),RTEMS_INTERRUPT_MASK,&previous));
 CHECK(rtems_task_wake_after(5));
 /* A yielded task resumes with the RTEMS context's saved PC. Open the
  * interrupt window only in this bounded worker loop; do not yield again
  * while the timer owns vector 18. */
 priority0();
 __asm__ volatile("modpc 0,0,%0":"=r"(pc_start));
 wake_tick=ticks;
 REG(0xc000fa78u)=wake_tick;
 ASSERT(wake_tick>=5u && irq_sp>=(unsigned int)irq_owned_area+192u);
 control[4]=0x59444152u; /* READY only after hardware-tick wake */
 for(i=0;i<500000u;i++){
  lease_invalidate_dcache();
  if(control[3]==STOP){
   ASSERT(control[0]==0x3145534cu&&control[1]==nonce&&control[2]==1u);
   stop_seen=1u;break;
  }
  if(irq_fault)bounded_fatal(0x50010u|irq_fault);
 }
 polls=i;
 __asm__ volatile("modpc 0,0,%0":"=r"(pc_end));
 trace[0]=0x444b4c43u; /* CLKD */
 trace[1]=pc_start;trace[2]=pc_end;
 trace[3]=REG(0xff008504u);trace[4]=REG(0xff008500u);
 trace[5]=REG(0xff000310u);trace[6]=REG(0xff000314u);
 trace[7]=ticks;trace[8]=polls;
 trace[9]=REG(0x4u);trace[10]=REG(0xff008528u);
 if(!stop_seen)control[4]=TIME;
 done=1u;
 CHECK(rtems_task_delete(RTEMS_SELF));
 bounded_fatal(0x30001u);
}
static void Init(rtems_task_argument nonce){rtems_task_priority old;
 (void)nonce;
 CHECK(rtems_task_create(0x574f524bu,2,4096,
       RTEMS_INTERRUPT_LEVEL(31),RTEMS_DEFAULT_ATTRIBUTES,&worker_id));
 CHECK(rtems_task_start(worker_id,Worker,0x161610d1u));
 arm_timer();
 priority0();
 CHECK(rtems_task_set_priority(RTEMS_SELF,3,&old));
 while(!done){CHECK(rtems_task_wake_after(0));priority0();}
 stop_timer();
 ASSERT(restoration && wake_tick>=5u && ticks>=wake_tick);
 if(stop_seen){control[5]=0x214b4341u;control[6]=0x161610d1u;control[7]=1u;}
 result=stop_seen?STOP:TIME;
 rtems_shutdown_executive(0);
}
static rtems_initialization_tasks_table tasks[]={{0x494e4954,4096,1,
 RTEMS_DEFAULT_ATTRIBUTES,Init,RTEMS_INTERRUPT_LEVEL(31),0}};
static rtems_api_configuration_table api={3,0,2,0,0,0,0,0,1,tasks};
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
 if(done!=1u || !restoration || wake_tick<5u ||
    result!=(stop_seen?STOP:TIME))return 0xbad00003u;
 report[0]=0x314e5552u;
 report[1]=nonce;
 report[2]=0x31454e4fu;
 report[6]=result;
 REG(0xc000fa70u)=ticks;
 REG(0xc000fa74u)=irq_sp;
 REG(0xc000fa78u)=wake_tick;
 REG(0xc000fa7cu)=restoration;
 return 0;
}

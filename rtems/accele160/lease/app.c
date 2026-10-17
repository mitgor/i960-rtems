#include <rtems/system.h>
#include <rtems/rtems/tasks.h>
#include <rtems/rtems/clock.h>
#include <rtems/config.h>
#include <rtems/init.h>
#include <rtems/score/context.h>
#include <rtems/score/thread.h>
#include <stddef.h>

extern unsigned char _bss_start[],_bss_end[];
extern void bounded_escape(unsigned int code) __attribute__((noreturn));
extern void lease_invalidate_dcache(void);
static unsigned char workspace[32768] __attribute__((aligned(16)));
static volatile unsigned int done,stop_seen,polls,worker_sp,result;
static rtems_id worker_id;
static volatile unsigned int * const control=(volatile unsigned int *)0xc000fa40u;

void bounded_fatal(unsigned int code){bounded_escape(0xf0000000u|code);}
#define CHECK(x) do {unsigned int e=(x);if(e)bounded_fatal(0x10000u+__LINE__*256u+e);}while(0)
#define ASSERT(x) do {if(!(x))bounded_fatal(0x20000u+__LINE__);}while(0)
typedef char context_pc_offset[(offsetof(Context_Control,pc)==8)?1:-1];
typedef char context_g8_offset[(offsetof(Context_Control,g8)==12)?1:-1];

static void Worker(rtems_task_argument nonce){
 unsigned int i,sp;
 __asm__ volatile("mov sp,%0":"=r"(sp));
 worker_sp=sp;
 control[4]=0x59444152u; /* READY */
 for(i=0;i<2000000u;i++){
  lease_invalidate_dcache();
  if(control[3]==0x504f5453u){
   ASSERT(control[0]==0x3145534cu&&control[1]==nonce&&control[2]==1u);
   control[5]=0x214b4341u; /* ACK */
   control[6]=nonce;
   control[7]=1u;
   stop_seen=1u;
   break;
  }
  if((i&4095u)==0)CHECK(rtems_task_wake_after(0));
 }
 polls=i;
 if(!stop_seen)control[4]=0x454d4954u; /* TIME */
 done=1u;
 CHECK(rtems_task_delete(RTEMS_SELF));
 bounded_fatal(0x30001u);
}

static void Init(rtems_task_argument nonce){
 rtems_task_priority old;
 (void)nonce;
 CHECK(rtems_task_create(0x574f524bu,2,4096,
       RTEMS_INTERRUPT_LEVEL(31),RTEMS_DEFAULT_ATTRIBUTES,&worker_id));
 CHECK(rtems_task_start(worker_id,Worker,0x161610d1u));
 CHECK(rtems_task_set_priority(RTEMS_SELF,3,&old));
 while(!done)CHECK(rtems_task_wake_after(0));
 result=stop_seen?0x504f5453u:0x454d4954u;
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
 if(done!=1u||result!=(stop_seen?0x504f5453u:0x454d4954u))
  return 0xbad00003u;
 report[0]=0x314e5552u; /* RUN1 */
 report[1]=nonce;
 report[2]=0x31454e4fu; /* ONE1 */
 report[6]=result;
 ((volatile unsigned int *)0xc000fa70u)[0]=worker_sp;
 ((volatile unsigned int *)0xc000fa70u)[1]=polls;
 ((volatile unsigned int *)0xc000fa70u)[2]=stop_seen;
 ((volatile unsigned int *)0xc000fa70u)[3]=done;
 return 0;
}

#include <string.h>
#include <rtems/system.h>
#include <rtems/rtems/options.h>
#include <rtems/config.h>
#include <rtems/init.h>
#include <rtems/rtems/tasks.h>
#include <rtems/rtems/sem.h>
#include <rtems/rtems/message.h>
#include <rtems/rtems/clock.h>
#include <rtems/score/context.h>
#include <rtems/score/thread.h>
#include <stddef.h>
extern unsigned char _bss_start[],_bss_end[];
static unsigned char workspace[32768] __attribute__((aligned(16)));
static volatile unsigned int result,mode,count[2],done,ticks,woke;
static rtems_id ids[2],sems[2],queue;
extern void bounded_escape(unsigned int code) __attribute__((noreturn));
void bounded_fatal(unsigned int code){bounded_escape(0xf0000000|code);}
#define CHECK(x) do {unsigned int e=(x);if(e)bounded_fatal(0x10000+__LINE__*256+e);}while(0)
#define ASSERT(x) do {if(!(x))bounded_fatal(0x20000+__LINE__);}while(0)
typedef char context_pc_offset[(offsetof(Context_Control,pc)==8)?1:-1];
typedef char context_g8_offset[(offsetof(Context_Control,g8)==12)?1:-1];
typedef char context_fp_offset[(offsetof(Context_Control,g15_fp)==40)?1:-1];
static void Worker(rtems_task_argument arg){
 unsigned int i,n,msg,bytes;volatile unsigned int cookie=0xabcd0000|arg;
 if(mode==6){CHECK(rtems_task_wake_after(5));woke=ticks;done=1;CHECK(rtems_task_suspend(RTEMS_SELF));}
 for(i=0;i<200;i++){
  if(mode==4)CHECK(rtems_semaphore_obtain(sems[arg],RTEMS_WAIT,WATCHDOG_NO_TIMEOUT));
  if(mode==5 && arg==1){bytes=0;CHECK(rtems_message_queue_receive(queue,&msg,&bytes,RTEMS_WAIT,WATCHDOG_NO_TIMEOUT));ASSERT(bytes==4&&msg==i);}
  ASSERT(cookie==(0xabcd0000|arg));count[arg]++;
  if(mode==4)CHECK(rtems_semaphore_release(sems[1-arg]));
  if(mode==5 && arg==0){msg=i;CHECK(rtems_message_queue_send(queue,&msg,4));}
  CHECK(rtems_task_wake_after(0));
 }
 done|=1u<<arg;CHECK(rtems_task_suspend(RTEMS_SELF));bounded_fatal(0x30001);
}
static void Init(rtems_task_argument arg){
 unsigned int i; rtems_task_priority old;
 if(mode<3){result=0x46600001;rtems_shutdown_executive(0);}
 if(mode==4){for(i=0;i<2;i++)CHECK(rtems_semaphore_create(0x53454d30+i,i==0,RTEMS_SIMPLE_BINARY_SEMAPHORE|RTEMS_FIFO,0,&sems[i]));}
 if(mode==5)CHECK(rtems_message_queue_create(0x51554555,4,4,RTEMS_FIFO,&queue));
 for(i=0;i<(mode==6?1:2);i++){
  CHECK(rtems_task_create(0x574f5230+i,2,4096,RTEMS_INTERRUPT_LEVEL(31),RTEMS_DEFAULT_ATTRIBUTES,&ids[i]));
  CHECK(rtems_task_start(ids[i],Worker,i));
 }
 CHECK(rtems_task_set_priority(RTEMS_SELF,3,&old));
 if(mode==6){for(ticks=1;ticks<=10;ticks++)CHECK(rtems_clock_tick());ASSERT(done==1&&woke==5);}
 else ASSERT(done==3&&count[0]==200&&count[1]==200);
 result=0x46600000|mode;rtems_shutdown_executive(0);
}
static rtems_initialization_tasks_table tasks[]={{0x494e4954,4096,1,RTEMS_DEFAULT_ATTRIBUTES,Init,RTEMS_INTERRUPT_LEVEL(31),0}};
static rtems_api_configuration_table api={3,0,2,1,0,0,0,0,1,tasks};
static rtems_configuration_table config={workspace,sizeof(workspace),0,10000,1,0,0,0,0,0,0,0,&api,0,0};
static rtems_cpu_table cpu={0,0,0,0,1,2048,2048,0,0,0};
void _ISR_Handler(void){bounded_fatal(0x40000);}
void _CPU_ISR_install_raw_handler(unsigned int v,proc_ptr n,proc_ptr*o){bounded_fatal(0x40000|v);}
unsigned int bounded_main(unsigned int arg){unsigned char*p;for(p=_bss_start;p<_bss_end;p++)*p=0;if(arg==1)bounded_fatal(0x1234);if(arg==2)return 0x46600000|sizeof(Context_Control);mode=arg;rtems_initialize_executive(&config,&cpu);return result;}

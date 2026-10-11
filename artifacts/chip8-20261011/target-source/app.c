/* Bounded RTEMS worker application. No IRQ ownership or production net changes. */
#include <rtems/system.h>
#include <rtems/config.h>
#include <rtems/init.h>
#include <rtems/rtems/options.h>
#include <rtems/rtems/tasks.h>
#include <rtems/rtems/sem.h>
#include <rtems/rtems/clock.h>
#include <rtems/score/thread.h>
#include "buffer_io.h"
#include "chip8.h"
extern unsigned char _bss_start[],_bss_end[];
static unsigned char workspace[49152] __attribute__((aligned(16)));
static struct chip8 guest;
static unsigned int initialized=0,clock_carry;
static rtems_id worker_id,request_sem,reply_sem;
extern void bounded_escape(unsigned int code) __attribute__((noreturn));
void bounded_fatal(unsigned int code){bounded_escape(0xf0000000|code);}
#define CHECK(x) do {unsigned int e=(x);if(e)bounded_fatal(0x10000+__LINE__*256+e);}while(0)
static void idle_error(void){bounded_fatal(0xdead);}
static void Worker(rtems_task_argument arg){
 unsigned char*b=(unsigned char*)BIO_BASE;
 unsigned int rc,ticks;
 for(;;){
  CHECK(rtems_semaphore_obtain(request_sem,RTEMS_WAIT,WATCHDOG_NO_TIMEOUT));
  rc=c8_request(&guest,b+BIO_INPUT,bio_word(b+12),b+BIO_OUTPUT,bio_word(b+16));
  if(!rc){
   ticks=bio_word(b+BIO_INPUT+16);
   /* Convert validated 60 Hz guest ticks into the existing 100 Hz RTEMS clock. */
   clock_carry+=ticks*100;
   while(clock_carry>=60){clock_carry-=60;CHECK(rtems_clock_tick());}
  }
  bio_put(b+20,rc);bio_put(b+24,rc?0:C8_REPLY_BYTES);bio_put(b+28,bio_word(b+8));
  CHECK(rtems_semaphore_release(reply_sem));
 }
}
static void Init(rtems_task_argument arg){
 CHECK(rtems_semaphore_create(0x43525131,0,RTEMS_SIMPLE_BINARY_SEMAPHORE|RTEMS_FIFO,0,&request_sem));
 CHECK(rtems_semaphore_create(0x43525031,0,RTEMS_SIMPLE_BINARY_SEMAPHORE|RTEMS_FIFO,0,&reply_sem));
 CHECK(rtems_task_create(0x43384731,2,4096,RTEMS_INTERRUPT_LEVEL(31),RTEMS_DEFAULT_ATTRIBUTES,&worker_id));
 CHECK(rtems_task_start(worker_id,Worker,0));
 for(;;){
  if(!bio_request_valid((unsigned char*)BIO_BASE))bounded_fatal(0x50001);
  CHECK(rtems_semaphore_release(request_sem));
  CHECK(rtems_semaphore_obtain(reply_sem,RTEMS_WAIT,WATCHDOG_NO_TIMEOUT));
  _CPU_Context_switch(&_Thread_Executing->Registers,&_Thread_BSP_context);
 }
}
static rtems_initialization_tasks_table tasks[]={{0x494e4954,8192,1,RTEMS_DEFAULT_ATTRIBUTES,Init,RTEMS_INTERRUPT_LEVEL(31),0}};
static rtems_api_configuration_table api={2,0,2,0,0,0,0,0,1,tasks};
static rtems_configuration_table config={workspace,sizeof(workspace),0,10000,1,0,0,0,0,0,0,0,&api,0,0};
static rtems_cpu_table cpu={0,0,0,idle_error,1,2048,2048,0,0,0};
void _ISR_Handler(void){bounded_fatal(0x40000);}
void _CPU_ISR_install_raw_handler(unsigned int v,proc_ptr n,proc_ptr*o){bounded_fatal(0x40000|v);}
unsigned int bounded_main(unsigned int arg){
 unsigned char*p;if(arg!=BIO_BASE)return 1;
 if(!initialized){for(p=_bss_start;p<_bss_end;p++)*p=0;initialized=1;rtems_initialize_executive(&config,&cpu);}
 else _CPU_Context_switch(&_Thread_BSP_context,&_Thread_Executing->Registers);
 return 0;
}
#include <stddef.h>
typedef char abi_word_size[(sizeof(void*)==4&&sizeof(unsigned long)==4&&sizeof(c8_u32)==4)?1:-1];
typedef char abi_context_size[(sizeof(Context_Control)==48)?1:-1];
typedef char abi_context_pc[(offsetof(Context_Control,pc)==8)?1:-1];
typedef char abi_context_g8[(offsetof(Context_Control,g8)==12)?1:-1];
typedef char abi_context_fp[(offsetof(Context_Control,g15_fp)==40)?1:-1];

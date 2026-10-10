#include <string.h>
#include <rtems/system.h>
#include <rtems/config.h>
#include <rtems/init.h>
#include <rtems/rtems/options.h>
#include <rtems/rtems/tasks.h>
#include <rtems/rtems/sem.h>
#include <rtems/rtems/clock.h>
#include <rtems/score/thread.h>
#include "buffer_io.h"
#include "network.h"
extern unsigned char _bss_start[],_bss_end[];
static unsigned char workspace[49152] __attribute__((aligned(16)));
static unsigned int initialized=0,steps,worker_steps,ticks,carry;
static unsigned char guarded_stacks[3][8320] __attribute__((aligned(16)));
static unsigned int stack_count,stack_sizes[3];
static rtems_id worker_id,request_sem,reply_sem;
extern void bounded_escape(unsigned int code) __attribute__((noreturn));
void bounded_fatal(unsigned int code){bounded_escape(0xf0000000|code);}
#define CHECK(x) do {unsigned int e=(x);if(e)bounded_fatal(0x10000+__LINE__*256+e);}while(0)
static void *stack_alloc(unsigned int size){unsigned int i=stack_count++;if(i>=3||size>8192)bounded_fatal(0x51000);stack_sizes[i]=size;memset(guarded_stacks[i],0xa5,sizeof(guarded_stacks[i]));return guarded_stacks[i]+16;}
static void stack_free(void *p){bounded_fatal(0x51001);}
static void stack_check(void){unsigned int i,j;for(i=0;i<stack_count;i++){for(j=0;j<16;j++)if(guarded_stacks[i][j]!=0xa5)bounded_fatal(0x51010+i);for(j=16+stack_sizes[i];j<sizeof(guarded_stacks[i]);j++)if(guarded_stacks[i][j]!=0xa5)bounded_fatal(0x51020+i);}}
static void yield_host(void){_CPU_Context_switch(&_Thread_Executing->Registers,&_Thread_BSP_context);}
static void Worker(rtems_task_argument arg){for(;;){CHECK(rtems_semaphore_obtain(request_sem,RTEMS_WAIT,WATCHDOG_NO_TIMEOUT));worker_steps++;CHECK(rtems_semaphore_release(reply_sem));}}
static void idle_error(void){bounded_fatal(0xdead);}
static void process(void){
 unsigned char*b=(unsigned char*)BIO_BASE,*in=b+BIO_INPUT,*out=b+BIO_OUTPUT;
 unsigned int n=bio_word(b+12),ms,op;
 if(_CPU_ISR_Get_level()!=31)bounded_fatal(0x52000);
 if(!bio_request_valid(b)||n<16||bio_word(in)!=0x314d5452){bounded_fatal(0x50001);}
 op=bio_word(in+4);ms=bio_word(in+8);
 if(ms>1000||bio_word(in+12)!=n-16||op>5){bounded_fatal(0x50002);}
 carry+=ms;while(carry>=10){carry-=10;ticks++;CHECK(rtems_clock_tick());}
 CHECK(rtems_semaphore_release(request_sem));CHECK(rtems_semaphore_obtain(reply_sem,RTEMS_WAIT,WATCHDOG_NO_TIMEOUT));
 if(op==2||op==5){char name[128];unsigned int length=n-16,port;if(length<3||length>129)bounded_fatal(0x50003);port=in[16]|in[17]<<8;memcpy(name,in+18,length-2);name[length-2]=0;network_fetch(name,port,op==5);}
 network_step(ms,op==1?in+16:0,op==1?n-16:0);
 steps++;bio_put(out,0x314d5452);bio_put(out+4,steps);bio_put(out+8,worker_steps);bio_put(out+12,ticks);
 bio_put(out+16,network_report(out+20));
 {unsigned int bytes;if(op==4){if(n!=20)bounded_fatal(0x50004);bytes=network_fetch_data(out+48,bio_word(in+16),4096);bio_put(out+44,bytes|0x80000000u);}else{bytes=network_output(out+48,8192-48);bio_put(out+44,bytes);}
 bio_put(b+20,0);bio_put(b+24,48+bytes);bio_put(b+28,bio_word(b+8));}

}
static void Init(rtems_task_argument arg){
 CHECK(rtems_semaphore_create(0x52455131,0,RTEMS_SIMPLE_BINARY_SEMAPHORE|RTEMS_FIFO,0,&request_sem));
 CHECK(rtems_semaphore_create(0x52504c31,0,RTEMS_SIMPLE_BINARY_SEMAPHORE|RTEMS_FIFO,0,&reply_sem));
 CHECK(rtems_task_create(0x574f524b,2,4096,RTEMS_INTERRUPT_LEVEL(31),RTEMS_DEFAULT_ATTRIBUTES,&worker_id));
 CHECK(rtems_task_start(worker_id,Worker,0));
 network_init();
 for(;;){process();yield_host();}
}
static rtems_initialization_tasks_table tasks[]={{0x494e4954,8192,1,RTEMS_DEFAULT_ATTRIBUTES,Init,RTEMS_INTERRUPT_LEVEL(31),0}};
static rtems_api_configuration_table api={2,0,2,0,0,0,0,0,1,tasks};
static rtems_configuration_table config={workspace,sizeof(workspace),0,10000,1,0,0,0,0,0,0,0,&api,0,0};
static rtems_cpu_table cpu={0,0,0,idle_error,1,2048,2048,0,stack_alloc,stack_free};
void _ISR_Handler(void){bounded_fatal(0x40000);}
void _CPU_ISR_install_raw_handler(unsigned int v,proc_ptr n,proc_ptr*o){bounded_fatal(0x40000|v);}
unsigned int bounded_main(unsigned int arg){unsigned char*p;if(arg!=BIO_BASE)return 1;
 if(!initialized){for(p=_bss_start;p<_bss_end;p++)*p=0;initialized=1;rtems_initialize_executive(&config,&cpu);}
 else _CPU_Context_switch(&_Thread_BSP_context,&_Thread_Executing->Registers);
 stack_check();return 0;
}

/* Assembly contract, checked on every target build. */
#include <stddef.h>
typedef char abi_word_size[(sizeof(void*)==4 && sizeof(unsigned long)==4)?1:-1];
typedef char abi_context_size[(sizeof(Context_Control)==48)?1:-1];
typedef char abi_context_pc[(offsetof(Context_Control,pc)==8)?1:-1];
typedef char abi_context_g8[(offsetof(Context_Control,g8)==12)?1:-1];
typedef char abi_context_fp[(offsetof(Context_Control,g15_fp)==40)?1:-1];

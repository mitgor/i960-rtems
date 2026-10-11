/* irq: bounded hardware-interrupt/preemption experiment; stop before return.
 * auto/I960_BACKGROUND: experimental background runtime, requires dac960auto
 * with its pinned image and kernel-side stop-before-restore protocol. */
#include <string.h>
#include <rtems/system.h>
#include <rtems/config.h>
#include <rtems/init.h>
#include <rtems/rtems/tasks.h>
#include <rtems/rtems/clock.h>
#include <rtems/score/thread.h>
#include <rtems/score/isr.h>
#include "buffer_io.h"
extern unsigned char _bss_start[],_bss_end[];
extern void timer_isr(void);
extern void bounded_escape(unsigned int) __attribute__((noreturn));
static unsigned char workspace[49152] __attribute__((aligned(16)));
static unsigned char stacks[3][8320] __attribute__((aligned(16)));
static unsigned int allocated,sizes[3],initialized=0,steps;
static volatile unsigned int ticks,wakes,busy,observed_busy,last_wake_tick;
static volatile unsigned int background_irq;
#ifdef I960_BACKGROUND
static volatile unsigned int background_active;
static volatile unsigned int background_fault;
static Context_Control fault_context;
#endif
#include "timer_hw.h"
#ifdef I960_MU_ECHO
#include "../control/mu_echo.h"
#endif
void bounded_fatal(unsigned int code){stop_timer();
#ifdef I960_BACKGROUND
 if(background_active){background_fault=code;_CPU_Context_switch(&fault_context,&_Thread_BSP_context);for(;;){} }
#endif
 bounded_escape(0xf0000000|code);
}
#define CHECK(x) do{unsigned int e=(x);if(e)bounded_fatal(0x10000+__LINE__*256+e);}while(0)
static void*stack_alloc(unsigned int size){unsigned int i=allocated++;if(i>=3||size>8192)bounded_fatal(0x51000);sizes[i]=size;memset(stacks[i],0xa5,sizeof(stacks[i]));return stacks[i]+16;}
static void stack_free(void*p){bounded_fatal(0x51001);}
static void idle_error(void){bounded_fatal(0xdead);}
void timer_interrupt(void){
#ifdef I960_MU_ECHO
 mu_poll();
#endif
#ifdef I960_BACKGROUND
 if(armed){background_active=1;background_irq=1;_CPU_Context_switch(&_Thread_BSP_context,&_Thread_Executing->Registers);background_active=0;}
#else
 _ISR_Nest_level++;_Thread_Dispatch_disable_level++;
 ticks++;CHECK(rtems_clock_tick());
 _Thread_Dispatch_disable_level--;_ISR_Nest_level--;
 if(_Context_Switch_necessary&&!_Thread_Dispatch_disable_level)_Thread_Dispatch();
#endif
}
static void Ticker(rtems_task_argument arg){for(;;){CHECK(rtems_task_wake_after(1));wakes++;observed_busy=busy;last_wake_tick=ticks;}}
static void Init(rtems_task_argument arg){rtems_id ticker;unsigned int error,i;
 CHECK(rtems_task_create(0x5449434b,1,4096,RTEMS_INTERRUPT_LEVEL(31),RTEMS_DEFAULT_ATTRIBUTES,&ticker));CHECK(rtems_task_start(ticker,Ticker,0));
 for(;;){unsigned char*b=(unsigned char*)BIO_BASE,*out=b+BIO_OUTPUT;
#ifdef I960_BACKGROUND
 if(background_irq){background_irq=0;ticks++;busy++;CHECK(rtems_clock_tick());_CPU_Context_switch(&_Thread_Executing->Registers,&_Thread_BSP_context);continue;}
 error=0;
 if(bio_word(b+BIO_INPUT+4)==1&&!armed){
#ifdef I960_MU_ECHO
 error=mu_start();if(!error)error=start_timer();
#else
 error=start_timer();
#endif
 }
 if(bio_word(b+BIO_INPUT+4)==2)stop_timer();
#else
 ticks=wakes=busy=observed_busy=last_wake_tick=0;error=start_timer();
 if(!error){priority20();while(ticks<8&&busy<1000000)busy++;stop_timer();}
#endif
 for(i=0;i<allocated;i++){unsigned int j;for(j=0;j<16;j++)if(stacks[i][j]!=0xa5)bounded_fatal(0x51010+i);for(j=16+sizes[i];j<8320;j++)if(stacks[i][j]!=0xa5)bounded_fatal(0x51020+i);}
 steps++;
#ifdef I960_BACKGROUND
 bio_put(out,0x31415452);
#else
 bio_put(out,0x31515249);
#endif
 bio_put(out+60,armed);bio_put(out+4,error);bio_put(out+8,ticks);bio_put(out+12,wakes);bio_put(out+16,busy);bio_put(out+20,observed_busy);bio_put(out+24,last_wake_tick);
 bio_put(out+28,REG(0xff008504));bio_put(out+32,REG(0xff008528));bio_put(out+36,REG(0x3c));bio_put(out+40,saved_vector);
 bio_put(out+44,REG(0xff000310));bio_put(out+48,REG(0xff000314));bio_put(out+52,armed?0x36:REG(0xff000318));bio_put(out+56,REG(0xff008500));
 bio_put(b+20,0);bio_put(b+24,64);bio_put(b+28,bio_word(b+8));
 _CPU_Context_switch(&_Thread_Executing->Registers,&_Thread_BSP_context);
 }
}
static rtems_initialization_tasks_table tasks[]={{0x494e4954,8192,2,RTEMS_DEFAULT_ATTRIBUTES,Init,RTEMS_INTERRUPT_LEVEL(31),0}};
static rtems_api_configuration_table api={2,0,0,0,0,0,0,0,1,tasks};
static rtems_configuration_table config={workspace,sizeof(workspace),0,10000,1,0,0,0,0,0,0,0,&api,0,0};
static rtems_cpu_table cpu={0,0,0,idle_error,1,2048,2048,0,stack_alloc,stack_free};
void _ISR_Handler(void){bounded_fatal(0x40000);}
void _CPU_ISR_install_raw_handler(unsigned int v,proc_ptr n,proc_ptr*o){bounded_fatal(0x40000|v);}
unsigned int bounded_main(unsigned int arg){unsigned char*p;if(arg!=BIO_BASE||!bio_request_valid((unsigned char*)arg))return 1;
#ifdef I960_BACKGROUND
 if(bio_word((unsigned char*)arg+12)!=16||bio_word((unsigned char*)arg+BIO_INPUT)!=0x31415452||bio_word((unsigned char*)arg+BIO_INPUT+4)>2)return 2;
 if(bio_word((unsigned char*)arg+BIO_INPUT+4)==2){timer_stop_response((unsigned char*)arg,initialized);
#ifdef I960_MU_ECHO
 {unsigned int owned=mu_owned,rc=mu_finish();
 bio_put((unsigned char*)arg+BIO_OUTPUT+4,rc);
 bio_put((unsigned char*)arg+BIO_OUTPUT+8,owned&&!rc?0x4d554f4bu:0);}
#endif
 return 0;}
 if(initialized&&background_fault)return 0xf0000000u|background_fault;
#endif
 if(!initialized){for(p=_bss_start;p<_bss_end;p++)*p=0;initialized=1;rtems_initialize_executive(&config,&cpu);}
 else _CPU_Context_switch(&_Thread_BSP_context,&_Thread_Executing->Registers);
 return 0;
}

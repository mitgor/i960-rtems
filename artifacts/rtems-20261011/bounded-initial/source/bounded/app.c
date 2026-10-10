#include <rtems/system.h>
#include <rtems/config.h>
#include <rtems/init.h>
#include <rtems/rtems/tasks.h>
#include <rtems/score/context.h>
#include <rtems/score/thread.h>
extern unsigned char _bss_start[],_bss_end[];
static unsigned char workspace[24576] __attribute__((aligned(16)));
static volatile unsigned int result;
static void Init(rtems_task_argument arg){result=0x46600001;rtems_shutdown_executive(0);}
static rtems_initialization_tasks_table tasks[]={{0x494e4954,4096,1,RTEMS_DEFAULT_ATTRIBUTES,Init,RTEMS_INTERRUPT_LEVEL(31),0}};
static rtems_api_configuration_table api={1,0,0,0,0,0,0,0,1,tasks};
static rtems_configuration_table config={workspace,sizeof(workspace),0,10000,1,0,0,0,0,0,0,0,&api,0,0};
static rtems_cpu_table cpu={0,0,0,0,1,2048,2048,0,0,0};
extern void bounded_escape(unsigned int code) __attribute__((noreturn));
void bounded_fatal(unsigned int code){bounded_escape(0xf0000000|code);}
void _ISR_Handler(void){}
void _CPU_ISR_install_raw_handler(unsigned int v,proc_ptr n,proc_ptr*o){bounded_fatal(0x10000|v);}
unsigned int bounded_main(unsigned int arg){unsigned char*p;for(p=_bss_start;p<_bss_end;p++)*p=0;if(arg==1)bounded_fatal(0x1234);if(arg==2)return 0x46600000|sizeof(Context_Control);rtems_initialize_executive(&config,&cpu);return result;}

/* Persistent, bounded ownership prototype. No timer/IRQ borrowing or device DMA. */
#include <string.h>
#include <rtems/system.h>
#include <rtems/config.h>
#include <rtems/init.h>
#include <rtems/rtems/tasks.h>
#include <rtems/rtems/options.h>
#include <rtems/rtems/sem.h>
#include <rtems/score/thread.h>
#include <rtems/score/isr.h>
#include "buffer_io.h"
#include "policy.h"
extern unsigned char _bss_start[],_bss_end[];
extern void bounded_escape(unsigned int) __attribute__((noreturn));
static unsigned char workspace[49152] __attribute__((aligned(16)));
static unsigned char stacks[5][8320] __attribute__((aligned(16)));
static unsigned int sizes[5],allocated,initialized,finalized,heartbeats;
static struct ownership resource;
static rtems_id tasks_id[3],commands[3],acks[2],mutex_id;
static Thread_Control*threads[3];static Semaphore_Control*mutex;
static unsigned int command_a,arg_a,epoch_a,result_a,wait_value,wait_started,wait_done,wait_seen;
static unsigned int other_count,other_value,owner_starts,guard_fault,hash_a,hash_b;
void bounded_fatal(unsigned int code){bounded_escape(0xf0000000u|code);}
#define CHECK(x) do{unsigned int rc=(x);if(rc)bounded_fatal(0x10000+__LINE__*256+rc);}while(0)
#define REQUIRE(x) do{if(!(x))bounded_fatal(0x90000+__LINE__);}while(0)
static void*stack_alloc(unsigned int n){unsigned int i=allocated++;REQUIRE(i<5&&n<=8192);sizes[i]=n;memset(stacks[i],0xa5,8320);return stacks[i]+16;}
static void stack_free(void*p){bounded_fatal(0x91000);}
static void idle_error(void){bounded_fatal(0xdead);}
static unsigned int hash_stack(unsigned int i){unsigned int n,h=2166136261u;volatile unsigned char*p=threads[i]->Start.Initial_stack.area;
 for(n=0;n<threads[i]->Start.Initial_stack.size;n++)h=(h^p[n])*16777619u;return h;
}
static void guards(void){unsigned int i,j;for(i=0;i<allocated;i++){
 for(j=0;j<16;j++)if(stacks[i][j]!=0xa5)guard_fault++;
 for(j=16+sizes[i];j<8320;j++)if(stacks[i][j]!=0xa5)guard_fault++;
 }REQUIRE(!guard_fault);
}
static void pump(void){rtems_task_priority old;CHECK(rtems_task_set_priority(RTEMS_SELF,5,&old));CHECK(rtems_task_set_priority(RTEMS_SELF,1,&old));}
static void Owner(rtems_task_argument arg){threads[0]=_Thread_Executing;owner_starts++;
 for(;;){CHECK(rtems_semaphore_obtain(commands[0],RTEMS_WAIT,WATCHDOG_NO_TIMEOUT));
  if(command_a==1){result_a=own_begin(&resource,epoch_a,arg_a);if(!result_a)CHECK(rtems_semaphore_obtain(mutex_id,RTEMS_NO_WAIT,0));}
  else{
   /* Publish rollback/commit and release as one dispatch-protected handoff. */
   _Thread_Disable_dispatch();result_a=own_finish(&resource,epoch_a,command_a==12);
   if(!result_a)CHECK(rtems_semaphore_release(mutex_id));
   _Thread_Enable_dispatch();
  }
  CHECK(rtems_semaphore_release(acks[0]));
  if(resource.phase==OWN_RETIRED){CHECK(rtems_task_suspend(RTEMS_SELF));bounded_fatal(0x92000);}
 }
}
static void Waiter(rtems_task_argument arg){threads[1]=_Thread_Executing;
 for(;;){CHECK(rtems_semaphore_obtain(commands[1],RTEMS_WAIT,WATCHDOG_NO_TIMEOUT));wait_started++;
  CHECK(rtems_semaphore_obtain(mutex_id,RTEMS_WAIT,WATCHDOG_NO_TIMEOUT));
  REQUIRE(resource.phase==OWN_RETIRED&&!resource.refs&&resource.staged==resource.committed);
  wait_seen=resource.committed;resource.committed=resource.staged=wait_value;wait_done++;
  CHECK(rtems_semaphore_release(mutex_id));
 }
}
static void Other(rtems_task_argument arg){threads[2]=_Thread_Executing;
 for(;;){CHECK(rtems_semaphore_obtain(commands[2],RTEMS_WAIT,WATCHDOG_NO_TIMEOUT));other_count++;other_value=other_value*1664525u+1013904223u;CHECK(rtems_semaphore_release(acks[1]));}
}
static unsigned int ask_owner(unsigned int op,unsigned int e,unsigned int value){
 if(!own_epoch(&resource,e))return own_reject(&resource,OWN_STALE);
 if(resource.phase==OWN_QUARANTINE||resource.phase==OWN_RETIRED)return own_reject(&resource,OWN_STATE);
 command_a=op;epoch_a=e;arg_a=value;CHECK(rtems_semaphore_release(commands[0]));CHECK(rtems_semaphore_obtain(acks[0],RTEMS_WAIT,WATCHDOG_NO_TIMEOUT));pump();return result_a;
}
static unsigned int process(unsigned int op,unsigned int e,unsigned int value){unsigned int rc,i;
 if(op==0)return 0;
 if(op==10){CHECK(rtems_semaphore_release(commands[2]));CHECK(rtems_semaphore_obtain(acks[1],RTEMS_WAIT,WATCHDOG_NO_TIMEOUT));pump();return 0;}
 if(!own_epoch(&resource,e))return own_reject(&resource,OWN_STALE);
 switch(op){
 case 1:case 4:case 12:return ask_owner(op,e,value);
 case 2:
  if(resource.phase!=OWN_HELD||wait_started!=wait_done)return own_reject(&resource,OWN_STATE);
  wait_value=value;CHECK(rtems_semaphore_release(commands[1]));pump();
  REQUIRE(threads[1]->current_state&STATES_WAITING_FOR_MUTEX);return 0;
 case 3:return own_cancel(&resource,e);
 case 5:return own_lease(&resource,e);
 case 6:return own_complete(&resource,e,value);
 case 7:
  if(resource.phase!=OWN_HELD&&resource.phase!=OWN_CANCEL&&resource.phase!=OWN_QUARANTINE)return own_reject(&resource,OWN_STATE);
  rc=rtems_semaphore_release(mutex_id);REQUIRE(rc==RTEMS_NOT_OWNER_OF_RESOURCE);return rc;
 case 8:
  if(resource.phase!=OWN_RETIRED||threads[0]->current_state!=STATES_SUSPENDED||threads[0]->resource_count||mutex->Core_control.mutex.holder||wait_started!=wait_done)return own_reject(&resource,OWN_STATE);
  rc=own_restart(&resource,e);if(rc)return rc;CHECK(rtems_task_restart(tasks_id[0],0));pump();return 0;
 case 9:
  rc=own_quarantine(&resource,e);if(rc)return rc;
  CHECK(rtems_task_suspend(tasks_id[0]));CHECK(rtems_task_suspend(tasks_id[1]));
  hash_a=hash_stack(0);hash_b=hash_stack(1);return 0;
 case 11:
  if(resource.refs||(resource.phase!=OWN_IDLE&&resource.phase!=OWN_RETIRED&&resource.phase!=OWN_QUARANTINE))return own_reject(&resource,OWN_BUSY);
  for(i=0;i<3;i++)if(!(threads[i]->current_state&STATES_SUSPENDED))CHECK(rtems_task_suspend(tasks_id[i]));
  finalized=1;return 0;
 default:return own_reject(&resource,OWN_STATE);
 }
}
static void report(unsigned int op,unsigned int result){unsigned int w[64],i,pc;unsigned char*b=(unsigned char*)BIO_BASE;
 memset(w,0,sizeof(w));guards();
 if(resource.phase==OWN_QUARANTINE)REQUIRE(hash_a==hash_stack(0)&&hash_b==hash_stack(1));
 __asm__ volatile("modpc 0,0,%0":"=r"(pc));
 w[0]=0x314e574f;w[1]=1;w[2]=bio_word(b+8);w[3]=op;w[4]=result;w[5]=finalized;
 /* The i960 ABI pads this struct to 48 bytes; wire fields occupy 44. */
 memcpy(w+6,&resource,11*sizeof(unsigned int));w[17]=++heartbeats;
 for(i=0;i<3;i++){w[18+i]=tasks_id[i];w[23+i]=threads[i]->current_state;w[42+i]=(unsigned int)threads[i]->Start.Initial_stack.area;}
 w[21]=mutex->Core_control.mutex.holder_id;w[22]=mutex->Core_control.mutex.nest_count;
 w[26]=threads[0]->current_priority;w[27]=threads[0]->resource_count;w[28]=threads[1]->resource_count;
 w[29]=wait_started;w[30]=wait_done;w[31]=wait_seen;w[32]=other_count;w[33]=other_value;w[34]=owner_starts;
 w[35]=guard_fault;w[36]=_Thread_Dispatch_disable_level;w[37]=_ISR_Nest_level;w[38]=hash_a;w[39]=hash_b;w[40]=pc;w[41]=(unsigned int)&resource;w[45]=allocated;
 for(i=0;i<3;i++)if(threads[i]->current_state&STATES_SUSPENDED)w[48]|=1u<<i;
 for(i=0;i<64;i++)bio_put(b+BIO_OUTPUT+i*4,w[i]);
 bio_put(b+20,0);bio_put(b+24,sizeof(w));bio_put(b+28,bio_word(b+8));
}
static void Init(rtems_task_argument arg){unsigned int i;Objects_Locations location;
 CHECK(rtems_semaphore_create(0x4c4f434b,1,RTEMS_BINARY_SEMAPHORE|RTEMS_PRIORITY|RTEMS_INHERIT_PRIORITY,0,&mutex_id));
 mutex=_Semaphore_Get(mutex_id,&location);REQUIRE(location==OBJECTS_LOCAL);_Thread_Enable_dispatch();
 for(i=0;i<3;i++)CHECK(rtems_semaphore_create(0x434d4430+i,0,RTEMS_SIMPLE_BINARY_SEMAPHORE|RTEMS_FIFO,0,&commands[i]));
 for(i=0;i<2;i++)CHECK(rtems_semaphore_create(0x41434b30+i,0,RTEMS_SIMPLE_BINARY_SEMAPHORE|RTEMS_FIFO,0,&acks[i]));
 for(i=0;i<3;i++)CHECK(rtems_task_create(0x574b5230+i,i==1?2:3,8192,RTEMS_INTERRUPT_LEVEL(31),RTEMS_DEFAULT_ATTRIBUTES,&tasks_id[i]));
 CHECK(rtems_task_start(tasks_id[0],Owner,0));CHECK(rtems_task_start(tasks_id[1],Waiter,0));CHECK(rtems_task_start(tasks_id[2],Other,0));pump();
 resource.epoch=1;resource.committed=resource.staged=0x10203040;
 for(;;){unsigned char*b=(unsigned char*)BIO_BASE;unsigned int op=bio_word(b+BIO_INPUT+4),e=bio_word(b+BIO_INPUT+8),v=bio_word(b+BIO_INPUT+12);
  unsigned int rc=process(op,e,v);report(op,rc);
  _CPU_Context_switch(&_Thread_Executing->Registers,&_Thread_BSP_context);
  REQUIRE(!finalized);
 }
}
static rtems_initialization_tasks_table init_tasks[]={{0x494e4954,8192,1,RTEMS_DEFAULT_ATTRIBUTES,Init,RTEMS_INTERRUPT_LEVEL(31),0}};
static rtems_api_configuration_table api={4,0,6,0,0,0,0,0,1,init_tasks};
static rtems_configuration_table config={workspace,sizeof(workspace),0,10000,1,0,0,0,0,0,0,0,&api,0,0};
static rtems_cpu_table cpu={0,0,0,idle_error,1,2048,2048,0,stack_alloc,stack_free};
void _ISR_Handler(void){bounded_fatal(0x40000);}
void _CPU_ISR_install_raw_handler(unsigned int v,proc_ptr n,proc_ptr*o){bounded_fatal(0x40000|v);}
unsigned int bounded_main(unsigned int arg){unsigned char*p=(unsigned char*)arg;
 if(arg!=BIO_BASE||!bio_request_valid(p)||bio_word(p+12)!=16||bio_word(p+16)<256||bio_word(p+BIO_INPUT)!=0x314e574f||finalized)return 1;
 if(!initialized){for(p=_bss_start;p<_bss_end;p++)*p=0;initialized=1;rtems_initialize_executive(&config,&cpu);}
 else _CPU_Context_switch(&_Thread_BSP_context,&_Thread_Executing->Registers);
 return 0;
}

/* Bounded two-task time-slicing test, not a production/resident BSP. */
#include <string.h>
#include <rtems/system.h>
#include <rtems/config.h>
#include <rtems/init.h>
#include <rtems/rtems/tasks.h>
#include <rtems/rtems/clock.h>
#include <rtems/score/thread.h>
#include <rtems/score/isr.h>
#include "buffer_io.h"
#include "lifetime.h"
extern unsigned char _bss_start[],_bss_end[];
extern void bounded_escape(unsigned int) __attribute__((noreturn));
#include "../irq/timer_hw.h"
static unsigned char workspace[49152] __attribute__((aligned(16)));
static unsigned char stacks[4][8320] __attribute__((aligned(16)));
static unsigned int allocated,sizes[4],initialized;
unsigned char switch_irq_areas[2][8192] __attribute__((aligned(16)));
volatile unsigned int switch_threads[2],switch_active[2],switch_fault,switch_stop;
static volatile unsigned int ticks,two_live,handoffs,done[2],sampled_high[2];
static struct irq_lifetime life[2];
/* globals before/after, locals before/after, PC/TC before/after, AC-failure,
 * remaining loop budget. The assembly offsets are checked by host tests. */
unsigned int switch_records[2][70];
#ifdef I960_DEFER_TEST
#define REPORT_SIZE 816
/* Wire words: magic, fault, owner, begin, inner end, outer end, resumed,
 * levels 2/1/0, phase tick counts, pending/heir observations, B entries
 * before/after outer enable, max sampled ISR depth, reserved. */
static volatile unsigned int deferral[20],defer_phase;
void bounded_fatal(unsigned int code);
static void defer_wait(void){unsigned int start=ticks,budget=1000000;
 priority20();while(ticks-start<4 && --budget) __asm__ volatile("":::"memory");
 mask31();if(!budget)bounded_fatal(0x56000);
}
static void defer_probe(void){
 deferral[0]=0x31464544;deferral[2]=(unsigned int)_Thread_Executing;
 _Thread_Disable_dispatch();_Thread_Disable_dispatch();
 deferral[3]=ticks;defer_phase=1;defer_wait();
 deferral[4]=ticks;deferral[7]=_Thread_Dispatch_disable_level;
 _Thread_Enable_dispatch();deferral[8]=_Thread_Dispatch_disable_level;
 defer_phase=2;defer_wait();deferral[5]=ticks;
 deferral[14]=life[1].entries;
 if(switch_threads[1]||deferral[14])deferral[1]|=8;
 defer_phase=0;_Thread_Enable_dispatch();
 deferral[6]=ticks;deferral[9]=_Thread_Dispatch_disable_level;
 deferral[15]=life[1].entries;
}
#else
#define REPORT_SIZE 736
#endif
extern void switch_probe(unsigned int*,unsigned int);
void bounded_fatal(unsigned int code){stop_timer();bounded_escape(0xf0000000u|code);}
#define CHECK(x) do{unsigned int e=(x);if(e)bounded_fatal(0x10000+__LINE__*256+e);}while(0)
static void*stack_alloc(unsigned int n){unsigned int i=allocated++;if(i>=4||n>8192)bounded_fatal(0x51000);sizes[i]=n;memset(stacks[i],0xa5,8320);return stacks[i]+16;}
static void stack_free(void*p){bounded_fatal(0x51001);}
static void idle_error(void){bounded_fatal(0xdead);}
static void measure(unsigned int id){unsigned int sp,base=(unsigned int)switch_irq_areas[id];
 __asm__ volatile("mov sp,%0":"=r"(sp));
 if(sp<base+192||sp>base+8128)switch_fault|=1;
 if(sp>sampled_high[id])sampled_high[id]=sp;
}
void switch_irq_enter(unsigned int id,unsigned int fp){
 measure(id);
 if(!lifetime_enter(&life[id],(unsigned int)_Thread_Executing,fp,REG(fp-16),REG(fp-12),REG(fp-8)))switch_fault|=2;
 if(life[0].live&&life[1].live)two_live++;
}
void switch_irq_body(void){
 _ISR_Nest_level++;_Thread_Dispatch_disable_level++;
 #ifdef I960_DEFER_TEST
 if(defer_phase && _Thread_Dispatch_disable_level>deferral[16])deferral[16]=_Thread_Dispatch_disable_level;
#endif
 ticks++;CHECK(rtems_clock_tick());
 _Thread_Dispatch_disable_level--;_ISR_Nest_level--;
#ifdef I960_DEFER_TEST
 if(defer_phase){
  deferral[9+defer_phase]++;
  if((unsigned int)_Thread_Executing!=deferral[2])deferral[1]|=1;
  if(_Thread_Dispatch_disable_level!=3-defer_phase)deferral[1]|=2;
  if(_ISR_Nest_level)deferral[1]|=4;
  if(_Context_Switch_necessary)deferral[12]++;
  if(_Thread_Heir!=_Thread_Executing)deferral[13]++;
 }
#endif
 if(_Context_Switch_necessary&&!_Thread_Dispatch_disable_level){
  if(_Thread_Heir!=_Thread_Executing)handoffs++;
  _Thread_Dispatch(); /* This call may stay suspended on this owner's C stack. */
 }
}
void switch_irq_leave(unsigned int id,unsigned int fp){unsigned int i,tc,*save=(unsigned int*)(switch_irq_areas[id]+64);
 measure(id);
 if(!lifetime_leave(&life[id],(unsigned int)_Thread_Executing,fp,REG(fp-16),REG(fp-12),REG(fp-8)))switch_fault|=4;
 for(i=0;i<64;i++)if(switch_irq_areas[id][i]!=0xa5||switch_irq_areas[id][8128+i]!=0xa5)switch_fault|=8;
 __asm__ volatile("modtc 0,0,%0":"=r"(tc));if((tc^save[16])&0x0f000000)switch_fault|=16;
}
static void deep_probe(unsigned int n,unsigned int id){volatile unsigned int pad[16];unsigned int i;
 for(i=0;i<16;i++)pad[i]=id*65536+n*256+i;
 if(n)deep_probe(n-1,id);else switch_probe(switch_records[id],0x19600000u+id*0x10000000u);
 for(i=0;i<16;i++)if(pad[i]!=id*65536+n*256+i)switch_fault|=32;
}
static void Worker(rtems_task_argument id){unsigned int *r=switch_records[id],i;
 switch_threads[id]=(unsigned int)_Thread_Executing;
 life[id].owner=switch_threads[id];life[id].low=(unsigned int)_Thread_Executing->Start.Initial_stack.area;
 life[id].high=life[id].low+_Thread_Executing->Start.Initial_stack.size;
#ifdef I960_DEFER_TEST
 if(id==0)defer_probe();
#endif
 deep_probe(16,id);
 if(!switch_stop||!r[69])bounded_fatal(0x52000+id); /* finite loop deadline */
 for(i=0;i<16;i++)if(r[i]!=r[16+i])switch_fault|=128;
 for(i=0;i<16;i++)if(i!=2&&i!=3&&i!=5&&r[32+i]!=r[48+i])switch_fault|=256;
 if(r[64]!=r[65]||r[66]!=r[67]||r[68])switch_fault|=512;
 done[id]=1;CHECK(rtems_task_suspend(RTEMS_SELF));bounded_fatal(0x53000+id);
}
static void Init(rtems_task_argument arg){rtems_id a,b;rtems_task_priority old;unsigned int i,j,error;unsigned char*out=(unsigned char*)BIO_BASE+BIO_OUTPUT;
 memset(switch_irq_areas,0xa5,sizeof(switch_irq_areas));
 CHECK(rtems_task_create(0x43545841,2,8192,RTEMS_TIMESLICE|RTEMS_INTERRUPT_LEVEL(31),RTEMS_DEFAULT_ATTRIBUTES,&a));
 CHECK(rtems_task_create(0x43545842,2,8192,RTEMS_TIMESLICE|RTEMS_INTERRUPT_LEVEL(31),RTEMS_DEFAULT_ATTRIBUTES,&b));
 CHECK(rtems_task_start(a,Worker,0));CHECK(rtems_task_start(b,Worker,1));
 error=start_timer();if(error)bounded_fatal(0x54000+error);
 CHECK(rtems_task_wake_after(32)); /* both workers spin, no voluntary yield */
 switch_stop=1;
 /* Both task-owned IRQ continuations must return before timer/code teardown. */
 CHECK(rtems_task_set_priority(RTEMS_SELF,3,&old));
 stop_timer();
 if(!done[0]||!done[1]||switch_active[0]||switch_active[1]||!lifetime_drained(life))switch_fault|=1024;
 if(_ISR_Nest_level||_Thread_Dispatch_disable_level)switch_fault|=2048;
 for(i=0;i<allocated;i++){
  for(j=0;j<16;j++)if(stacks[i][j]!=0xa5)switch_fault|=4096;
  for(j=16+sizes[i];j<8320;j++)if(stacks[i][j]!=0xa5)switch_fault|=4096;
 }
 {unsigned int header[]={0x31575349,switch_fault,ticks,two_live,handoffs,done[0],done[1],switch_active[0],switch_active[1],_ISR_Nest_level,_Thread_Dispatch_disable_level,REG(0xff008504),REG(0xff008528),REG(0x3c),saved_vector,REG(0xff000310),REG(0xff000314),REG(0xff000318),REG(0xff008500),armed};
 for(i=0;i<20;i++)bio_put(out+i*4,header[i]);}
 for(i=0;i<2;i++){
  unsigned int*state=(unsigned int*)&life[i];for(j=0;j<10;j++)bio_put(out+80+i*328+j*4,state[j]);
  bio_put(out+120+i*328,(unsigned int)switch_irq_areas[i]);bio_put(out+124+i*328,sampled_high[i]);
  for(j=0;j<70;j++)bio_put(out+128+i*328+j*4,switch_records[i][j]);
 }
#ifdef I960_DEFER_TEST
 for(i=0;i<20;i++)bio_put(out+736+i*4,deferral[i]);
#endif
 bio_put((unsigned char*)BIO_BASE+20,0);bio_put((unsigned char*)BIO_BASE+24,REPORT_SIZE);
 bio_put((unsigned char*)BIO_BASE+28,bio_word((unsigned char*)BIO_BASE+8));
 _CPU_Context_switch(&_Thread_Executing->Registers,&_Thread_BSP_context);
 for(;;)bounded_fatal(0x55000);
}
static rtems_initialization_tasks_table tasks[]={{0x494e4954,8192,1,RTEMS_DEFAULT_ATTRIBUTES,Init,RTEMS_INTERRUPT_LEVEL(31),0}};
static rtems_api_configuration_table api={3,0,0,0,0,0,0,0,1,tasks};
static rtems_configuration_table config={workspace,sizeof(workspace),0,10000,1,0,0,0,0,0,0,0,&api,0,0};
static rtems_cpu_table cpu={0,0,0,idle_error,1,2048,2048,0,stack_alloc,stack_free};
void _ISR_Handler(void){bounded_fatal(0x40000);}
void _CPU_ISR_install_raw_handler(unsigned int v,proc_ptr n,proc_ptr*o){bounded_fatal(0x40000|v);}
unsigned int bounded_main(unsigned int arg){unsigned char*p=(unsigned char*)arg;
 if(arg!=BIO_BASE||!bio_request_valid(p)||bio_word(p+16)<REPORT_SIZE||initialized)return 1;
 for(p=_bss_start;p<_bss_end;p++)*p=0;initialized=1;rtems_initialize_executive(&config,&cpu);return 0;
}

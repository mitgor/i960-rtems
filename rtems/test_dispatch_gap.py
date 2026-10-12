#!/usr/bin/env python3
"""Compile the actual upstream and patched dispatcher with IRQ interposition.
The old source exposes heir identity on outgoing FP; the patch must preserve
masking through transfer and restore the original level after resume."""
import argparse,subprocess,tempfile
from pathlib import Path
from dispatch_gap import patch
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args();source=a.source.read_text()
start=source.index('void _Thread_Dispatch( void )');source=source[start:]
header=r'''
#include <assert.h>
#include <stdio.h>
#define CPU_HARDWARE_FP 0
#define CPU_SOFTWARE_FP 0
#define TRUE 1
#define FALSE 0
#define THREAD_CPU_BUDGET_ALGORITHM_RESET_TIMESLICE 1
#define ISR_Level unsigned
#define Context unsigned
struct Thread {unsigned Registers,rtems_ada_self,budget_algorithm,cpu_time_budget,ticks_executed;void*libc_reent;unsigned do_post_task_switch_extension;};
typedef struct Thread Thread_Control;
static Thread_Control first,second,*_Thread_Executing,*_Thread_Heir,*physical;
static unsigned _Thread_Dispatch_disable_level,_Context_Switch_necessary,_Thread_Ticks_per_timeslice=1,rtems_ada_self,pc,wrong_irqs,good_irqs,switches;
static void**_Thread_libc_reent;static unsigned _Thread_Do_post_task_switch_extension;
static void irq(void){if(pc==20){if(_Thread_Executing!=physical)wrong_irqs++;else good_irqs++;}}
#define _ISR_Disable(level) do{level=pc;pc=31;}while(0)
#define _ISR_Enable(level) do{pc=level;irq();}while(0)
static void _User_extensions_Thread_switch(Thread_Control*a,Thread_Control*b){(void)a;(void)b;irq();}
static void _API_extensions_Run_postswitch(void){irq();}
static void transfer(unsigned*a,unsigned*b){assert(a==&physical->Registers);*a=pc;assert(b==&_Thread_Executing->Registers);physical=_Thread_Executing;pc=*b;irq();switches++;/* Model a later masked switch back: this C call resumes on its original stack. */pc=31;_Thread_Executing=physical=&first;pc=*a;irq();}
#define _Context_Switch transfer
'''
main=r'''
int main(void){unsigned initial;
 for(initial=20;initial<=31;initial+=11){first=(Thread_Control){0};second=(Thread_Control){0};physical=_Thread_Executing=&first;_Thread_Heir=&second;second.Registers=31;second.budget_algorithm=1;pc=initial;wrong_irqs=good_irqs=switches=0;_Context_Switch_necessary=1;_Thread_Dispatch_disable_level=0;_Thread_Do_post_task_switch_extension=1;
 _Thread_Dispatch();assert(switches==1&&physical==&first&&_Thread_Executing==&first&&pc==initial&&!_Thread_Dispatch_disable_level&&second.ticks_executed==1);
#ifdef PATCHED
 assert(!wrong_irqs&&first.Registers==31);if(initial==20)assert(good_irqs);
#else
 if(initial==20)assert(wrong_irqs&&first.Registers==20);
#endif
 }return 0;}
'''
with tempfile.TemporaryDirectory() as d:
 t=Path(d)
 for fixed in (False,True):
  s=patch(source) if fixed else source;(t/'test.c').write_text(('#define PATCHED 1\n' if fixed else '')+header+s+main)
  subprocess.run(['cc','-std=c99','-fsanitize=address,undefined',str(t/'test.c'),'-o',str(t/'test')],check=True);subprocess.run([str(t/'test')],check=True)
print('PASS: actual dispatcher source; old unmask gap reproduced; patched transfer masks heir/FP mismatch and preserves original levels 20/31')

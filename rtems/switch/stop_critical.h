/* Case 1/2: READY only inside the requested nested critical level. Keep the
 * same owner and B's suspended continuation until both levels are released. */
static void stop_wait_ticks(unsigned int start,unsigned int n){unsigned int budget=1000000;
 priority20();while(ticks-start<n&&--budget)__asm__ volatile("":::"memory");
 mask31();if(!budget)bounded_fatal(0x58000);
}
static void stop_critical(void){
 stop_wait_ticks(0,16); /* both workers have accumulated IRQ continuations */
 _Thread_Disable_dispatch();_Thread_Disable_dispatch();
 critical_phase=1;case_diag[1]=ticks;case_diag[9]=life[1].entries;
 stop_wait_ticks(case_diag[1],12);
 case_diag[2]=ticks;case_diag[5]=_Thread_Dispatch_disable_level;
 _Thread_Enable_dispatch();case_diag[6]=_Thread_Dispatch_disable_level;
 critical_phase=2;stop_wait_ticks(case_diag[2],12);
 case_diag[3]=ticks;case_diag[7]=_Thread_Dispatch_disable_level;
 case_diag[10]=life[1].entries;critical_phase=0;
 _Thread_Enable_dispatch();case_diag[4]=ticks;case_diag[8]=_Thread_Dispatch_disable_level;
}
static void stop_critical_observe(void){
 if(!critical_phase)return;
 case_diag[12+critical_phase]++;
 if((unsigned int)_Thread_Executing!=switch_threads[0]||
    _Thread_Dispatch_disable_level!=3-critical_phase||_ISR_Nest_level)case_diag[15]++;
 if(_Context_Switch_necessary)case_diag[16]++;
}

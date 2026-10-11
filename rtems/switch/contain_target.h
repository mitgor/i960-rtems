/* Disposable, one-shot quarantine. Never resume/delete a suspended worker.
 * Their original frames and ISR stacks survive until the firmware callback
 * returns. This requires delivered interrupts and an intact RTEMS scheduler. */
static unsigned int contain_diag[32];
static unsigned int contain_hash(unsigned int base,unsigned int size){
 unsigned int h=2166136261u,i;for(i=0;i<size;i++)h=(h^*(volatile unsigned char*)(base+i))*16777619u;return h;
}
static unsigned int contain_progress(unsigned int i){return REG((unsigned int)&switch_records[i][69]);}
static unsigned int contain_quiescent(void){unsigned int i;
 if(armed||done[0]||done[1]||_ISR_Nest_level||_Thread_Dispatch_disable_level||!switch_stop)return 0;
 if((unsigned int)_Thread_Executing!=contain_diag[1]||_Thread_Heir!=_Thread_Executing||_Context_Switch_necessary)return 0;
 for(i=0;i<2;i++){
  Thread_Control*t=(Thread_Control*)switch_threads[i];struct irq_lifetime*l=&life[i];
  if(!t||t->current_state!=STATES_SUSPENDED||t->suspend_count!=1||
     !switch_active[i]||!l->live||l->entries!=l->returns+1||
     REG(l->frame-16)!=l->pc||REG(l->frame-12)!=l->ac||REG(l->frame-8)!=l->vector)return 0;
 }
 return 1;
}
static void contain_workers(rtems_id a,rtems_id b){unsigned int i,j;rtems_task_priority old;
 contain_diag[0]=0x314e5443;contain_diag[1]=(unsigned int)_Thread_Executing;
 contain_diag[2]=ticks;contain_diag[4]=4;
 for(i=0;i<2;i++)contain_diag[5+i]=contain_progress(i);
 /* Let both workers actually run with switch_stop set. They must ignore it. */
 CHECK(rtems_task_wake_after(4));contain_diag[3]=ticks;
 CHECK(rtems_task_suspend(a));CHECK(rtems_task_suspend(b));
 stop_timer();
 for(i=0;i<2;i++){
  contain_diag[7+i]=contain_progress(i);
  contain_diag[11+i]=((Thread_Control*)switch_threads[i])->current_state;
  if(!contain_diag[7+i]||contain_diag[7+i]>=contain_diag[5+i])bounded_fatal(0x58002);
  contain_diag[18+i]=contain_hash(life[i].low,life[i].high-life[i].low);
  contain_diag[22+i]=contain_hash((unsigned int)switch_irq_areas[i],8192);
  for(j=0;j<64;j++)if(switch_irq_areas[i][j]!=0xa5||switch_irq_areas[i][8128+j]!=0xa5)switch_fault|=8;
  for(j=0;j<15;j++)if(REG((unsigned int)switch_irq_areas[i]+64+j*4)!=0x19600000u+i*0x10000000u+j)switch_fault|=128;
 }
 /* Workers have higher RTEMS priority: if either remains runnable this yields
  * to it. CPU priority stays 31, timer is restored, and no ISR slot is reused. */
 CHECK(rtems_task_set_priority(RTEMS_SELF,3,&old));
 contain_diag[15]=(unsigned int)_Thread_Executing;contain_diag[16]=(unsigned int)_Thread_Heir;
 for(i=0;i<10000;i++){
  if(!contain_quiescent()||contain_progress(0)!=contain_diag[7]||contain_progress(1)!=contain_diag[8])bounded_fatal(0x58003);
  contain_diag[17]++;
 }
 for(i=0;i<2;i++){
  contain_diag[9+i]=contain_progress(i);contain_diag[13+i]=((Thread_Control*)switch_threads[i])->current_state;
  contain_diag[20+i]=contain_hash(life[i].low,life[i].high-life[i].low);
  contain_diag[24+i]=contain_hash((unsigned int)switch_irq_areas[i],8192);
  if(contain_diag[18+i]!=contain_diag[20+i]||contain_diag[22+i]!=contain_diag[24+i])bounded_fatal(0x58004);
 }
 contain_diag[26]=0x514f4b31;contain_diag[27]=switch_stop;
 contain_diag[28]=_ISR_Nest_level;contain_diag[29]=_Thread_Dispatch_disable_level;contain_diag[30]=armed;
}

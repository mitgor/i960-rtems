/* One-shot STOP1 experiment. No queues, BAR RAM, interrupt unmasking or DMA.
 * READY is published from an IRQ. DRAINED means both task continuations have
 * returned and the timer is restored. Host RELEASE permits MU restoration. */
static unsigned int stop_epoch,stop_diag[20];
static rtems_id stop_controller;
static unsigned int stop_mu_start(void){
 if(REG(0x1328)!=0x1fb||REG(0x1334)!=0xff||REG(0x1314)||REG(0x131c)||
    (REG(0x1324)&2)||(REG(0x1330)&2))return 1;
 stop_diag[0]=0x31505453;stop_diag[1]=stop_epoch;return 0;
}
static void stop_mu_poll(void){unsigned int token;
 if(REG(0x1328)!=0x1fb||REG(0x1334)!=0xff){switch_fault|=8192;return;}
 if(ticks==8){stop_diag[2]=ticks;REG(0x131c)=0x71000000u|stop_epoch;(void)REG(0x131c);}
 token=REG(0x1314);
 if(token==(0x72000000u|stop_epoch)&&!stop_diag[3]){
  stop_diag[3]=ticks;stop_diag[4]=(unsigned int)_Thread_Executing;
  stop_diag[5]=life[0].live;stop_diag[6]=life[1].live;
  stop_diag[7]=_Thread_Dispatch_disable_level;stop_diag[8]=_ISR_Nest_level;
  REG(0x1324)=2;(void)REG(0x1324);
  switch_stop=1;CHECK(rtems_event_send(stop_controller,RTEMS_EVENT_0));
 }
}
static void stop_mu_finish(void){unsigned int budget=1000000;
 stop_diag[9]=ticks;stop_diag[10]=life[0].returns;stop_diag[11]=life[1].returns;
 if(switch_fault||switch_active[0]||switch_active[1]||!lifetime_drained(life))bounded_fatal(0x57001);
 REG(0x131c)=0x73000000u|stop_epoch;(void)REG(0x131c);
 while(REG(0x1314)!=(0x74000000u|stop_epoch)&&--budget){}
 stop_diag[12]=budget;if(!budget)switch_fault|=16384;
 if(REG(0x1328)!=0x1fb||REG(0x1334)!=0xff)switch_fault|=8192;
 REG(0x1314)=0;(void)REG(0x1314);REG(0x131c)=0;(void)REG(0x131c);
 REG(0x1324)=2;(void)REG(0x1324);
 if(REG(0x1314)||REG(0x131c)||(REG(0x1324)&2))switch_fault|=32768;
 stop_diag[13]=0x4d554f4b; /* host must clear OISR only after callback return */
}

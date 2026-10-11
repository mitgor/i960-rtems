/* Bounded monitor-entry proof. DMA/SCSI ownership is deliberately NOT granted. */
#include <string.h>
#include "buffer_io.h"
extern unsigned char _bss_start[],_bss_end[];
#define I960_BACKGROUND 1
#include "../irq/timer_hw.h"
#include "../irq/owned_stack.h"
#include "../control/mu_echo.h"
#include "../handoff/policy.h"
#include "engines.h"
#ifdef I960_SECONDARY_RESET
#include "../residentnet/scsi_target.h"
#endif
#ifdef I960_RESIDENT_NET
#include "../residentnet/cache_probe.h"
#endif
#ifdef I960_RESIDENT_NET
#define EXCLUSIVE_MAX_TICKS 180000u
#else
#define EXCLUSIVE_MAX_TICKS 6000u
#endif
#define MONITOR_READ() REG(0x1314)
#define MONITOR_WRITE(v) (REG(0x1314)=(v))
#include "../handoff/entry.h"
extern unsigned int exclusive_init(void),exclusive_run(unsigned int);
extern void exclusive_resident(unsigned int,unsigned int);
extern void exclusive_report(unsigned int*);
#ifdef I960_FAULT_OWNER
extern unsigned int exclusive_fault_install(unsigned int);
#ifdef I960_EXTRA_RAM
extern unsigned int exclusive_extra_prepare(void);
extern void exclusive_abort(void);
#endif
#endif
static unsigned int requested_phase,requested_ticks,runtime_error;
static unsigned int initialized,epoch,ticks,state,entries,denials,expired,spins,drift,busy,decision;
static unsigned int dma_before[6],dma_after[6],entered_frame,entered_pc,entered_ac,entered_vector,enter_mask,leave_mask;
static const unsigned int dma_regs[6]={0x1400,0x1404,0x1440,0x1444,0x1480,0x1484};
static void sample(unsigned int*out){unsigned int i;for(i=0;i<6;i++)out[i]=REG(dma_regs[i]);}
static void publish(unsigned int tag){REG(0x131c)=tag|epoch;(void)REG(0x131c);REG(0x1324)=2;(void)REG(0x1324);}
void timer_interrupt(void){unsigned int token,i,n;
 ticks++;token=REG(0x1314);
 if(REG(0x1328)!=0x1fb||REG(0x1334)!=0xff){drift++;return;}
 if(token==(0x84000000u|epoch)){
  sample(dma_before);busy=0;for(i=0;i<6;i++)busy|=dma_before[i];
  /* No release/drain/reservation contract has been established for any engine.
   * Zero registers cannot set proof bits. Host input cannot override this. */
  decision=transfer_check(0,busy,drift);denials++;state=3;publish(0x85000000u);REG(0x1314)=0;(void)REG(0x1314);return;
 }
 if(token==(0x88000000u|epoch)){stop_timer();state=4;publish(0x89000000u);return;}
 if(token==(0x8a000000u|epoch)){
  REG(0x1314)=0;(void)REG(0x1314);mask31();entries++;state=6;
#ifdef I960_SECONDARY_RESET
  if(requested_phase!=2||!requested_ticks||!scsi_target_identity()||engine_acquire(2)){publish(0x8c000000u);for(;;){}}
#else
  if(requested_phase!=2||!requested_ticks||engine_acquire(2)){publish(0x8c000000u);for(;;){}}
#endif
#ifdef I960_FAULT_OWNER
  if(exclusive_fault_install(epoch)){publish(0x8c000000u);for(;;){}}
#endif
#ifdef I960_SECONDARY_RESET
  if(scsi_stop_hold(&scsi_stop,0x31504353u)){publish(0x8c000000u);for(;;){}}
#endif
#ifdef I960_EXTRA_RAM
  if(exclusive_extra_prepare()){publish(0x8b000000u);exclusive_abort();for(;;){}}
#endif
  publish(0x8b000000u);exclusive_resident(requested_ticks,epoch);for(;;){}
 }
 if(!monitor_take(epoch))return;
 /* Only this original firmware IRQ continuation is parked. No DMA writes. */
 mask31();entries++;state=1;engine_acquire(requested_phase);sample(dma_before);enter_mask=REG(0xff008504);
 entered_frame=irq_owned_entry_fp;entered_pc=REG(entered_frame-16);entered_ac=REG(entered_frame-12);entered_vector=REG(entered_frame-8);
 publish(0x82000000u);
 if(requested_ticks&&!engine_error)runtime_error=exclusive_run(requested_ticks);
 for(n=0;n<1000000;n++){
  if(REG(0x1314)==(0x83000000u|epoch))break;
  if(!(n&255))for(i=0;i<6;i++)if(REG(dma_regs[i])!=dma_before[i])drift++;
 }
 spins=n;engine_release();sample(dma_after);leave_mask=REG(0xff008504);
 if(entered_pc!=REG(entered_frame-16)||entered_ac!=REG(entered_frame-12)||entered_vector!=REG(entered_frame-8))irq_owned_fault|=128;
 if(n==1000000){expired++;state=5;publish(0x86000000u);}else{state=2;publish(0x87000000u);}
}
static void report(unsigned char*b,unsigned int rc){unsigned int w[160],i;memset(w,0,sizeof(w));
 w[0]=0x31415452;w[1]=rc;w[2]=ticks;w[7]=REG(0xff008504);w[8]=REG(0xff008528);w[9]=REG(0x3c);w[10]=saved_vector;w[11]=REG(0xff000310);w[12]=REG(0xff000314);w[13]=armed?0x36:REG(0xff000318);w[14]=REG(0xff008500);w[15]=armed;
 w[16]=0x31464f48;w[17]=state;w[18]=entries;w[19]=denials;w[20]=expired;w[21]=spins;w[22]=drift;w[23]=busy;w[24]=decision;w[25]=0;w[26]=TRANSFER_REQUIRED;w[27]=epoch;
 for(i=0;i<6;i++){w[28+i]=dma_before[i];w[34+i]=dma_after[i];}
 w[40]=entered_frame;w[41]=entered_pc;w[42]=entered_ac;w[43]=entered_vector;w[44]=enter_mask;w[45]=leave_mask;
 w[46]=irq_owned_active;w[47]=irq_owned_entries;w[48]=irq_owned_fault;w[49]=(unsigned int)irq_owned_area;w[50]=irq_owned_low;w[51]=irq_owned_high;w[52]=IRQ_AREA_SIZE;w[53]=REG(0xff008704);
 w[64]=0x31435845;w[65]=engine_phase;w[66]=engine_error;w[67]=engine_written;
 for(i=0;i<16;i++){w[68+i]=engine_before[i];w[84+i]=engine_during[i];w[100+i]=engine_after[i];}
 exclusive_report(w+116);w[148]=runtime_error;w[149]=requested_ticks;
#ifdef I960_RESIDENT_NET
 cache_decode_probe(w+150,bio_word(b+BIO_INPUT+4)==0?bio_word(b+BIO_INPUT+12):0);
#endif
 for(i=0;i<160;i++)bio_put(b+BIO_OUTPUT+i*4,w[i]);bio_put(b+20,0);bio_put(b+24,640);bio_put(b+28,bio_word(b+8));
}
unsigned int bounded_main(unsigned int a){unsigned char*b=(unsigned char*)a,*p;unsigned int op,rc=0;
 if(a!=BIO_BASE||!bio_request_valid(b)||bio_word(b+12)!=16||bio_word(b+16)<64||bio_word(b+BIO_INPUT)!=0x31415452)return 1;
 op=bio_word(b+BIO_INPUT+4);if(op>2)return 2;
 if(!initialized){for(p=_bss_start;p<_bss_end;p++)*p=0;initialized=1;irq_owned_prepare();}
 if(op==2){unsigned int owned=mu_owned;stop_timer();rc=mu_finish();timer_stop_response(b,initialized);bio_put(b+BIO_OUTPUT+4,rc);bio_put(b+BIO_OUTPUT+8,owned&&!rc?0x4d554f4bu:0);return 0;}
 if(bio_word(b+16)<640)return 5;
 if(op==1){if(armed||entries||denials)return 3;requested_phase=bio_word(b+BIO_INPUT+12)&255;requested_ticks=bio_word(b+BIO_INPUT+12)>>8;if(requested_phase>2||requested_ticks>EXCLUSIVE_MAX_TICKS)return 6;if(requested_ticks){rc=exclusive_init();if(rc)return rc;}epoch=bio_word(b+BIO_INPUT+8);if(!epoch||epoch>65535)return 4;rc=mu_start();if(!rc)rc=start_timer();}
 report(b,rc);return 0;
}

void exclusive_engine_report(unsigned int*w){unsigned int i;engine_snapshot(w);for(i=0;i<6;i++)if(w[i])runtime_error|=0x100;w[16]=runtime_error;}

/* AcceleRAID timer 1: read count only; reading mode clears terminal state. */
extern unsigned doom_platform_ticks_ms(void);
static unsigned last,faults;
unsigned doom_platform_wall_clock_faults(void){return faults;}
unsigned doom_platform_wall_clock(void){
 unsigned before=0,after=0,count,tries,clock;
 for(tries=0;tries<16;tries++){
  before=doom_platform_ticks_ms();
  count=*(volatile unsigned*)0xff000314u;
  after=doom_platform_ticks_ms();
  if(before==after && count<=125000u &&
     !(*(volatile unsigned*)0xff008500u&0x2000u)){
   clock=(before/10u)*41667u+(125000u-count)/3u;
   if(clock<last){faults++;clock=last;}
   last=clock;return clock;
  }
 }
 faults++;clock=(after/10u)*41667u;
 if(clock<last)clock=last;
 last=clock;return clock;
}

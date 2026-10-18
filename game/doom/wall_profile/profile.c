#include "wall_profile.h"
/* Task-context inclusive brackets. The free-running downcounter also counts
 * interrupts/preemption; these are elapsed ticks, not exclusive CPU cycles. */
static unsigned calls[4],ticks[4];
unsigned doom_wall_begin(void){
#ifdef __i960__
#ifdef DOOM_WALL_PROFILE_ACCELE160
 extern unsigned doom_platform_wall_clock(void);
 return doom_platform_wall_clock();
#else
 return *(volatile unsigned*)0xff000304u;
#endif
#else
 return 0;
#endif
}
void doom_wall_end(unsigned site,unsigned begin){
 unsigned end=doom_wall_begin();
#ifdef DOOM_WALL_PROFILE_ACCELE160
 ticks[site]+=end-begin;
#else
 ticks[site]+=begin-end;
#endif
 calls[site]++;
}
void doom_wall_record(unsigned*q,unsigned generation){
 unsigned i,begin=doom_wall_begin(),cal;
#ifdef DOOM_WALL_PROFILE_ACCELE160
 cal=doom_wall_begin()-begin;
#else
 cal=begin-doom_wall_begin();
#endif
 for(i=0;i<128;i++)q[i]=0;
 q[0]=0x314c4157u;q[1]=1;q[2]=generation;q[3]=4;q[4]=4166700u;q[5]=cal;
#ifdef DOOM_WALL_PROFILE_ACCELE160
 {extern unsigned doom_platform_wall_clock_faults(void);
  q[6]=doom_platform_wall_clock_faults();}
#endif
 for(i=0;i<4;i++){q[8+2*i]=calls[i];q[9+2*i]=ticks[i];calls[i]=ticks[i]=0;}
}

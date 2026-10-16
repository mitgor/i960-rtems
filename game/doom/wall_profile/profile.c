#include "wall_profile.h"
/* Task-context inclusive brackets. The free-running downcounter also counts
 * interrupts/preemption; these are elapsed ticks, not exclusive CPU cycles. */
static unsigned calls[4],ticks[4];
unsigned doom_wall_begin(void){
#ifdef __i960__
 return *(volatile unsigned*)0xff000304u;
#else
 return 0;
#endif
}
void doom_wall_end(unsigned site,unsigned begin){
 unsigned end=doom_wall_begin();ticks[site]+=begin-end;calls[site]++;
}
void doom_wall_record(unsigned*q,unsigned generation){
 unsigned i,begin=doom_wall_begin(),cal=begin-doom_wall_begin();
 for(i=0;i<128;i++)q[i]=0;
 q[0]=0x314c4157u;q[1]=1;q[2]=generation;q[3]=4;q[4]=4166700u;q[5]=cal;
 for(i=0;i<4;i++){q[8+2*i]=calls[i];q[9+2*i]=ticks[i];calls[i]=ticks[i]=0;}
}

#include "fixed_profile.h"
int doom_div_legacy(int,int);
int doom_div_fast(int,int);
static unsigned counts[FD_SITES],ticks[FD_SITES],checks,seed=1,calibration;
static unsigned now(void){
#ifdef __i960__
 return *(volatile unsigned*)0xff000304u;
#else
 return 0;
#endif
}
int doom_div_profile(int a,int b,unsigned site){
 unsigned begin=now();int result;
#ifdef DOOM_FAST_FIXED_DIV
 result=doom_div_fast(a,b);
#else
 result=doom_div_legacy(a,b);
#endif
 ticks[site]+=begin-now();counts[site]++;return result;
}
/* Bounded differential checks in task context, once per delivered frame.
 * Compare target code with its own untouched pinned implementation. */
int doom_div_check(void){
 static const int edge[]={0,1,-1,16383,16384,65535,65536,-65536,1073741823,2147483647,(-2147483647-1)};
 unsigned i,begin;int a,b;
 for(i=0;i<32;i++){
  if(checks<121){a=edge[checks/11];b=edge[checks%11];}
  else{seed=seed*1664525u+1013904223u;a=(int)seed;seed=seed*1664525u+1013904223u;b=(int)seed;}
  /* Legacy INT_MIN/0 reaches division by zero: do not execute undefined input. */
  if(a==(-2147483647-1)&&b==0)b=1;
  if(doom_div_fast(a,b)!=doom_div_legacy(a,b))return 0;
  checks++;
 }
 begin=now();calibration+=begin-now();return 1;
}
void doom_div_record(unsigned*q){
 unsigned i;q[0]=0x31564446u;q[1]=1;q[2]=FD_SITES;
#ifdef DOOM_FAST_FIXED_DIV
 q[3]=1;
#else
 q[3]=0;
#endif
 q[4]=4166700u;q[5]=checks;q[6]=calibration;q[7]=0;
 for(i=0;i<FD_SITES;i++){q[8+2*i]=counts[i];q[9+2*i]=ticks[i];counts[i]=ticks[i]=0;}
}

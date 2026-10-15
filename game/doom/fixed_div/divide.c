/* Exact bounded FixedDiv. INT_MIN retains the pinned legacy implementation,
 * whose abs(INT_MIN) behavior is toolchain-specific. No signed overflow here. */
#include <limits.h>
int doom_div_legacy(int,int);
#ifdef __i960__
unsigned doom_div_unsigned(unsigned,unsigned);
#else
static unsigned doom_div_unsigned(unsigned a,unsigned b){return (unsigned)(((unsigned long long)a<<16)/b);}
#endif
int doom_div_fast(int a,int b){
 unsigned ua=(unsigned)a,ub=(unsigned)b,q;
 if(a==INT_MIN||b==INT_MIN)return doom_div_legacy(a,b);
 if(a<0)ua=0u-ua;if(b<0)ub=0u-ub;
 if((ua>>14)>=ub)return (a^b)<0?INT_MIN:INT_MAX;
 /* ub>ua>>14 implies (ua<<16)/ub < 2^30, hence ediv cannot overflow. */
 q=doom_div_unsigned(ua,ub);
 return (a^b)<0?-(int)q:(int)q;
}

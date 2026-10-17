/* Identical bounded workload on RP/JT. No cache enabling or timing-register
 * writes. Volatile memory accesses are intentional; result checks are outside
 * timed regions. Caller owns storage and supplies its monotonic millisecond
 * clock. Global invalidation is confined to case 7, never removed from IPC. */
#define CB_WORDS 16384u
#define CB_STEPS 1048576u
static unsigned cb_status(void){
#ifdef __i960__
 unsigned v;__asm__ volatile("dcctl 4,0,%0":"=r"(v)::"memory");return v;
#else
 return 0xffffffffu;
#endif
}
static void cb_invalidate(void){
#ifdef __i960__
 unsigned v;__asm__ volatile("dcctl 2,0,%0":"=r"(v)::"memory");
#endif
}
static unsigned cb_run(unsigned kind,volatile unsigned *p,volatile unsigned *q){
 unsigned i,j,h=1;
 if(kind==0){for(i=0;i<CB_STEPS;i++){h^=h<<13;h^=h>>17;h^=h<<5;}return h;}
 if(kind==5){for(j=0;j<64;j++)for(i=0;i<CB_WORDS;i++)q[i]=p[i];return q[123];}
 if(kind==6){for(j=0;j<64;j++)for(i=0;i<CB_WORDS;i++)q[i]=j;return q[123];}
 if(kind==1||kind==7){for(j=0;j<4096;j++){if(kind==7)cb_invalidate();for(i=0;i<256;i++)h+=p[i];}return h;}
 for(i=0;i<CB_STEPS;i++){
  if(kind==1)h+=p[i&255];
  else if(kind==2)h+=p[i&1023];
  else if(kind==3)h+=p[i&16383];
  else h+=p[(i*80u)&16383];
 }
 return h;
}

#include "../cache_bench/bench.h"
static void cache_bench_record(unsigned char *frame,unsigned generation){
 unsigned *raw,*p,*q,*r=(unsigned*)(frame+65024),i,k=(generation-1)&7;
 unsigned start,elapsed,result,before,after;
 if(!owned||!owned->owner()||owned->stopping())fatal(210);
 raw=malloc((CB_WORDS*2+8)*4);if(!raw)fatal(216);
 p=raw+4;q=p+CB_WORDS;
 for(i=0;i<4;i++)raw[i]=q[CB_WORDS+i]=0xa55ac33cu;
 for(i=0;i<CB_WORDS;i++){p[i]=i;q[i]=0xdeadbeefu;}
 before=cb_status();start=io->ticks_ms();result=cb_run(k,p,q);
 elapsed=io->ticks_ms()-start;after=cb_status();
 if(before!=after)fatal(217);
 for(i=0;i<4;i++)if(raw[i]!=0xa55ac33cu||q[CB_WORDS+i]!=0xa55ac33cu)fatal(218);
 for(i=0;i<CB_WORDS;i++)if(p[i]!=i||q[i]!=(k==5?i:k==6?63u:0xdeadbeefu))fatal(219);
 for(i=0;i<128;i++)r[i]=0;
 r[0]=0x31424343u;r[1]=2;r[2]=generation;r[3]=k;r[4]=CB_STEPS;
 r[5]=elapsed;r[6]=result;r[7]=before;r[8]=after;r[9]=(unsigned long)p;
 r[10]=CB_WORDS;r[11]=1;
#ifdef __i960__
 /* Intel Jx/Rx logical memory attributes: read-only observation. */
 r[12]=*(volatile unsigned*)0xff008100u;
 r[13]=*(volatile unsigned*)0xff008108u;
 r[14]=*(volatile unsigned*)0xff00810cu;
 r[15]=*(volatile unsigned*)0xff008110u;
 r[16]=*(volatile unsigned*)0xff008114u;
#endif
 free(raw);if(!owned->owner()||owned->stopping())fatal(210);
}

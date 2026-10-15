#ifdef DOOM_COLUMN_TEST
#include "column.h"
#endif
/* CPU fields are timer-sampled task attribution, not cycle counters. */
#if defined(DOOM_LOW_DETAIL) || defined(DOOM_DETAIL_TEST) || defined(DOOM_RUNTIME_DETAIL)
extern int screenblocks,detailLevel,detailshift;
extern void R_SetViewSize(int,int);
static unsigned detail_mode(unsigned g){
#ifdef DOOM_DETAIL_TEST
 static const unsigned char modes[64]={0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0};
 return modes[g&63];
#else
 (void)g;
#ifdef DOOM_LOW_DETAIL
 return 1;
#else
 return 0;
#endif
#endif
}
#endif
#ifdef DOOM_CPU_PROFILE
static unsigned present_cpu[7],present_cpu_begin;
static unsigned present_sample(void){const struct doom_runtime_checkpoint*t=(const void*)owned;int n=t->mark(102,0,0,0);if(n<0)fatal(210);return (unsigned)n;}
#endif
/* Per-frame timing uses the owned 10 ms clock, never Doom's virtual game time.
 * Only the delivery-slot copy is removed; I_VideoBuffer stays persistent. */
#define PRESENT_OFFSET 64768u
#define PRESENT_MAGIC 0x31524650u
static unsigned present_times[12],present_previous_wait;
static unsigned char *present_scratch;
static unsigned present_mode(unsigned generation){
#ifdef DOOM_PRESENT_TEST
 /* The pinned i960 compiler miscompiled the two unsigned range tests.
  * A bounded table avoids condition-code scheduling; test engine stops at 52. */
 static const unsigned char modes[64]={1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,2,2,2,2,2,2,2,2,2,2,2,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1};
 return modes[generation&63];
#else
 unsigned mode=0;
#ifndef DOOM_NO_FNV
 mode|=1;
#endif
#ifdef DOOM_DIRECT_FRAME
 mode|=2;
#endif
 return mode;
#endif
}
static void present_mark(unsigned stage){
#ifdef DOOM_COLUMN_TEST
 if(stage==80)doom_column_begin(stats.frames+1);
#endif
#if defined(DOOM_LOW_DETAIL) || defined(DOOM_DETAIL_TEST) || defined(DOOM_RUNTIME_DETAIL)
 if(stage==80){unsigned d;
#ifdef DOOM_RUNTIME_DETAIL
 /* Select the initial preference once; thereafter Doom's menu/F5 owns it. */
 static unsigned initialized;
 if(initialized)d=(unsigned)detailLevel;
 else {d=detail_mode(stats.frames+1);initialized=1;}
#else
 d=detail_mode(stats.frames+1);
#endif
 if((unsigned)detailLevel!=d){detailLevel=d;R_SetViewSize(screenblocks,detailLevel);}}
#endif
#ifdef DOOM_FRAME_PROFILE
 unsigned slot;
 switch(stage){case 37:slot=0;break;case 42:slot=1;break;case 43:slot=2;break;case 44:slot=3;break;case 80:slot=4;break;case 96:slot=5;break;case 98:slot=6;break;default:return;}
 present_times[slot]=io->ticks_ms();
#ifdef DOOM_CPU_PROFILE
 present_cpu[slot]=present_sample();
#endif
#else
 (void)stage;
#endif
}
static void present_record(unsigned char *frame,unsigned generation,unsigned mode,unsigned begin){
#ifdef DOOM_FRAME_PROFILE
 unsigned *p=(unsigned*)(frame+PRESENT_OFFSET);
 p[0]=PRESENT_MAGIC;p[1]=1;p[2]=generation;p[3]=mode;
 p[4]=present_times[3]-present_times[0]; /* renderer, includes any service stalls */
 p[5]=present_times[1]-present_times[0];p[6]=present_times[2]-present_times[1];p[7]=present_times[3]-present_times[2];
 p[8]=present_times[6]-present_times[5]; /* persistent screen -> presentation */
 p[9]=io->ticks_ms()-begin; /* adapter copy/hash/palette */
 p[10]=present_previous_wait; /* previous publication backpressure */
 p[11]=present_times[5]-present_times[4]; /* display before I_FinishUpdate */
 #ifdef DOOM_CPU_PROFILE
 {unsigned*q=p+16;unsigned end=present_sample();
 q[0]=0x31555043u;q[1]=1;
#if defined(DOOM_LOW_DETAIL) || defined(DOOM_DETAIL_TEST) || defined(DOOM_RUNTIME_DETAIL)
 q[2]=(unsigned)detailshift; /* renderer state, not merely requested mode */
#else
 q[2]=0;
#endif
 q[3]=10;q[4]=present_cpu[3]-present_cpu[0];
 q[5]=present_cpu[1]-present_cpu[0];q[6]=present_cpu[2]-present_cpu[1];q[7]=present_cpu[3]-present_cpu[2];
 q[8]=present_cpu[6]-present_cpu[5];q[9]=end-present_cpu_begin;q[10]=q[11]=0;
#ifdef DOOM_COLUMN_TEST
 q[10]=doom_column_mode;q[11]=doom_column_cases;
#endif
 }
#endif
#ifdef DOOM_WAD_PROFILE
 {extern const struct doom_cache*doom_wad_backend_stats(void);
  const struct doom_cache*c=doom_wad_backend_stats();unsigned k,*q=(unsigned*)(frame+64960);q[0]=0x31435057u;q[1]=1;
  for(k=0;k<4;k++){q[2+k]=c->profile_ms[k];q[6+k]=c->profile_counts[k];}
  q[10]=c->wire_bytes;q[11]=c->copied_bytes;q[12]=c->reads;q[13]=c->hits;q[14]=c->misses;q[15]=10;}
#endif
 p[12]=stats.frame_hash;p[13]=stats.palette_hash;p[14]=10;p[15]=0;
#else
 (void)frame;(void)generation;(void)mode;(void)begin;
#endif
}

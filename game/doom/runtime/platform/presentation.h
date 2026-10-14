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
#ifdef DOOM_FRAME_PROFILE
 unsigned slot;
 switch(stage){case 37:slot=0;break;case 42:slot=1;break;case 43:slot=2;break;case 44:slot=3;break;case 80:slot=4;break;case 96:slot=5;break;case 98:slot=6;break;default:return;}
 present_times[slot]=io->ticks_ms();
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
 p[12]=stats.frame_hash;p[13]=stats.palette_hash;p[14]=10;p[15]=0;
#else
 (void)frame;(void)generation;(void)mode;(void)begin;
#endif
}

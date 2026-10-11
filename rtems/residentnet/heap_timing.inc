/* Exclusive-only timer 0 ownership. Never read TMR while measuring: it clears TC.
 * Counts use the same bus/8 clock as the validated 100 Hz timer 1. */
static unsigned int timing_ready,timing_start,timing_op,timing_stats[8][4];
static volatile unsigned int irq_samples;
static unsigned int copy_preemptions[2];
static unsigned int irq_previous,irq_max_gap,irq_min_gap=~0u,irq_late,irq_elapsed[2],old_t0[2];
#ifndef HEAP_NATIVE
static unsigned int heap_counter(void){return *(volatile unsigned int*)0xff000304;}
static void timing_init(void){
 old_t0[0]=*(volatile unsigned int*)0xff000300;old_t0[1]=heap_counter();
 *(volatile unsigned int*)0xff008504&=~0x1000u;
 *(volatile unsigned int*)0xff000308=0;
 *(volatile unsigned int*)0xff000300=~0u;*(volatile unsigned int*)0xff000304=~0u;
 *(volatile unsigned int*)0xff000308=0x36;timing_ready=1;
}
#else
static unsigned int heap_counter(void){static unsigned int n=~0u;return n-=17;}
static void timing_init(void){timing_ready=1;}
#endif
static void add_time(unsigned int*s,unsigned int n){unsigned int old=s[0];s[0]+=n;if(s[0]<old)s[1]++;}
static unsigned int lock_heap(void){unsigned int v=heap_raw_lock();if(timing_ready)timing_start=heap_counter();return v;}
static void unlock_heap(unsigned int v){if(timing_ready){unsigned int d=timing_start-heap_counter(),*s=timing_stats[timing_op];s[0]++;if(d>s[1])s[1]=d;add_time(s+2,d);}heap_raw_unlock(v);}
void resident_heap_irq_sample(void){unsigned int now,gap,late;
 if(!timing_ready)return;now=heap_counter();gap=irq_previous-now;
 if(irq_samples){if(gap>irq_max_gap)irq_max_gap=gap;if(gap<irq_min_gap)irq_min_gap=gap;add_time(irq_elapsed,gap);}
 irq_previous=now;irq_samples++;
#ifndef HEAP_NATIVE
 late=41667-*(volatile unsigned int*)0xff000314;if(late>irq_late&&late<=41667)irq_late=late;
#else
 late=0;
#endif
}

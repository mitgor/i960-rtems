/* Shared, board-specific timer borrowing. All paths require priority 31.
 * Timer 0 remains firmware-owned. Timer 1 and cached vector F2 are temporary. */
#ifndef I960_TIMER_HW_H
#define I960_TIMER_HW_H
extern void timer_isr(void);
static volatile unsigned int armed;
static unsigned int timer_saved,saved_mask,saved_map,saved_vector,saved_reload,saved_count;
#define REG(a) (*(volatile unsigned int*)(a))
static void mask31(void){unsigned int value=31u<<16;__asm__ volatile("lda 0x1f0000,g0; modpc 0,g0,%0":"+r"(value)::"g0","memory");}
static void priority20(void){unsigned int v=20u<<16;__asm__ volatile("lda 0x1f0000,g0; modpc 0,g0,%0":"+r"(v)::"g0","memory");}
static void stop_timer(void){unsigned int v=0;
 if(!armed)return;mask31();REG(0xff000318)=0;
 /* The next instruction follows the documented disable/posting boundary. */
 __asm__ volatile("lda 0xff008500,g0; lda 0x2000,g1; atmod g0,g1,%0":"+r"(v)::"g0","g1","memory");
 REG(0x3c)=saved_vector;REG(0xff008528)=saved_map;
 REG(0xff000310)=saved_reload;REG(0xff000314)=saved_count;
 REG(0xff008504)=saved_mask;armed=0;
}
static unsigned int start_timer(void){unsigned int i,m;
 saved_mask=REG(0xff008504);saved_map=REG(0xff008528);
 if(REG(0xff008510)!=0x6000||(saved_mask&0x2000)||(REG(0xff008500)&0x2000))return 1;
 if(REG(0xff000310)||REG(0xff000314))return 2;
 for(i=0;i<8;i++){m=i<4?REG(0xff008520):REG(0xff008524);if(((m>>((i%4)*4))&15)==15)return 3;}
 if(((saved_map>>16)&15)==15)return 4;
 /* Only now inspect timer 1 mode; its count/reload/mask/pending are all zero.
  * Reading TMR1 clears terminal count; a nonzero mode refuses the experiment. */
 if(REG(0xff000318)!=0)return 5;
 saved_reload=0;saved_count=0;saved_vector=REG(0x3c);timer_saved=1;armed=1;
 REG(0xff008504)=0;REG(0x3c)=(unsigned int)timer_isr;
 REG(0xff008528)=(saved_map&~0xf00000u)|0xf00000u;
#if defined(I960_BACKGROUND) || defined(I960_BACKGROUND_NET)
 /* 33.333 MHz measured bus / 8 / 41667 ~= 100 Hz. Validate against host time. */
 REG(0xff000310)=41667;REG(0xff000314)=41667;
#else
 REG(0xff000310)=20000;REG(0xff000314)=20000;
#endif
#if defined(I960_BACKGROUND) || defined(I960_BACKGROUND_NET)
 REG(0xff008504)=saved_mask|0x2000;
#else
 REG(0xff008504)=0x2000;
#endif
 REG(0xff000318)=0x36;
 return 0;
}


/* STOP is handled directly at the masked host entry, never by resuming a
 * possibly failed RTEMS task context. The kernel validates this acknowledgement. */
static void timer_stop_response(unsigned char*b,unsigned int initialized){
 unsigned char*out=b+BIO_OUTPUT;unsigned int i;
 if(!timer_saved)saved_vector=REG(0x3c);
 stop_timer();for(i=0;i<64;i+=4)bio_put(out+i,0);
 bio_put(out,0x31415452u);bio_put(out+28,REG(0xff008504));bio_put(out+32,REG(0xff008528));
 bio_put(out+36,REG(0x3c));bio_put(out+40,saved_vector);
 bio_put(out+44,REG(0xff000310));bio_put(out+48,REG(0xff000314));bio_put(out+52,REG(0xff000318));
 bio_put(out+56,REG(0xff008500));bio_put(out+60,armed);
 bio_put(b+20,0);bio_put(b+24,64);bio_put(b+28,bio_word(b+8));
}
#endif

/* Bounded observational prerequisite for an autonomous BSP, not a takeover.
 * Deliberately never reads TMR0/1: reading clears terminal-count status. */
#include "buffer_io.h"
static const unsigned int registers[]={
 0xff000300,0xff000304,0xff000310,0xff000314,
 0xff008500,0xff008504,0xff008510,0xff008520,0xff008524,0xff008528,
 0xff008700,0xff008704,0xff008708,0xff008710,
 0xff008100,0xff008108,0xff00810c,0xff008110,0xff008114,
 0x1400,0x1404,0x1440,0x1444,0x1480,0x1484,0x1330,0x1334,0x1350
};
static unsigned int readable(unsigned int a,unsigned int n){
 if(a&3)return 0;
 return (a>=0xc0000000u&&a<=0xc1000000u-n)||(a>=0xfef80000u&&a<=0xff000000u-n)||(a<=0x1000u-n);
}
unsigned int payload(unsigned long address){
 unsigned char*b=(unsigned char*)address,*o=b+BIO_OUTPUT;unsigned int i,n=0,prcb,it,pc;
 if(!bio_request_valid(b)||bio_word(b+16)<1400||bio_word(b+12))return 1;
 __asm__ volatile("modpc 0,0,%0":"=r"(pc));
 bio_put(o,0x31494152);bio_put(o+4,pc);n=8;
 for(i=0;i<sizeof(registers)/sizeof(registers[0]);i++){bio_put(o+n,registers[i]);bio_put(o+n+4,*(volatile unsigned int*)registers[i]);n+=8;}
 prcb=*(volatile unsigned int*)0xff008700;
 if(!readable(prcb,40))return 2;
 bio_put(o+n,prcb);n+=4;
 for(i=0;i<10;i++){bio_put(o+n,((volatile unsigned int*)prcb)[i]);n+=4;}
 it=((volatile unsigned int*)prcb)[4];if(!readable(it,1028))return 3;
 bio_put(o+n,it);n+=4;
 for(i=0;i<257;i++){bio_put(o+n,((volatile unsigned int*)it)[i]);n+=4;}
 bio_put(b+20,0);bio_put(b+24,n);bio_put(b+28,bio_word(b+8));return 0;
}

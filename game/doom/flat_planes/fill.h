/* GPL-2.0-or-later. Bounded indexed-color span; caller owns the render buffer. */
#ifndef DOOM_FLAT_FILL_H
#define DOOM_FLAT_FILL_H
static void doom_flat_fill(unsigned char *p,unsigned n,unsigned char color){
 unsigned word=(unsigned)color*0x01010101u;
 while(n && ((unsigned long)p&3u)){*p++=color;--n;}
 while(n>=4){*(unsigned*)p=word;p+=4;n-=4;}
 while(n--)*p++=color;
}
#endif

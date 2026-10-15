#ifndef DOOM_SCREEN_COPY_H
#define DOOM_SCREEN_COPY_H
/* Fixed CMAP256 320x200 presentation, distinct owned buffers. Keep the
 * persistent Doom screen separate from delivery slots that DMA may pin.
 * No read/write extends beyond the 64,000 pixel bytes. */
typedef unsigned doom_screen_word __attribute__((__may_alias__));
typedef char doom_screen_word_is_four[sizeof(doom_screen_word)==4?1:-1];
static void doom_screen_copy(unsigned char *dst,const unsigned char *src){
 unsigned n=64000;
 if(!(((unsigned long)dst|(unsigned long)src)&3u)){
  doom_screen_word *d=(doom_screen_word*)dst;
  const doom_screen_word *s=(const doom_screen_word*)src;
  /* Four independent words amortize loop control without 16-byte alignment. */
  do{d[0]=s[0];d[1]=s[1];d[2]=s[2];d[3]=s[3];d+=4;s+=4;n-=16;}while(n);
 }else{
  do{*dst++=*src++;}while(--n);
 }
}
#endif

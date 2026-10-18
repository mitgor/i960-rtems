#ifndef DOOM_SCREEN_COPY_H
#define DOOM_SCREEN_COPY_H
/* Exact 320x200 indexed copy. The source is Doom's persistent screen and the
 * destination is a distinct owned delivery slot. Never cross the pixel edge. */
typedef unsigned long long doom_screen_pair __attribute__((__may_alias__));
typedef unsigned doom_screen_word __attribute__((__may_alias__));
typedef char doom_screen_pair_is_eight[sizeof(doom_screen_pair)==8?1:-1];
typedef char doom_screen_word_is_four[sizeof(doom_screen_word)==4?1:-1];
static void doom_screen_copy(unsigned char *dst,const unsigned char *src){
 unsigned n=64000;
 if(!(((unsigned long)dst|(unsigned long)src)&7u)){
  doom_screen_pair *d=(doom_screen_pair*)dst;
  const doom_screen_pair *s=(const doom_screen_pair*)src;
  do{d[0]=s[0];d[1]=s[1];d[2]=s[2];d[3]=s[3];d+=4;s+=4;n-=32;}while(n);
 }else if(!(((unsigned long)dst|(unsigned long)src)&3u)){
  doom_screen_word *d=(doom_screen_word*)dst;
  const doom_screen_word *s=(const doom_screen_word*)src;
  do{d[0]=s[0];d[1]=s[1];d[2]=s[2];d[3]=s[3];d+=4;s+=4;n-=16;}while(n);
 }else{
  do{*dst++=*src++;}while(--n);
 }
}
#endif

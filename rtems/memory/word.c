/* Ordinary RAM only: never use these helpers for MMIO or volatile DMA state.
 * GCC may_alias makes word accesses valid for arbitrary object representations.
 * Byte prefixes/tails prevent accesses outside [pointer, pointer + n).
 */
#include <stddef.h>
typedef unsigned int memory_word __attribute__((__may_alias__));
typedef char memory_word_must_be_32_bits[sizeof(memory_word)==4?1:-1];

void *memcpy(void *destination,const void *source,size_t n)
{
 unsigned char *d=destination;
 const unsigned char *s=source;
 /* Different mod-4 alignment cannot make both pointers word aligned. */
 if((((unsigned long)d^(unsigned long)s)&3)==0){
  while(n && ((unsigned long)d&3)){*d++=*s++;n--;}
  while(n>=4){*(memory_word*)d=*(const memory_word*)s;d+=4;s+=4;n-=4;}
 }
 while(n--)*d++=*s++;
 return destination;
}

void *memset(void *destination,int value,size_t n)
{
 unsigned char *d=destination;
 unsigned char byte=(unsigned char)value;
 memory_word word=(memory_word)byte*0x01010101u;
 while(n && ((unsigned long)d&3)){*d++=byte;n--;}
 while(n>=4){*(memory_word*)d=word;d+=4;n-=4;}
 while(n--)*d++=byte;
 return destination;
}

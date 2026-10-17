/* RAM-only copy: exact prefix/tail, equal-alignment wide accesses only. */
typedef unsigned dma_copy_word __attribute__((__may_alias__));
static void dma_copy(void *dst,const void *src,unsigned n){
 unsigned char*d=dst;const unsigned char*s=src;
 if(!(((unsigned long)d^(unsigned long)s)&3u)){
  while(n&&((unsigned long)d&3u)){*d++=*s++;n--;}
  while(n>=4u){*(dma_copy_word*)d=*(const dma_copy_word*)s;d+=4;s+=4;n-=4u;}
 }
 while(n--)*d++=*s++;
}

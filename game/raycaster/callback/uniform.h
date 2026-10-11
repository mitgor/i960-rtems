/* Ordinary request RAM only. Aligned alias-safe words, exact prefix/tail.
 * Never reads outside the supplied range; every byte contributes to equality. */
typedef unsigned int bio_scan_word __attribute__((__may_alias__));
typedef char bio_scan_word_32[sizeof(bio_scan_word)==4?1:-1];
static inline int bio_uniform(const unsigned char *p,unsigned int n,unsigned char value)
{
    unsigned int expected=(unsigned int)value*0x01010101u;
    while(n && ((unsigned long)p&3)){if(*p++!=value)return 0;n--;}
    while(n>=4){if(*(const bio_scan_word*)p!=expected)return 0;p+=4;n-=4;}
    while(n--){if(*p++!=value)return 0;}
    return 1;
}

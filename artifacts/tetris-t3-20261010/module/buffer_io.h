#ifndef I960_BUFFER_IO_H
#define I960_BUFFER_IO_H
/* Fixed little-endian wire format. Offsets are relative to the IO block. */
#define BIO_BASE 0xc0f34000u
#define BIO_OFFSET 0x8000u
#define BIO_MAGIC 0x314f4942u /* BIO1 */
#define BIO_VERSION 1u
#define BIO_HEADER 64u
#define BIO_INPUT 64u
#define BIO_INPUT_MAX 4096u
#define BIO_GUARD1 (BIO_INPUT+BIO_INPUT_MAX)
#define BIO_OUTPUT (BIO_GUARD1+16u)
#define BIO_OUTPUT_MAX 8192u
#define BIO_GUARD2 (BIO_OUTPUT+BIO_OUTPUT_MAX)
#define BIO_SIZE (BIO_GUARD2+16u)
#define BIO_IMAGE_SIZE (BIO_OFFSET+BIO_SIZE)
#define BIO_PENDING 0xffffffffu
/* header words: magic, version, sequence, input_length, output_capacity,
 * status, output_length, response_sequence, eight reserved zero words.
 * status: 0 success; 1 invalid request; 2 insufficient output capacity.
 * Only words 5..7 and output[0..output_length) may change. */
static inline unsigned int bio_word(const unsigned char *p)
{
    return (unsigned int)p[0] | (unsigned int)p[1]<<8 |
           (unsigned int)p[2]<<16 | (unsigned int)p[3]<<24;
}
static inline void bio_put(unsigned char *p,unsigned int n)
{ p[0]=n;p[1]=n>>8;p[2]=n>>16;p[3]=n>>24; }
static inline int bio_request_valid(const unsigned char *b)
{
    unsigned int i;
    if(bio_word(b)!=BIO_MAGIC || bio_word(b+4)!=BIO_VERSION ||
       !bio_word(b+8) || bio_word(b+12)>BIO_INPUT_MAX ||
       bio_word(b+16)>BIO_OUTPUT_MAX || bio_word(b+20)!=BIO_PENDING ||
       bio_word(b+24) || bio_word(b+28)) return 0;
    for(i=32;i<BIO_HEADER;i++) if(b[i]) return 0;
    for(i=BIO_INPUT+bio_word(b+12);i<BIO_GUARD1;i++) if(b[i]) return 0;
    for(i=0;i<16;i++) if(b[BIO_GUARD1+i]!=0xa5 || b[BIO_GUARD2+i]!=0x5a) return 0;
    for(i=0;i<BIO_OUTPUT_MAX;i++) if(b[BIO_OUTPUT+i]!=0xcc) return 0;
    return 1;
}
/* Verify the entire staging image, not just the declared output: all bytes
 * outside the explicit mutable fields must equal the pre-execution image. */
static inline int bio_response_valid(const unsigned char *before,const unsigned char *after,
                              unsigned int size)
{
    const unsigned char *b=after+BIO_OFFSET;
    unsigned int i,n,status;
    if(size<BIO_IMAGE_SIZE) return 0;
    n=bio_word(b+24);status=bio_word(b+20);
    if(n>bio_word(before+BIO_OFFSET+16) ||
       status==BIO_PENDING || (status && n) ||
       bio_word(b+28)!=bio_word(before+BIO_OFFSET+8)) return 0;
    for(i=0;i<size;i++) {
        if(i>=BIO_OFFSET+20 && i<BIO_OFFSET+32) continue;
        if(i>=BIO_OFFSET+BIO_OUTPUT && i<BIO_OFFSET+BIO_OUTPUT+n) continue;
        if(before[i]!=after[i]) return 0;
    }
    return 1;
}
#endif

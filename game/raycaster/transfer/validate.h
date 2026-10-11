/* Same RTEMS RIO1 mutation contract, expressed as whole immutable ranges.
 * Callers must first validate the request. Both complete reads are still compared.
 * This header is included with the kernel/native memcmp declaration available.
 */
static inline int bio_response_valid(const unsigned char *before,const unsigned char *after,
                              unsigned int size)
{
    const unsigned char *b;
    unsigned int n,status;
    if(size<BIO_IMAGE_SIZE) return 0;
    b=after+BIO_OFFSET;n=bio_word(b+24);status=bio_word(b+20);
    if(n>BIO_OUTPUT_MAX || n>bio_word(before+BIO_OFFSET+16) ||
       status==BIO_PENDING || (status && n) ||
       bio_word(b+28)!=bio_word(before+BIO_OFFSET+8)) return 0;
    /* Mutable: [0x20010,0x6fff0), response words [20,32), declared output.
     * Everything else, including both workspace guards and the allocation
     * suffix on periodic/full-close audits, must compare byte for byte. */
    if(memcmp(before,after,0x20010u)) return 0;
    if(memcmp(before+0x6fff0u,after+0x6fff0u,BIO_OFFSET+20u-0x6fff0u)) return 0;
    if(memcmp(before+BIO_OFFSET+32u,after+BIO_OFFSET+32u,BIO_OUTPUT-32u)) return 0;
    if(memcmp(before+BIO_OFFSET+BIO_OUTPUT+n,after+BIO_OFFSET+BIO_OUTPUT+n,
              size-(BIO_OFFSET+BIO_OUTPUT+n))) return 0;
    return 1;
}

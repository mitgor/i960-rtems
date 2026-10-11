/* Exact count of bytes different from pattern, after DMA completion/rmb.
 * memcpy loads one complete 8-byte word without alignment/aliasing assumptions.
 * Addition cannot carry between bytes: each low-seven-bit sum is at most 254.
 * A high bit therefore marks exactly each nonzero xor byte; horizontal byte
 * summation counts those bits (0..8). No byte outside [p,p+n) is accessed.
 */
static unsigned int changed(const u8 *p,size_t n,u8 pattern)
{
    const u64 ones=0x0101010101010101ULL,low=0x7f7f7f7f7f7f7f7fULL;
    const u64 high=0x8080808080808080ULL;
    u64 word,x,marks;unsigned int count=0;
    while(n>=8){
        memcpy(&word,p,8);x=word^(ones*pattern);
        marks=(((x&low)+low)|x)&high;
        count+=(unsigned int)(((marks>>7)*ones)>>56);
        p+=8;n-=8;
    }
    while(n--)if(*p++!=pattern)count++;
    return count;
}

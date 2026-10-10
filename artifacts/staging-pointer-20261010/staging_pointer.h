/* Fixed profile only; shared with the native guard test. No arbitrary addresses. */
#ifndef STAGING_POINTER_H
#define STAGING_POINTER_H
#define STAGING_BASE 0xc0f2c000u
#define POINTER_OFFSET 0xff1e6a70u
static unsigned int sp_word(const unsigned char *p)
{
    return (unsigned int)p[0] | (unsigned int)p[1]<<8 |
           (unsigned int)p[2]<<16 | (unsigned int)p[3]<<24;
}
static int sp_profile(const unsigned char *p)
{
    return p[4]==4 && p[5]==7 && p[6]==29 &&
        sp_word(p+0x18)==0x1000000u && sp_word(p+0x1c)==0xe72000u &&
        sp_word(p+0x20)==0x80000u && p[0x68]==16 && p[0x69]==0;
}
static int sp_allowed(unsigned int count, unsigned int offset, int armed)
{
    if (armed && count==4 && offset==POINTER_OFFSET) return 1;
    return count && count<=0xf000u && !(count&3) && !(offset&3) &&
        offset<=0x80000u-count;
}
#endif

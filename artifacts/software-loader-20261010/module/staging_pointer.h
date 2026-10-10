/* Fixed profile only; shared with the native guard test. No arbitrary addresses. */
#ifndef STAGING_POINTER_H
#define STAGING_POINTER_H
#define STAGING_BASE 0xc0f2c000u
#define POINTER_OFFSET 0xff1e6a70u
#define DRAM_HOOK_ADDRESS 0xc0120000u
#define DRAM_HOOK_SIZE 64u
#define DRAM_HOOK_OFFSET (DRAM_HOOK_ADDRESS - STAGING_BASE)
#define ROM_TABLE_ADDRESS 0xc001f9bcu
#define ROM_TABLE_OFFSET (ROM_TABLE_ADDRESS - STAGING_BASE)
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
static int sp_runtime_allowed(unsigned int count, unsigned int offset, int verified)
{
    if (!verified) return 0;
    return (count == 16 && offset == 0xc004a2e0u - STAGING_BASE) ||
        (count == 8 && offset == 0xc011e22cu - STAGING_BASE) ||
        (count == 512 && offset == 0xc0110780u - STAGING_BASE);
}
static int sp_dram_hook_allowed(unsigned int count, unsigned int offset, int verified,
                                int armed)
{
    return verified && armed && count == DRAM_HOOK_SIZE &&
           offset == DRAM_HOOK_OFFSET;
}
static int sp_rom_table_allowed(unsigned int count, unsigned int offset, int verified,
                                int armed)
{
    return verified && armed && count == 4 && offset == ROM_TABLE_OFFSET;
}
#endif

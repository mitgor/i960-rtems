/* Last extra block owned by the validated 65-block staging allocation. */
#ifndef RAM_SCRATCH_H
#define RAM_SCRATCH_H
#define SCRATCH_REGION_OFFSET 0x80000u
#define SCRATCH_WRITE_OFFSET 0x80010u
#define SCRATCH_REGION_SIZE 64u
#define SCRATCH_WRITE_SIZE 16u
static const unsigned char scratch_pattern[SCRATCH_WRITE_SIZE] = {
    0x49,0x39,0x36,0x30,0x52,0x41,0x4d,0x21,
    0x10,0x32,0x54,0x76,0x98,0xba,0xdc,0xfe
};
static int scratch_allowed(unsigned int opcode, unsigned int count,
                           unsigned int offset, int verified, int armed)
{
    if (!verified || !armed) return 0;
    return (opcode==0x20 && count==SCRATCH_REGION_SIZE && offset==SCRATCH_REGION_OFFSET) ||
           (opcode==0x21 && count==SCRATCH_WRITE_SIZE && offset==SCRATCH_WRITE_OFFSET);
}
static int scratch_matches(const unsigned char *before, const unsigned char *after,
                           const unsigned char *payload)
{
    unsigned int i;
    for (i=0;i<SCRATCH_REGION_SIZE;i++) {
        unsigned char expected=(i>=16 && i<32) ? payload[i-16] : before[i];
        if (after[i]!=expected) return 0;
    }
    return 1;
}
#endif

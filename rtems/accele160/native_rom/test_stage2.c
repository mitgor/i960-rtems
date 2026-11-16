/* Exercises the exact stage2_copy C implementation with guarded buffers. */
#define STAGE2_NATIVE_TEST 1
#include "stage2.c"
#include <assert.h>
#include <string.h>

static u32 fnv(const unsigned char *data, unsigned int size)
{
    u32 h = 2166136261u;
    unsigned int i;
    for (i = 0; i < size; ++i) h = (h ^ data[i]) * 16777619u;
    return h;
}

int main(void)
{
    u32 src[8] = {MAGIC, 8, 0, 0, 0x04030201u, 0x08070605u,
                  0xaaaaaaaa, 0xbbbbbbbbu};
    u32 dst[4] = {0xfeedfaceu, 0xaaaaaaaau, 0xbbbbbbbbu, 0xdec0de00u};
    u32 detail = 0, hash;
    hash = fnv((const unsigned char *)&src[4], 8);
    src[2] = hash;
    assert(stage2_copy(src, dst + 1, 8, &detail) == 0x2000u);
    assert(detail == hash && dst[0] == 0xfeedfaceu && dst[3] == 0xdec0de00u);
    assert(memcmp(dst + 1, src + 4, 8) == 0);
    src[0] ^= 1;
    assert(stage2_copy(src, dst + 1, 8, &detail) == 0x1001u);
    src[0] ^= 1;
    src[1] = 12;
    assert(stage2_copy(src, dst + 1, 8, &detail) == 0x1002u);
    src[1] = 8;
    src[3] = 1;
    assert(stage2_copy(src, dst + 1, 8, &detail) == 0x1002u);
    src[3] = 0;
    src[2] ^= 1;
    dst[1] = dst[2] = 0xa5a5a5a5u;
    assert(stage2_copy(src, dst + 1, 8, &detail) == 0x1003u);
    assert(detail == hash && dst[0] == 0xfeedfaceu && dst[3] == 0xdec0de00u);
    assert(dst[1] == 0xa5a5a5a5u && dst[2] == 0xa5a5a5a5u);
    return 0;
}

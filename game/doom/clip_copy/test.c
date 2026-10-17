#include <assert.h>
#include <string.h>
#include "copy.h"
int main(void)
{
    unsigned count, so, doff, i;
    for (count = 0; count <= 320; ++count)
    for (so = 0; so < 4; ++so)
    for (doff = 0; doff < 4; ++doff) {
        short source[328], target[328], expected[328];
        for (i = 0; i < 328; ++i) {
            source[i] = (short)(i * 307u + count);
            target[i] = expected[i] = (short)0x5aa5;
        }
        memcpy(expected + doff, source + so, count * sizeof(short));
        doom_clip_copy(target + doff, source + so, count);
        assert(memcmp(target, expected, sizeof(target)) == 0);
        for (i = 0; i < 328; ++i) assert(source[i] == (short)(i * 307u + count));
    }
    return 0;
}

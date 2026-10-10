#include <assert.h>
#include <string.h>
#include "ram_scratch.h"
int main(void)
{
    unsigned char before[64], after[64];
    unsigned int i;
    memset(before,0x73,sizeof(before)); memcpy(after,before,sizeof(after));
    assert(scratch_allowed(0x20,64,0x80000,1,1));
    assert(scratch_allowed(0x21,16,0x80010,1,1));
    assert(!scratch_allowed(0x21,16,0x80010,0,1));
    assert(!scratch_allowed(0x21,16,0x80010,1,0));
    assert(!scratch_allowed(0x21,16,0x80000,1,1));
    assert(!scratch_allowed(0x21,32,0x80010,1,1));
    assert(!scratch_allowed(0x22,16,0x80010,1,1));
    assert(!scratch_matches(before,after,scratch_pattern));
    memcpy(after+16,scratch_pattern,16);
    assert(scratch_matches(before,after,scratch_pattern));
    for(i=0;i<64;i++) { after[i]^=1; assert(!scratch_matches(before,after,scratch_pattern)); after[i]^=1; }
    memcpy(after+16,before+16,16);
    assert(scratch_matches(before,after,before+16));
    return 0;
}

/* Native tests of the actual post-init dispatcher, with mapped DRAM/MMIO. */
#include <assert.h>
#define POSTINIT_PROFILE
#define LOADER_TEST
static unsigned int ram[0x10000/4], regs[16];
#define MEMORY(a) ram[((a)-0xC0120000u)/4]
#define REG(a) regs[(a)/4]
#include "../loader.c"
int main(void)
{
    struct loader_state s = {0,0,0};
    assert(dispatch(&s,OP_SET_ADDR,0x200)==ST_BADADDR);
    assert(dispatch(&s,OP_GO,0x200)==ST_BADADDR);
    assert(dispatch(&s,OP_WRITE,1)==ST_BADSTATE);
    assert(dispatch(&s,OP_SET_ADDR,PAYLOAD_BASE)==ST_OK);
    assert(dispatch(&s,OP_WRITE,0x12345678)==ST_OK);
    assert(dispatch(&s,OP_READ,PAYLOAD_BASE)==ST_OK);
    assert(REG(R_OMR1)==0x12345678);
    assert(dispatch(&s,OP_SET_ADDR,PAYLOAD_END-4)==ST_OK);
    assert(dispatch(&s,OP_WRITE,0x87654321)==ST_OK);
    assert(dispatch(&s,OP_WRITE,0)==ST_BADADDR);
    assert(dispatch(&s,OP_SET_ADDR,PAYLOAD_END)==ST_BADADDR);
    assert(dispatch(&s,OP_WRITE,0)==ST_BADSTATE);
    assert(dispatch(&s,OP_GO,PAYLOAD_BASE)==ST_HANDOFF);
    assert(dispatch(&s,OP_GO,PAYLOAD_BASE+1)==ST_BADADDR);
    assert(dispatch(&s,OP_SET_REG_ADDR,0x1204)==ST_BADADDR);
    assert(dispatch(&s,OP_REG_READ,0x1204)==ST_BADADDR);
    return 0;
}

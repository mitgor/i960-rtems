/* Flash-resident i960 loader for the DAC960PG.
 *
 * Boots from flash (its firstIP is set by host/mkimage.py), then serves commands
 * from the host over the Messaging Unit (see mu.h): write words into memory and
 * jump to them. This replaces "reflash to iterate" with "flash once, push code".
 *
 * Deliberately self-contained: no static storage (no .bss/.data to init), no
 * libgcc calls (no mul/div), and one non-recursive function one call deep. On the
 * i960 a shallow call stays in the on-chip register cache and never spills to the
 * stack, so the loader runs correctly even before DRAM exists. The only memory it
 * touches is the MU registers and wherever the host points the load pointer.
 */
typedef unsigned int u32;
#include "mu.h"

#define REG(off) (*(volatile u32 *)(MU_LOCAL_BASE + (off)))

void loader_main(void)
{
    u32 last = 0;
    volatile u32 *dst = 0;

    REG(R_OMR0) = (last << 16) | ST_READY;      /* host sees READY at BAR0+0x18 */

    for (;;) {
        u32 seq, op, arg, st = ST_OK, cmd;
        do { cmd = REG(R_IMR1); } while ((cmd >> 16) == last);  /* wait: new seq */
        seq = cmd >> 16;
        op  = cmd & 0xffff;
        arg = REG(R_IMR0);                      /* IMR0 was committed before IMR1 */

        switch (op) {
        case OP_PING:     break;
        case OP_SET_ADDR: dst = (volatile u32 *)arg; break;
        case OP_WRITE:    *dst++ = arg; break;
        case OP_READ:     REG(R_OMR1) = *(volatile u32 *)arg; break;
        case OP_GO:
            last = seq;
            REG(R_OMR0) = (last << 16) | ST_OK; /* ack GO before handing off */
            ((void (*)(void))arg)();            /* payload owns the CPU */
            for (;;) ;                          /* if it returns, park */
        default:          st = ST_BADOP;
        }
        last = seq;
        REG(R_OMR0) = (last << 16) | st;        /* ack this seq */
    }
}

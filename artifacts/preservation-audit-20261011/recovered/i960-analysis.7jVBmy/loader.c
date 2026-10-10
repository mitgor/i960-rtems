/* Flash-resident i960 loader. No static storage or runtime initialization.
 * Startup/register-cache assumptions still require target disassembly and card
 * bring-up; see REVIEW.md. The local state must remain below payload RAM. */
typedef unsigned int u32;
#include "mu.h"

#ifndef REG
#define REG(off) (*(volatile u32 *)(MU_LOCAL_BASE + (off)))
#endif
#ifndef MEMORY
#define MEMORY(addr) (*(volatile u32 *)(addr))
#endif

struct loader_state {
    u32 last;
    u32 dst;
    u32 mode; /* 0 unset, 1 payload, 2 explicit register write */
};

/* Inline so target build need not add another register frame. Tests exercise
 * this exact dispatcher rather than a separate model of its behavior. */
static __inline__ u32 dispatch(struct loader_state *s, u32 op, u32 arg)
{
    switch (op) {
    case OP_PING: return ST_OK;
    case OP_SET_ADDR:
    case OP_SET_REG_ADDR:
        s->mode = 0; s->dst = 0;
        if (!(op == OP_SET_ADDR ? payload_word(arg) : register_word(arg))) return ST_BADADDR;
        s->dst = arg; s->mode = op == OP_SET_ADDR ? 1u : 2u;
        return ST_OK;
    case OP_WRITE:
        if (s->mode != 1) return ST_BADSTATE;
        if (!payload_word(s->dst)) return ST_BADADDR;
        MEMORY(s->dst) = arg; s->dst += 4u;
        return ST_OK;
    case OP_REG_WRITE:
        if (s->mode != 2) return ST_BADSTATE;
        MEMORY(s->dst) = arg;
        return ST_OK;
    case OP_READ:
    case OP_REG_READ:
        if (!(op == OP_READ ? payload_word(arg) : register_word(arg))) return ST_BADADDR;
        REG(R_OMR1) = MEMORY(arg);
        return ST_OK;
    case OP_GO:
        return payload_word(arg) ? ST_HANDOFF : ST_BADADDR;
    default: return ST_BADOP;
    }
}

#ifndef LOADER_TEST
void loader_main(void)
{
    struct loader_state s;
    s.last = REG(R_IMR1) >> 16; /* discard stale input across reset */
    s.dst = s.mode = 0;
    REG(R_OMR1) = 0;
    REG(R_OMR0) = (s.last << 16) | ST_READY;
    for (;;) {
        u32 cmd, arg, status;
        do { cmd = REG(R_IMR1); } while ((cmd >> 16) == s.last);
        arg = REG(R_IMR0);
        status = dispatch(&s, cmd & 0xffffu, arg);
        s.last = cmd >> 16;
        if (status == ST_HANDOFF) REG(R_OMR1) = 0;
        REG(R_OMR0) = (s.last << 16) | status;
        if (status == ST_HANDOFF) {
            ((void (*)(void))arg)(); /* payload must preserve OMR0 */
            for (;;) ; /* if it returns, park */
        }
    }
}
#endif

/* Included after stage_read_pair(), before run_stage(). */
#include "one_shot.h"

static unsigned int program_read(void *ctx, enum po_register reg)
{
    struct experiment *d = ctx;
    switch (reg) {
    case PO_IDB: return readl(d->bar + IDB);
    case PO_ODB: return readl(d->bar + ODB);
    case PO_STATUS_ID: return readw(d->bar + STATUS_ID);
    case PO_STATUS: return readw(d->bar + STATUS);
    default: return ~0u;
    }
}
static void program_write(void *ctx, enum po_register reg, unsigned int value)
{
    struct experiment *d = ctx;
    switch (reg) {
    case PO_MBOX0: writel(value, d->bar + MBOX); break;
    case PO_MBOX4: writel(value, d->bar + MBOX + 4); break;
    case PO_MBOX8: writel(value, d->bar + MBOX + 8); break;
    case PO_MBOX12: writeb(value, d->bar + MBOX + 12); break;
    case PO_IDB:
        if (value == 1) {
            d->pending = true;
            record(d, "PROGRAM SUBMITTED once: op=2b id=%u subcommand=1 bootblock=0; RAM rollback prohibited\n", d->tag);
        }
        writel(value, d->bar + IDB); break;
    case PO_ODB: writel(value, d->bar + ODB); break;
    default: break;
    }
}
static int program_wait(void *ctx, int completion)
{
    struct experiment *d = ctx;
    u32 value;
    if (!completion)
        return readl_poll_timeout(d->bar + IDB, value, !(value & 3), 50, 2000000);
    /* Runs in a workqueue, not module insertion. Never retry on timeout. */
    return readl_poll_timeout(d->bar + ODB, value, value & 1, 1000, 120000000);
}
static void program_fence(void *ctx)
{
    (void)ctx;
    dma_wmb();
}
static int program_submit(void *ctx, struct po_state *state)
{
    static const struct po_io io = { program_read, program_write, program_wait, program_fence };
    struct experiment *d = ctx;
    int rc;
    if (!program_enable || strcmp(program_token, PROGRAM_CANDIDATE_SHA)) return -EPERM;
    if (d->pending || d->exec_dirty || !d->runtime_verified || d->tag == 255)
        return -EPERM;
    ++d->tag;
    rc = po_submit(state, &io, d, d->tag);
    if (state->completed) d->pending = false;
    record(d, "program transport rc=%d submitted=%d completed=%d pending=%u\n",
           rc, state->submitted, state->completed, d->pending);
    return rc;
}
static int program_readback(void *ctx)
{
    struct experiment *d = ctx;
    int rc;
    /* Stock CF80 completion frees/zeros staging. The first normal 20 allocates
     * and rebuilds it from physical flash through stock bytewise CPU loads.
     * No upload or custom callback is permitted after the program doorbell. */
    d->stage_armed = false;
    rc = stage_read_pair(d, 4, stage_candidate_sha256, "fresh-flash");
    if (!rc && memcmp(d->stage[0].data + 0x7c000,
                      d->stage[4].data + 0x7c000, 0x4000)) rc = -ENODATA;
    if (!rc) {
        d->stage_dirty = false;
        record(d, "VERIFIED fresh bytewise flash snapshot: full candidate SHA256 and unchanged boot block\n");
    }
    return rc;
}
static int run_program_once(struct experiment *d)
{
    static const struct po_ops ops = { program_submit, program_readback };
    int rc = po_run(&d->program, d->runtime_verified && d->stage_dirty &&
                    !d->pending && !d->exec_dirty && !d->exec_armed,
                    program_enable, &ops, d);
    record(d, "program-state=%u rc=%d submitted=%d completed=%d verified=%d\n",
           d->program.phase, rc, d->program.submitted,
           d->program.completed, d->program.verified);
    return rc;
}

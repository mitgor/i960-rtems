/* SPDX-License-Identifier: GPL-2.0
 * Shared kernel/native one-shot state machine and exact mailbox transport.
 * No allocation, reset, retry or firmware rollback lives in this code.
 */
#ifndef DAC960_ONE_SHOT_H
#define DAC960_ONE_SHOT_H

enum po_phase {
    PO_NEW, PO_REFUSED, PO_DRY_RUN, PO_READY, PO_SUBMITTED,
    PO_UNCERTAIN, PO_PROGRAM_FAILED, PO_READBACK_FAILED, PO_VERIFIED
};
enum po_register { PO_IDB, PO_ODB, PO_STATUS_ID, PO_STATUS,
                   PO_MBOX0, PO_MBOX4, PO_MBOX8, PO_MBOX12 };
struct po_state {
    enum po_phase phase;
    int attempted, submitted, completed, verified, error;
};
struct po_io {
    unsigned int (*read)(void *, enum po_register);
    void (*write)(void *, enum po_register, unsigned int);
    /* idle: IDB bits 0/1 clear; completion: ODB bit 0 set. */
    int (*wait)(void *, int completion);
    void (*fence)(void *);
};
struct po_ops {
    int (*submit)(void *, struct po_state *);
    int (*readback)(void *);
};

/* ready must represent verified stock + candidate + CPU CRC + restored code
 * and table, with no outstanding command. Authorization is separate. */
static int po_run(struct po_state *s, int ready, int enable,
                  const struct po_ops *ops, void *ctx)
{
    int rc;
    if (s->attempted) return -EPERM;
    s->attempted = 1;
    if (!ready) { s->phase = PO_REFUSED; s->error = -EPERM; return s->error; }
    if (!enable) { s->phase = PO_DRY_RUN; return 0; }
    s->phase = PO_READY;
    rc = ops->submit(ctx, s);
    if (!s->submitted) {
        s->phase = PO_REFUSED;
        s->error = rc ? rc : -EPROTO;
        return s->error;
    }
    if (!s->completed) {
        s->phase = PO_UNCERTAIN;
        s->error = rc ? rc : -EPROTO;
        return s->error;
    }
    if (rc) { s->phase = PO_PROGRAM_FAILED; s->error = rc; return rc; }
    rc = ops->readback(ctx);
    if (rc) { s->phase = PO_READBACK_FAILED; s->error = rc; return rc; }
    s->verified = 1;
    s->phase = PO_VERIFIED;
    return 0;
}

static int po_submit(struct po_state *s, const struct po_io *io,
                     void *ctx, unsigned int tag)
{
    unsigned int id, status;
    int rc;
    if (s->phase != PO_READY || s->submitted || !tag || tag > 255)
        return -EPERM;
    if (io->read(ctx, PO_ODB) & 1) return -EBUSY;
    rc = io->wait(ctx, 0);
    if (rc) return rc; /* No doorbell: RAM restoration is still permissible. */
    /* Byte 2 = subcommand 1; byte 3 = 0 preserves the boot block.
     * No DMA address, component length or caller-defined mailbox bytes. */
    io->write(ctx, PO_MBOX0, 0x0001002bu | (tag << 8));
    io->write(ctx, PO_MBOX4, 0);
    io->write(ctx, PO_MBOX8, 0);
    io->write(ctx, PO_MBOX12, 0);
    io->fence(ctx);
    s->submitted = 1; /* Irreversible boundary, BEFORE the MMIO doorbell. */
    s->phase = PO_SUBMITTED;
    io->write(ctx, PO_IDB, 1);
    rc = io->wait(ctx, 1);
    if (rc) return rc;
    id = io->read(ctx, PO_STATUS_ID);
    status = io->read(ctx, PO_STATUS);
    if ((id & 0xff) != tag) return -EPROTO; /* Do not consume unknown completion. */
    io->write(ctx, PO_ODB, 1);
    io->write(ctx, PO_IDB, 2);
    (void)io->read(ctx, PO_IDB); /* Flush posted acknowledgements. */
    s->completed = 1;
    return status ? -EIO : 0;
}
#endif

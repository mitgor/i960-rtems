#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include "one_shot.h"

struct fake {
    struct po_state state;
    int stale, idle_error, completion_error, wrong_id, status_error, bad_readback;
    int writes, doorbells, acknowledgements, fences, readbacks;
    unsigned int mailbox[4];
};
static unsigned int rd(void *ctx, enum po_register reg)
{
    struct fake *f=ctx;
    switch(reg) {
    case PO_ODB: return f->stale;
    case PO_STATUS_ID: return f->wrong_id ? 99 : 42;
    case PO_STATUS: return f->status_error ? 2 : 0;
    case PO_IDB: return 0;
    default: assert(0); return 0;
    }
}
static void wr(void *ctx, enum po_register reg, unsigned int value)
{
    struct fake *f=ctx; f->writes++;
    if(reg>=PO_MBOX0) {
        assert(!f->state.submitted);
        f->mailbox[reg-PO_MBOX0]=value;
    } else if(reg==PO_IDB && value==1) {
        assert(f->state.submitted && f->state.phase==PO_SUBMITTED);
        assert(f->fences==1 && !f->doorbells);
        assert(f->mailbox[0]==0x00012a2b);
        assert(!f->mailbox[1] && !f->mailbox[2] && !f->mailbox[3]);
        f->doorbells++;
    } else {
        assert(f->doorbells==1 && !f->state.completed);
        assert((reg==PO_ODB && value==1) || (reg==PO_IDB && value==2));
        f->acknowledgements++;
    }
}
static int wait_io(void *ctx, int complete)
{
    struct fake *f=ctx;
    return (complete ? f->completion_error : f->idle_error) ? -ETIMEDOUT : 0;
}
static void fence(void *ctx) { ((struct fake *)ctx)->fences++; }
static const struct po_io io={rd,wr,wait_io,fence};
static int submit(void *ctx, struct po_state *s) { return po_submit(s,&io,ctx,42); }
static int readback(void *ctx)
{
    struct fake *f=ctx;
    assert(f->state.submitted && f->state.completed);
    assert(f->acknowledgements==2 && !f->status_error);
    f->readbacks++;
    return f->bad_readback ? -ENODATA : 0;
}
static const struct po_ops ops={submit,readback};

int main(void)
{
    int mask,rc;
    for(mask=0;mask<64;mask++) {
        struct fake f={0};
        int prior_writes;
        f.stale=mask&1; f.idle_error=mask&2; f.completion_error=mask&4;
        f.wrong_id=mask&8; f.status_error=mask&16; f.bad_readback=mask&32;
        rc=po_run(&f.state,1,1,&ops,&f);
        if(f.stale || f.idle_error) {
            assert(rc && f.state.phase==PO_REFUSED && !f.state.submitted && !f.writes);
        } else if(f.completion_error || f.wrong_id) {
            assert(rc && f.state.phase==PO_UNCERTAIN && !f.state.completed);
            assert(f.doorbells==1 && !f.acknowledgements && !f.readbacks);
        } else if(f.status_error) {
            assert(rc && f.state.phase==PO_PROGRAM_FAILED && f.state.completed && !f.readbacks);
        } else if(f.bad_readback) {
            assert(rc && f.state.phase==PO_READBACK_FAILED && f.readbacks==1);
        } else {
            assert(!rc && f.state.phase==PO_VERIFIED && f.state.verified && f.readbacks==1);
        }
        assert(f.doorbells<=1);
        prior_writes=f.writes;
        assert(po_run(&f.state,1,1,&ops,&f)==-EPERM && f.writes==prior_writes);
        assert(po_submit(&f.state,&io,&f,42)==-EPERM && f.writes==prior_writes);
    }
    {
        struct fake f={0};
        assert(!po_run(&f.state,1,0,&ops,&f));
        assert(f.state.phase==PO_DRY_RUN && !f.writes && !f.readbacks);
    }
    {
        struct fake f={0};
        assert(po_run(&f.state,0,1,&ops,&f)==-EPERM);
        assert(f.state.phase==PO_REFUSED && !f.writes);
    }
    {
        struct fake f={0};
        f.state.phase=PO_READY;
        assert(po_submit(&f.state,&io,&f,0)==-EPERM);
        assert(po_submit(&f.state,&io,&f,256)==-EPERM);
        assert(!f.writes);
    }
    puts("one-shot: 64 fault combinations, duplicate rejection, exact mailbox, dry-run and gates passed");
    return 0;
}

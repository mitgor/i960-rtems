# A one-shot, returning proof-of-execution callback for the DAC960PG.
#
# Entry contract: g0 is the firmware request object.  This is deliberately a
# tail-call shape: it supplies a distinctive completion code, then transfers to
# the stock completion routine, which restores interrupt state and rings the
# host mailbox.  It neither changes flash nor touches the Messaging Unit.
#
# This source is OFFLINE ONLY.  The stock host interface has no command which
# can install this callback in the live board table.  See
# ../../docs/loader/LIVE-EXECUTION-HANDOFF.md before considering any use.

    .text
    .globl _start
_start:
    lda 0x017e,g1
    stos g1,0x18(g0)       # request completion status = 0x017e
    lda stock_complete,g1
    bx (g1)                 # stock completion, tail transfer with g0 preserved

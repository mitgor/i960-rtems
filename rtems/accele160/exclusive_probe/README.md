# Bounded exclusive RTEMS callback, one upper page

This RAM-only image enters through current operation 13 on a stock-owned
512 KiB grant. Its entry changes to an owned stack and interrupt priority 31;
the stock command path cannot run on the same CPU until the callback returns.
Before any data write, the image checks the non-clearing CCR, NDAR and BCR
registers of all three 80303 DMA channels are zero. It verifies the selected
upper page `c0f01000` is all zero, hashes its 4 KiB, writes four unique words
at `+0x80`, reads them back, restores all four words, rehashes the entire page
and checks all three DMA channels again. It then runs the existing bounded
RTEMS STOP/no-host worker and restores firmware context.

The [physical run](../../../artifacts/current/accele160-exclusive-probe-20261017/README.md)
passed STOP and 2-million-poll timeout. Both upper-page snapshots match,
loader/owner/stage restoration passed, four full guarded firmware reads
matched, and the old card remained unbound. `host/accele160/exclusive_probe`
contains the exact host runner and independent replay.

This is a **temporary exclusive callback**, not a persistent takeover. Only
four words on one zero page were touched. It does not establish that the
whole upper bank is distinct DRAM or that stock firmware cannot reuse cache
after the callback returns. A Doom session needs a retained exclusive CPU,
interrupt and DMA handoff plus an 8 MiB arena proof.

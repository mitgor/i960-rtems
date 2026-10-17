# Borrowing stock-occupied RAM inside a bounded exclusive callback

This RAM-only operation-13 image extends the [upper-page test](../exclusive_probe/README.md).
At interrupt priority 31 on its owned entry stack, with the stock command
path suspended, it first checks all three DMA channels idle. It changes and
restores four words on zero upper page `c0f01000`, then does the same on the
known nonzero stock-runtime page `c0011000`. Each full 4 KiB page is hashed
by the card before and after its write; the host independently compares full
BAR snapshots before and after each STOP/timeout run. The card restores every
word even on a failed readback and checks DMA idle again before RTEMS starts.

The [two physical runs](../../../artifacts/current/accele160-occupied-probe-20261017/README.md)
passed with exact full-page restoration, firmware/RTEMS context, loader,
staging, allocator and four full-flash audits. This establishes that selected
stock-occupied bytes can be *temporarily* borrowed while stock execution is
paused. It does not establish persistent ownership after the callback returns,
or safe reuse of all firmware code, data and RAID cache pages.

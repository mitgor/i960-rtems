# Timer-driven exclusive RAM borrowing on AcceleRAID 160

This RAM-only operation-13 image extends the accepted [bounded RTEMS
preemption profile](../preempt/README.md). Before RTEMS starts, on the owned
entry stack at interrupt priority 31, it verifies CCR, NDAR and BCR idle on
all three Intel 80303 DMA channels. It saves four words at `c0f01080` and
`c0011080`, then writes distinct patterns. The first page is a zero upper-bank
page; the second is in stock's nonzero expanded runtime. A host PCI read
observes both complete 4 KiB pages while the two CPU-bound RTEMS workers are
being preempted by owned timer 1. The patterns persist across more ticks.

Exact STOP or the 120-tick no-host deadline stops the workers, drains both
retained ISR continuations, and restores stock timer/vector/mask, both pages,
firmware stack and allocator ownership. Card-side full-page FNV and all three
DMA channel guards run again before return. The host compares full pages,
loader, stage, owner and interrupt-stack captures, plus two full guarded flash
reads before and after. The [physical capture](../../../artifacts/current/accele160-exclusive-timer-20261017/README.md)
passes both paths; [replay](verify_live.py) rejects four independent tamper
cases. No firmware write was needed.

Build from the pinned RTEMS core and i960 toolchain with
`build.sh RTEMS_BUILD_DIR TOOLCHAIN_BIN OUT_DIR`. The [host runner](run_exclusive.py)
pins the exact accepted binary hashes and refuses a bound old card, active
stock descriptor, block device or missing same-boot flash preflight. On any
uncertain command result it retains the grant and one-shot module for guarded
recovery. Do not force-unload a pending command.

This proves **finite** CPU/timer/interrupt exclusivity while selected
stock-occupied bytes are borrowed and later restored. Stock firmware resumes
at callback return. It is not a retained reboot-only takeover, an 8 MiB
alias/extent proof, or Doom admission. Follow the [exclusive-mode contract](../EXCLUSIVE-MODE.md).

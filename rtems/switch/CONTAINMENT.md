# Containing workers that ignore STOP

2026-10-11: the separate `contain` profile passed three fresh card sessions.
Both workers ignored STOP and kept executing for four more timer ticks. The
controller suspended them externally, restored the timer, and returned through
the existing firmware callback. All three sessions then restored full borrowed
RAM/MU state and unloaded. No reboot or flash programming occurred. Production
IPv6 HTTP returned 200 after restart. [Evidence](../../artifacts/irq-containment-20261011/README.md).

## The containment contract

This is disposal of a whole, one-shot RTEMS instance. It does not kill one task
and continue a resident operating system. Both suspended worker stacks and both
owned ISR areas stay allocated until the callback has returned. Neither worker
is resumed, deleted, unwound, nor reported as drained. `initialized` prevents a
second invocation; the pinned driver also permits only one submitted step.

The workers execute the existing deep-call-chain assembly probe at CPU interrupt
priority 20. In this build its loop does not load or branch on `switch_stop` and
never yields or invokes an RTEMS service. It stores its decreasing iteration
budget in its own probe record. The one-million-iteration emergency ceiling is
retained as a finite test bound; all successful runs contain both workers long
before that ceiling. This demonstrates ignoring STOP, not an indefinitely
running or hostile program.

Timer F2 continues to time-slice the workers and observe the host's independent
MU STOP. The controller runs at RTEMS priority 1, CPU priority 31. On its STOP
event it samples both budgets, sleeps four ticks, and confirms both workers
have advanced despite STOP. It then calls `rtems_task_suspend()` on each worker.
The pinned RTEMS 4.6.6 implementation removes a ready task from the ready chain
and priority bitmap; it does not unwind its context or free its stack. The exact
`tasksuspend.c`, `threadsuspend.c` and state constants are saved in the archive.

After suspension the controller stops/restores the borrowed timer and checks
both workers are exactly `STATES_SUSPENDED` with suspend count 1. It lowers its
own RTEMS priority below the workers. Neither worker becomes the heir or runs.
Across 10,000 bounded checks, progress counters remain unchanged, ISR/dispatch
nesting stays zero, the controller remains executing/heir, and both original
interrupt frames still match the lifetime records. Whole worker-stack and owned
ISR-area checksums match before/after; guards and saved global sentinels pass.
These checks establish the tested quiescent state. Checksums are diagnostics,
not protection against malicious tasks forging evidence.

The timer source is stopped, its pending bit cleared, and the stock vector,
mapping and mask restored before acknowledgement. With workers no longer
runnable, the controller sends **QUIESCED (`0x75000000 | epoch`)**. This differs
from cooperative DRAINED (`0x73000000 | epoch`). RELEASE and the final callback
completion follow. The original interrupt frames are never synthesized or
edited to force an application return. The complete RTEMS workspace remains
intact through the BSP context switch back to firmware, then the host restores
the borrowed memory as a whole.

## Measured results

| Host STOP delay | STOP tick | Quiesced tick | A entries / returns | B entries / returns | Callback duration |
| --- | --- | --- | --- | --- | --- |
| 120 ms | 36 | 40 | 20 / 19 | 20 / 19 | 405.17 ms |
| 150 ms | 41 | 45 | 23 / 22 | 22 / 21 | 429.65 ms |
| 200 ms | 52 | 56 | 28 / 27 | 28 / 27 | 482.26 ms |

Each worker retains exactly one live ISR continuation: entries = returns + 1,
`live=1`, assembly active flag 1, and worker `done=0`. Those values are expected;
clearing them would conceal the retained contexts. Both tasks have state 2,
`STATES_SUSPENDED`. Budgets fell by 44,466–44,848 iterations during the four-tick
STOP-ignoring interval and then stayed unchanged. Remaining budgets at suspension
range from 372,480 to 552,401, so no successful worker hit its fallback ceiling.
All reports have zero fault bits and 10,000 stable observations.

The paired full 512 KiB staging restoration, execution RAM, table/flash
comparisons and MU words/masks/pending-bit checks passed. Each module unloaded
normally before the next fresh session. Boot ID remained
`ddc29cfe-f10a-4d49-b68b-9ad8f14c256f` throughout.

## Host cleanup gate and failure behavior

`build_contain_transport.py` derives the concurrent STOP driver, pins the exact
prepared image, and expects QUIESCED rather than DRAINED. After callback
completion and paired response reads, `contain_report.h` checks the complete
944-byte report before setting `stop_clean`. It requires zero faults, restored
timer registers, the matching epoch, two live retained contexts, suspended
states, continued progress after STOP, stopped progress after suspension,
unchanged checksums and a successful RELEASE/MU restoration report.

A bad report does not authorize restoration: `stop_started && !stop_clean`
continues to reject session close. The existing pending/dirty resource-retention
policy remains in force. Native ASan/UBSan tests exercise the exact C gate and
Python decoder against 91 damaged synthetic reports; offline tests additionally
reject 60 damaged copies of actual hardware reports. Failure injection into
this new target on hardware has not been performed. The earlier
[failed-control teardown](FAILED-TEARDOWN.md) results establish the inherited
retention mechanism, not every possible containment failure.

## Report layout

The original 736-byte report remains at offset 0, with retained-context semantics
for `done`, active and lifetime fields. The 80-byte STOP diagnostics at offset
736 record QUIESCED time in the former drained-tick slot. The 32 new words at
offset 816 are:

| Words | Meaning |
| --- | --- |
| 0–4 | CTN1 magic, controller pointer, STOP wake tick, containment tick, four-tick interval |
| 5–10 | A/B remaining budgets at STOP, at suspension, after stable checks |
| 11–14 | A/B scheduler states before/after checks |
| 15–17 | executing pointer, heir pointer, stable-observation count |
| 18–21 | A/B task-stack checksums before/after |
| 22–25 | A/B ISR-area checksums before/after |
| 26–31 | quiescence marker, stop flag, ISR depth, dispatch depth, armed flag, reserved zero |

Saved register *return* records are not claimed to be complete: the workers
never reach their assembly return path. The target checks live saved globals
and original interrupt-frame controls; prior profiles cover full roundtrips.

## Reproduce

Stop production and verify its complete close before taking exclusive ownership.
Use a fresh generated-module and live-output directory.

```sh
python3 project/rtems/build.py --work . --profile contain
python3 project/rtems/switch/build_contain_transport.py \
  --payload contain/kernel.bin --out contain-module
make -C /lib/modules/$(uname -r)/build M=$PWD/contain-module modules
sudo python3 project/rtems/switch/live_contain.py --payload contain/kernel.bin \
  --module contain-module/dac960rtems.ko --reader control-prototype/read_mu \
  --output contain-live1
```

Repository-side validation:

```sh
make -C rtems test
python3 rtems/switch/verify_contain_capture.py artifacts/irq-containment-20261011/live.tar.xz
```

The archive verifier checks the actual disassembled loop contains the progress
store and no STOP load, exact image/module hashes, raw paired responses and
immutable guards, original control records, the C cleanup gate, full close
captures and ordinary unload for all three sessions.

## Limits and next gate

This requires timer delivery, finite dispatch-disabled sections, an intact
scheduler, and workers that do not reprogram hardware or corrupt kernel memory.
There is no protection boundary between these i960 tasks. Permanently masked
interrupts, unbounded critical sections, stopped CPUs, shared-lock ownership,
external DMA engines and malicious code are not contained by task suspension.
The finite ceiling and 128-tick controller deadline are test bounds, not a
recovery guarantee for those cases. Physical recovery remains untested.

Next: combine this suspension path with the already bounded nested-critical-
section cases, then inject missed control/invalid containment acknowledgements
and verify retention. General task cancellation with resource/lock cleanup and
resident ownership remain separate design work. Do not enable preemption in
production autonet or start DMA networking based on these three bounded runs.

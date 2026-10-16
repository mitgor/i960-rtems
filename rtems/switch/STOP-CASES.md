# STOP in nested critical sections and bounded omission paths

2026-10-11: twelve hardware runs passed: three fresh sessions for each of four
cases. The separate `stopcases` profile adds `I960_STOP_CASES` to the existing
STOP1 test. Production HTTP and the earlier `mustop` profile are unchanged.

## Results

| Case | Host action | Observed target result (three runs each) |
| --- | --- | --- |
| 1 | STOP during dispatch depth 2 | READY tick 17, STOP tick 18; controller and drain delayed until tick 40 |
| 2 | STOP during dispatch depth 1 | READY tick 29, STOP tick 30; controller and drain delayed until tick 40 |
| 3 | Deliberately omit STOP | Controller event timeout at tick 128; workers and ISR continuations drain |
| 4 | Send STOP, deliberately omit RELEASE | Workers drain; 1,000,000-iteration RELEASE budget expires; callback returns with expected `0x4000` flag |

In cases 1/2, task A first runs with timer preemption until tick 16, giving both
workers live ISR continuations. It disables dispatch twice, holds depth 2 for
12 timer ticks, enables once, holds depth 1 for 12 more, then enables the outer
level. The host sends STOP as soon as READY identifies the selected depth.
The ISR records STOP and posts the controller event, but does not dispatch while
the critical section remains active. All 24 critical-section IRQ observations
retain the same owner, the correct dispatch depth and a pending switch. Task B's
entry count stays at 8 throughout. The controller wakes only at outer enable,
with dispatch depth 0; both workers then finish. A has 32 entries/returns and B
8. Both contexts were live when STOP arrived, including B's suspended ISR.

Task A runs its assembly sentinel/deep-stack probe after leaving the critical
section; task B remains in its sentinel loop while A holds dispatch disabled.
The critical-section evidence itself comes from owner, depth, pending-switch
and ISR lifetime observations.

The observed ISR dispatch depths are 3 and 2: the task's critical depth plus
one for ISR accounting. They are not additional task critical levels. The
inner enable does not let the ready controller run. All register sentinels,
PC/TC roundtrips, AC checks, deep-stack checks and task/ISR guards pass.

Case 3 keeps timer preemption running without any host STOP write. The event
receive returns `RTEMS_TIMEOUT` (6) at 128 delivered ticks. Both workers finish
with 64 entries/returns each and nonzero assembly-loop budgets. No STOP token
was recorded and the global fault word remains zero. Host still acknowledges
DRAINED with RELEASE; this is a missing-STOP test, not total host disappearance.

Case 4 omits RELEASE after receiving DRAINED. The timer is already restored,
so the deadline is a finite instruction-loop budget, not an interrupt clock.
The target records budget zero and the existing `0x4000` release-timeout flag,
restores its MU words/local status, and returns. The paired response, drained
state, restored timer, expected flag and mode are checked before host OISR
acknowledgement and cleanup. No other fault bit is allowed. Host remains present
to wait for and validate callback completion; this is not a host-process crash.

All twelve runs restored paired 512 KiB staging data, execution RAM, dispatch
words, timer state and MU words/masks/pending bits; the modules unloaded. No reboot
or flash writes occurred. The original IPv6 Vader service was restarted after
successful cleanup. [Exact evidence](../../artifacts/notes/irq-stop-cases-20261011.md).

## Implementation and bounds

The 12-byte request retains magic and nonce, with the third word selecting case
1–4. The separately pinned host module rejects other modes. `stop_critical.h`
holds/observes nested dispatch state; `stop_target.h` retains the prior STOP1
protocol. The host hook stays under the same session mutex. Only deliberate
mode-3/4 omissions change its behavior; an unexpected protocol timeout still
retains pending resources. The driver requires the mode-specific status and
complete timer/drain evidence before setting its cleanup-complete flag.

The 896-byte response contains the original 736-byte switch report, 80 bytes
of STOP diagnostics, then 20 critical-section words:

| Word | Meaning |
| --- | --- |
| 0 | case |
| 1–4 | critical start, inner enable, outer enable, outer enable return ticks |
| 5–8 | depths before/after inner and outer enable |
| 9–10 | B entries at critical start and before outer release |
| 11–12 | controller wake tick and dispatch depth |
| 13–14 | IRQ observations at depth 2 and depth 1 |
| 15–16 | owner/depth/nesting violations and pending-switch observations |
| 17 | critical phase at STOP |
| 18–19 | reserved zero |

`live_cases.py` checks every case-specific invariant and MU snapshots. The
archive verifier also checks exact payload/prepared-image/module hashes, all
cleanup captures and 102 deliberately corrupted reports. Native ASan/UBSan
coverage exercises the exact host loops and generated expected-outcome gates.
The prior STOP and deferral archives still pass their original verifiers.

The tick rate uses reload 20000. The 128-tick deadline depends on timer delivery;
it cannot recover code that permanently masks interrupts. Instruction-loop
bounds are finite on a progressing CPU, not calibrated wall-clock guarantees.
The experiments do not exercise unrecoverable hardware or a stopped CPU.

## Reproduce

Stop production and verify its complete close capture before running:

```sh
python3 project/rtems/build.py --work . --profile stopcases
python3 project/rtems/switch/build_cases_transport.py --payload stopcases/kernel.bin --out stopcases-module
make -C /lib/modules/$(uname -r)/build M=$PWD/stopcases-module modules
sudo python3 project/rtems/switch/live_cases.py --payload stopcases/kernel.bin \
  --module stopcases-module/dac960rtems.ko --reader control-prototype/read_mu \
  --output stopcases-live1
```

From the repository root, offline:

```sh
make -C rtems test
python3 rtems/switch/verify_cases_capture.py artifacts/irq-stop-cases-20261011/live.tar.xz
```

## Remaining work

The workers still check a stop flag. A new concurrent user-control API must
protect close/removal and outstanding-command lifetime before becoming a usable
monitor. Safe containment of code that ignores STOP or masks interrupts remains
unproven. CTL1 framing/retries, resident ownership, disk I/O, and network DMA are
not established by these tests. A full host-disappearance test is also distinct
from deliberately omitting individual protocol messages.

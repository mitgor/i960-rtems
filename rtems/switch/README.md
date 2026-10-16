# Two owned interrupt continuations and timer-driven task switching

**2026-10-11 batch follow-up:** [critical-section and failure containment](CONTAINMENT-BATCH.md)
now pass on the card. Six final critical sessions defer control until outer
release; three failure cases retain resources, including an invalid report after
completion. Earlier next-step statements below are historical. Resident resource
ownership and cancellation remain separate design gates.

**2026-10-11 follow-up:** [STOP-ignoring worker containment](CONTAINMENT.md) passed
three card sessions: external suspension, retained live ISR stacks, restored
timer and full cleanup after callback return. This is one-shot instance disposal,
not permanent-interrupt-mask recovery or resident resource-safe cancellation.
Earlier next-step statements below describe their historical checkpoints.

**2026-10-11 follow-up:** [failed-control teardown tests](FAILED-TEARDOWN.md) now pass
on the card for omitted STOP/final close and omitted RELEASE/unbind. Pending
resources remain pinned; unload is refused and recovery requires reboot. This
covers synthetic control failure, not physical disappearance or non-cooperative
task containment. Earlier next-step statements below are historical.

**Follow-up:** final user-descriptor close and orderly driver-unbind fault tests
now pass on the card, three runs each. See [lifecycle tests](LIFECYCLE.md) for
ordering evidence, the diagnostic fix and remaining failure-path limits.

**Follow-up:** nested critical-section STOP and both individual omission deadlines
now pass on hardware (three runs each). See [STOP cases](STOP-CASES.md) for the
new profile, expected timeout flag and exact limits. Earlier next-step statements
below describe the original STOP1 milestone.

2026-10-11: the `switch` profile passed three bounded hardware runs. Two equal
priority RTEMS tasks execute CPU-bound assembly loops without voluntarily yielding.
Timer interrupts time-slice them; each task owns its suspended ISR continuation.
[Exact evidence](../../artifacts/notes/irq-switch-20261011.md).

## Composite asynchronous context

The asynchronous context consists of several objects, all kept live together:

- The task's dedicated 8 KiB stack and original hardware interrupt frame, including
  saved PC/AC, vector and return linkage. No synthetic frame is constructed.
- A separate 8 KiB ISR area for that task: 64-byte lower guard, global-register/TC
  save area and padding up to offset 192, upward-growing C stack, 64-byte upper guard.
- The existing RTEMS `Thread_Control.Registers`, which saves the call-boundary
  continuation *inside that task's suspended ISR*. This 44-byte context does not
  become a standalone asynchronous register dump.
- A lifetime record: owner thread pointer, task-stack bounds, hardware frame
  address, saved PC/AC/vector, live flag, entry count and return count.

The assembly chooses a slot from `_Thread_Executing` before modifying global
registers. Unknown owners or reentry set a fault without overwriting a live
save area. It saves g0–g15 and TC, changes SP to the selected owned C stack,
then calls the IRQ body. That body enters/exits RTEMS ISR/dispatch accounting,
advances the clock, and dispatches at outermost exit. `_Thread_Dispatch()` can
remain suspended while the other task runs. On resume, the wrapper checks the
same owner, hardware frame and controls, restores TC/globals/SP and returns
through that task's original hardware frame.

Two live ISR continuations are not ordinary nested C calls on one shared stack.
`_ISR_Nest_level` is zero before the scheduler transfers execution. Each task
has its own saved continuation and does not reuse the other task's C stack.
This is why the earlier single-global save area cannot be used here.

## Bounded lifetime and stop

A controller task starts both workers and sleeps for 32 ticks. Each worker
registers its ownership at priority 31, then a finite assembly loop runs at
priority 20. Timer F2 can preempt that loop. Each loop carries distinct g0–g14
sentinels, local sentinels, PC/TC snapshots, an AC-dependent branch check and a
one-million-iteration ceiling. Seventeen call levels with checked volatile local
buffers exercise register-window spilling before the leaf loop.

At tick 32, the controller wakes at priority 31, publishes a stop flag and lowers
its RTEMS scheduling priority. Both workers resume their suspended ISRs, return
to their loops, observe STOP, restore CPU priority 31, check their records and
suspend themselves. Only then does the controller stop/restore the timer.
Normal success requires both lifetime records and assembly active flags drained,
matching entry/return counts, zero ISR/dispatch nesting, intact task/ISR guards,
and preserved registers. It then returns to the host for full RAM restoration.

The inherited fatal path stops the timer before escaping a failed callback;
that emergency path was not fault-injected on hardware here. Native tests cover
ownership-policy rejection; the live results establish the normal drained path.
An uncertain host transaction continues to use the existing transport retention
rules. This is an explicitly invoked experiment on an exclusively owned card.

## Evidence and limits

Every live run recorded 32 ticks, 32 IRQ-path scheduler handoffs and 31 observations
of both lifetime records being live. The handoff count includes the final wakeup
of the controller, not just worker-to-worker switches. Each worker entered and
returned 16 times. The two records had distinct owner pointers, non-overlapping
task stacks and distinct hardware-frame addresses/ISR areas. Both loop counters
advanced by about 228,000 iterations before STOP. All sentinels matched; both
PC values remained 00142002 and both TC values remained zero. No guard/frame
fault was reported. All three runs restored borrowed RAM and unloaded the module.

This proves timer-driven preemption/time-slicing of two CPU-bound tasks **inside
a bounded firmware callback**. It is not yet a resident RTEMS monitor. The host
still waits for the callback; the existing MU ioctl is not integrated into this
profile, so external independent STOP during these loops is not established.
Scheduler critical-section deferral is coded using the existing dispatch level,
but a live deferred-dispatch stress case remains to be added. General NMI/trace
faults, arbitrary nesting, more than two ISR owners and worst-case stack use
remain untested. Sampled entry/exit SP is not a full stack high-water measurement.
Production `autonet` and its priority policy remain unchanged.

## Build and run

In the established remote workspace, stop the web relay normally and verify its
restoration before taking exclusive ownership. Use a fresh output directory.

```sh
python3 project/rtems/build.py --work . --profile switch
python3 project/rtems/transport/build.py --out switch-module
make -C /lib/modules/$(uname -r)/build M="$PWD/switch-module" modules
sudo python3 project/rtems/switch/live_test.py --payload switch/kernel.bin \
  --module switch-module/dac960rtems.ko --output switch-live
```

This bounded profile uses ordinary `dac960rtems`, not `dac960auto`. Each upload
accepts one run; the harness creates a fresh session/module per repeat. Its
736-byte response includes timer state, counters, both lifetime records and
complete before/after probe records. `lifetime.h` is shared with ASan/UBSan
native tests (`python3 rtems/switch/test_lifetime.py`, also in `make -C rtems test`).

Next: validate deferred dispatch through critical sections, then integrate a
bounded MU STOP request into the CPU-bound switch profile with an explicit drain
handshake. Do not enable resident network tasks or general preemption merely
by lowering their interrupt priority.

## Nested dispatch deferral (`defer` profile)

`build.py --profile defer` compiles this same source with `I960_DEFER_TEST`.
The default `switch` profile and its 736-byte response are unchanged. `defer`
appends 20 little-endian words (816 bytes total), documented beside `deferral`
in `app.c` and named by `decode_defer()` in `live_test.py`.

Before its existing register/deep-stack probe, task A disables dispatch twice
using the actual RTEMS internal API. It lowers CPU priority to 20 and waits
for four timer interrupts, raises it to 31, enables dispatch once, then repeats
the four-tick wait at dispatch depth 1. Each wait has a finite loop budget.
The IRQ still advances RTEMS time and samples pending-switch/heir state after
unwinding ISR accounting. It checks that the executing owner and dispatch depth
stay correct, with ISR nesting zero at that sampling point. B has not started.

The outer `_Thread_Enable_dispatch()` dispatches to B; A's enable call returns
at tick 9 after B's first timer interrupt. A then joins the original CPU-bound
register-sentinel probe. The controller wakes at tick 32 and drains both tasks.
The maximum sampled ISR dispatch depth is 3 (outer critical depth 2 plus IRQ
accounting); this is not a measurement of every internal clock routine depth.

Three fresh upload/module cycles passed: four ticks at each critical level,
eight pending-switch/different-heir observations, B entries 0 before outer
release and 1 on A's return, levels 2/1/0, zero faults. Each had 24 IRQ-path
handoffs, 23 observations of two live continuations, A entries/returns 20/20,
B 12/12. The outer enable's direct dispatch is not part of the IRQ-handoff
counter. The last IRQ-path handoff wakes the controller. Timer reload 20000
is a bounded tick test, not a calibrated wall-clock claim.

Run only with the HTTP service stopped and its cleanup verified:

```sh
python3 project/rtems/build.py --work . --profile defer
python3 project/rtems/transport/build.py --out defer-module
make -C /lib/modules/$(uname -r)/build M=$PWD/defer-module modules
sudo python3 project/rtems/switch/live_test.py --defer \
  --payload defer/kernel.bin --module defer-module/dac960rtems.ko \
  --output defer-live1
```

Offline verification from the repository root:

```sh
python3 rtems/switch/verify_capture.py --defer artifacts/irq-deferral-20261011/live.tar.xz
```

This checks exact uploaded/module hashes, raw reports, sentinels and full close
restoration, and rejects 45 deliberately corrupted deferral reports. The next
experiment adds MU STOP during active CPU-bound execution. No independent host
STOP was attempted in this profile. [Evidence](../../artifacts/notes/irq-deferral-20261011.md).

## Host STOP while the callback is pending

The separate `mustop` profile now combines two owned task continuations with a
one-shot MU STOP/DRAINED/RELEASE handshake. Three live runs passed with both
continuations live at STOP. See [protocol, implementation and limits](STOP.md)
and [preserved evidence](../../artifacts/notes/irq-mu-stop-20261011.md).
The `switch` and `defer` profiles retain their previous contracts.

## Concurrent host control

The pending-callback STOP handshake can now be invoked through an ioctl from a
second host thread. Three live sessions passed duplicate/stale/late rejection,
context draining and complete cleanup. See [API and lock contract](CONCURRENT.md).

# Interrupt-context audit — P0

2026-10-11. Scope: actual `irq`, `auto`, `autonet` sources and build rewrites,
plus Intel i960 Rx manual chapters 7–9 and 17. This audit does not change the
working ISR or claim that asynchronous task preemption has been implemented.

## Current path

`timer_isr.S` is a hardware interrupt procedure. It saves g0–g15 to a 64-byte
area starting at the ISR entry SP, advances SP, clears g14 for the C ABI, calls
`timer_interrupt`, reloads the globals and returns through the hardware interrupt
frame. The save pointer is local r4 in the ISR's own register frame, not a shared
global pointer. The processor's new register frame isolates these ISR locals
from the interrupted procedure's locals. Normal return unwinds that frame.

In `autonet`, `timer_interrupt` sets `timer_in_irq` and `timer_request`, then
switches from `_Thread_BSP_context` to the saved RTEMS task. Init advances the
clock/network and calls `yield_host`, returning to the suspended ISR, which then
returns to stock firmware. This permits bounded background work. It does not
permit leaving that ISR continuation indefinitely suspended while unrelated
stock firmware or application contexts reuse its stack.

The same `_Thread_BSP_context` and scalar flags are used for host calls and IRQ
entry. They are not a stack of nested contexts. Current level-31 task execution
prevents ordinary timer nesting, which is essential to this implementation.
The processor's NMI exception still exists; priority 31 is not universal fault
or NMI exclusion.

## Saved-state ledger

| State | Current owner / preservation | Requirement before arbitrary preemption |
|---|---|---|
| Interrupted PC (process controls) | Hardware record at interrupt NFP−16 | Preserve that exact record through dispatch; priority-only context restore is not full PC restoration. |
| Interrupted AC / condition codes | Hardware record at NFP−12 | Retain until interrupt return; exercise interruptions between compare and branch. |
| Vector | Hardware record at NFP−8 | Retain/validate vector; do not treat reserved words as spare storage. |
| g0–g15 | Dedicated ISR saves 64 bytes per invocation | Preserve caller-clobbered globals as well as ABI callee-saved ones across asynchronous switches. |
| Local r0–r15, PFP/SP, return linkage | Register-window/procedure-frame mechanism; task switch stores PFP/SP and calls `flushreg` | Preserve interrupted frame/window chain and spill area; stress deep recursion and window spills. Do not equate a C call boundary with an arbitrary instruction. |
| Task context g8–g15 + PC priority | `context.S` uses 44-byte Context_Control; PC offset 8, g8 offset 12 through g15 offset 40 | Valid for existing cooperative call-boundary switching; insufficient alone for a full IRQ frame. Keep two context formats explicitly distinct. |
| Trace controls | No general per-task TC save in current context | Define debug/trace policy and verify required preservation before enabling traced tasks; do not claim hardware saves TC in the PC/AC record. |
| ISR stack | Firmware PRCB stack observed at C0001000; no owned RTEMS interrupt stack | Establish separate owned stack(s), guards and worst-case nesting depth. Keep suspended interrupt records live until their owning task resumes. |
| ISR nesting / dispatch state | Custom timer path bypasses a full BSP ISR framework | Integrate RTEMS ISR enter/exit accounting and dispatch-disable semantics; dispatch at the defined outermost exit. |
| Fault escape | Background faults switch to BSP continuation; callback faults use `_escape_context` | These are single-owner escape paths, not a nested-context recovery mechanism. Define monitor fault state and independent STOP before general preemption. |

Hardware layout above follows Intel manual §8.1.5/Fig.8-3; NFP is the ISR's new
frame pointer, not the interrupted task's FP. The manual describes 16-byte
interrupt-frame alignment. PFP return-type bits and the saved return linkage
must be preserved; an ordinary `ret` works here because the real interrupt frame
already exists. A synthetic thread startup frame needs its own validated recipe.
No unverified interrupt-frame offsets should be embedded in a new assembly stub.

## Concrete blockers and changes needed

1. `build.py` forces interrupt-enable levels and new task priorities to 31 and
   disables historical hardware-stack allocation macros. `net/app.c` also creates
   tasks at `RTEMS_INTERRUPT_LEVEL(31)` and asserts that level in `process()`.
   A new resident profile must replace these assumptions deliberately; changing
   a task option alone will not enable preemption.
2. Timer F2 is priority 30; it cannot interrupt level-31 application execution.
   A task below 30 can be interrupted, but the present firmware continuation and
   stack ownership still prohibit unrestricted execution inside the callback.
3. `context.S` restores only PC priority bits with mask 0x001f0000. It is not an
   asynchronous interrupt-frame restore. The `_ISR_reg_save` array remains as an
   unused historical symbol in this file; the current dedicated ISR does not use
   it. Do not describe that dead array as an active corruption bug.
4. Shared BSP/escape contexts and flags would be overwritten by naive nested
   entry. Replace them with explicit owner state/per-invocation records before
   lowering priorities or adding another interrupt-driven service.
5. lwIP is `NO_SYS=1`, `SYS_LIGHTWEIGHT_PROT=0`. Serialize its raw API in one task;
   ISR dispatch must queue network work rather than introduce concurrent callers.
6. The observed interrupt table is in ROM. Cached hardware vectors explain the
   current dedicated timer path; do not assume software `sysctl` posting can
   safely update the table's pending section. A resident BSP needs owned vector
   and pending state before relying on that mechanism.
7. Tick coalescing remains a clock-quality question: timer pending bits do not
   count all missed periods while priority masks delivery. Earlier silent-run
   rates near 100 Hz do not prove wall-clock accuracy during long masked work.
   Measure elapsed hardware time and worst masking interval under load before
   claiming a calibrated preemptive clock.

## Proposed resident context model and tests

Separate normal call-boundary context from an IRQ-suspended task. The latter owns
its original hardware record, complete global save area, interrupted window/stack
chain, saved scheduling metadata and any trace state required by the chosen
policy. Keep the record on owned storage until that task's IRQ continuation runs
again. Initially prohibit nesting in the new profile; validate outermost-exit
scheduling before adding any higher-priority ordinary IRQ. NMI remains separate.

Required tests: all global-register sentinels; compare/branch AC preservation;
deep calls forcing spills; simultaneous timer/control pending events; task
switch with another task's IRQ frame suspended; equal-priority time slicing;
CPU-bound low task interrupted by timed high task; nested-entry tests only after
an explicit nesting design; stack canaries and measured maximum usage; STOP while
application code is busy; deferred dispatch through RTEMS critical sections.

P0 result: audit and required-state model complete. Hardware validation of a new
frame-switching implementation is not complete. No resident preemption stub was
installed merely on the strength of the bounded eight-interrupt test.

Reference: Intel [i960 Rx Developer's Manual, 272736-002](https://datasheets.chipdb.org/Intel/80960/manuals/27273602.PDF),
§7.1, §8.1.3–8.1.5, §8.5 and chapter 9. Repository evidence:
`rtems/irq/context.S`, `timer_isr.S`, `timer_hw.h`, `rtems/net/app.c`, `start.S`,
`rtems/build.py`; earlier live captures in `artifacts/rtems-web-autonomous-20261011`.

## Follow-up: independent control under the existing priority policy

The [framed MU experiment](MU-FRAMED.md) now stops bounded RTEMS dispatch from
the timer handler and independently halts the timer. Its saved tick/heartbeat
remain unchanged across a later status exchange. Task priorities are still 31;
this does not remove blockers 1–4 above. Reclamation still uses the validated
firmware cleanup path after the ISR has returned. Next resolve owned stack,
complete frame preservation and continuation lifetime before CPU-bound trials.

## Owned execution-stack follow-up

[Owned C ISR storage and context-return stress](../interrupt/README.md) now pass
on hardware. This supersedes the lack of a separate C execution stack for the
new `irqctx`/`muctx` profiles, not for production `autonet`. PC.s=1 means nested
hardware entry follows current SP: the observed frame was in the RTEMS task
stack for the stress test and C0002050 for stock-background entry. ISP itself
remained C0001000. The original hardware frame is not relocated or independently
owned by a scheduler. Globals, hardware PC/AC record integrity, PC/TC roundtrips,
local-window/deep-call behavior and guards passed. Complete asynchronous task
switching, original-frame lifetime, IRQ accounting and nesting remain blockers.

## Two-task asynchronous continuation checkpoint

The isolated [switch profile](../switch/README.md) now keeps two task-specific
hardware frames, global saves and C ISR stacks live while timer-driven scheduling
alternates CPU-bound loops. RTEMS ISR accounting is unwound before dispatch, and
all 32 handlers per run resume and return before normal teardown. This closes
the controlled two-context experiment, not arbitrary owner registration, nested
interrupt scheduling or resident STOP. Deferred dispatch through live critical
sections and MU STOP while these contexts run are the next validation steps.

## Nested dispatch deferral result (2026-10-11)

The separate `defer` profile passed three bounded card runs using the real
RTEMS dispatch disable/enable functions at nested depths 2 and 1. Timer IRQs
continued, accumulated pending dispatch, and retained the same task owner.
Only outer enable permitted the other task to run. Both per-task ISR lifetimes
then drained; see [evidence](../../artifacts/irq-deferral-20261011/README.md).
This tests scheduler critical sections with timer IRQs, not arbitrary interrupt
nesting or MU STOP during a CPU-bound callback. Those control/lifetime paths
must be combined before claiming a resident preemptive monitor.

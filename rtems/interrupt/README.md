# Owned ISR execution stack and return-context preservation

**Later checkpoint:** [two per-task ISR continuations and bounded time-slicing passed](../switch/README.md).
The next-work section below records this owned-stack milestone’s earlier scope.

2026-10-11: implemented and tested on the card. The isolated `irqctx` profile
passed 126 hardware interrupts across three runs. `muctx` then passed 546
interrupts with bounded RTEMS, CTL1 control and independent STOP/HALT.
[Exact artifacts and verification](../../artifacts/notes/owned-interrupt-stack-20261011.md).

## What is owned

The new trampoline in `../irq/timer_isr.S`, selected by `I960_OWNED_STACK`, runs
the C interrupt handler on a dedicated 16,512-byte allocation in the uploaded
private RAM. Layout: 64-byte lower guard, 128 bytes for saved globals/metadata,
16,256 bytes for upward-growing C frames, and a 64-byte upper guard. Alignment
is 16 bytes, as supported by the i960 COFF toolchain. Global registers g0–g15
are saved before entering C; the assembly clears g14 for the C ABI.

**The original hardware interrupt frame is retained in place.** The processor
has already allocated it before our first instruction. The trampoline keeps its
SP in local r4, its save-area pointer in local r5, changes SP for the C calls,
then restores globals and the original SP and returns through the original
hardware frame. Deep calls may spill these locals into that frame; they remain
live until this same interrupt returns. We neither copy nor synthesize PFP,
RIP, PC or AC records, and do not change the global interrupt-stack pointer.

This distinction matters on this firmware: PC.s is already set when it calls
our code. Intel's interrupt rules allocate nested frames on the current stack,
not from the base ISP. In `irqctx`, the hardware frame was C0F5B0A0 in the
RTEMS task stack. In `muctx`, the sampled firmware frame was C0002050. The
base interrupt-stack register stayed C0001000. Moving ISP alone would not own
these nested frames, and moving their records casually would break return linkage.

## Context contract

| State | Preservation and evidence |
| --- | --- |
| g0–g14 | Explicit four-quadword save/restore; all 15 sentinels matched after the stress loop. |
| g15 / FP | Entry FP saved/restored with globals; hardware return restores the interrupted FP through the original frame chain. Probe FP matched before/after. |
| Local register windows, PFP/SP | Original hardware/call frames remain live. r4–r15 sentinels, PFP/SP and 25-level call chains passed; the r3 loop counter reached zero. |
| RIP / resume address | Uses the real hardware interrupt return. RIP may legitimately change on a call/interrupt; it is not compared as a constant sentinel. The probe resumed and returned normally. |
| PC and AC | Original hardware record at entry FP−16/−12 is copied for diagnostics and checked unchanged before return. Hardware restores it. Complete observed PC matched; compare/branch stress found no AC error. This is not exhaustive coverage of every possible AC/PC state. |
| TC modes | Save TC, restore only writable mode mask FE. The isolated ISR deliberately toggles mark-trace mode with PC.te clear; original TC=0 was restored after every roundtrip. No reserved bits are written. |
| TC event flags | Checked unchanged. These are not freely writable saved-thread state; no breakpoint/trace-fault virtualization is claimed. |
| Nesting | One active trampoline; a reentry flags failure without overwriting the live save area. Nested scheduling/NMI recovery has not been tested. |

The C handler checks both guards and the saved PC/AC/vector. The isolated test
recurses 25 levels inside the ISR and 25 levels in the interrupted task, with
volatile local buffers checked on unwind. Observed ISR SP samples span 3,264
bytes above the C-stack base in this stress run. This is a sampled bound for
that path, not a worst-case stack-usage proof. The background run samples only
entry/leave helpers; its 128-byte sample must not be described as total ISR use.

A complete interrupt return is now tested with owned C execution storage.
**This is not a relocatable per-task asynchronous context or unrestricted
preemption.** The original hardware frame and interrupted stack chain are still
borrowed until return. A scheduler must not abandon or reuse them. The ordinary
RTEMS call-boundary `Context_Control` remains 44 bytes and has not been promoted
into an asynchronous context format. Normal task priorities remain 31; only the
finite assembly stress loop lowers priority to 20 and restores it to 31.

## Profiles and reproduction

- `irqctx`: bounded stress profile; all interrupts stop before the callback
  returns. Use the ordinary `dac960rtems` transport. This profile does not use
  autonomous STOP semantics and must not be paired with `dac960auto`.
- `muctx`: the previous `muctl` bounded background profile with the owned C stack.
  Use the exact-image-pinned framed `dac960auto` variant. The optional diagnostic
  firmware STEP runs after independent STOP/HALT, not as part of that handshake.
- Existing `irq`, `auto`, `mu`, `muctl`, `net` and `autonet` retain their old entry
  path. The production Vader server uses its unchanged `autonet` binaries.

In the established remote build workspace:

```sh
python3 project/rtems/build.py --work . --profile irqctx
python3 project/rtems/transport/build.py --out irqctx-bounded
make -C /lib/modules/$(uname -r)/build M="$PWD/irqctx-bounded" modules
python3 project/rtems/interrupt/check_build.py irqctx
# Stop production normally and verify full restoration/unload first.
sudo python3 project/rtems/interrupt/live_context.py --payload irqctx/kernel.bin \
  --module irqctx-bounded/dac960rtems.ko --output irqctx-live

python3 project/rtems/build.py --work . --profile muctx
python3 project/rtems/control/build_framed_transport.py \
  --payload muctx/kernel.bin --out muctx-module
make -C /lib/modules/$(uname -r)/build M="$PWD/muctx-module" modules
python3 project/rtems/interrupt/check_build.py muctx
sudo python3 project/rtems/control/live_framed.py --owned-stack \
  --payload muctx/kernel.bin --module muctx-module/dac960auto.ko \
  --reader control-prototype/read_mu --output muctx-live
```

Use fresh output directories. The isolated response is 392 bytes: original
64-byte IRQ report, 14 diagnostic words, globals before/after, locals before/after,
and PC before/after plus TC before/after. STOP keeps its original 64-byte ABI.
Both drivers still verify full borrowed-RAM restoration. The framed driver's
final firmware cleanup validates timer/vector/masks before releasing memory.
No memory is reclaimed merely because the independent HALT response arrived.

## Next required work

Define a separate asynchronous task record that owns the original hardware
record, global save area and entire suspended stack/window chain. Then implement
a controlled two-context switch with distinct storage and explicit ISR
enter/exit accounting. Test resuming each interrupted context, guards, deferred
dispatch, and independent STOP under CPU-bound load before enabling arbitrary
RTEMS task preemption. This requires more than changing a task priority.
NMI/trace-fault handling, nested IRQ scheduling and worst-case stack use remain
separate validation gaps.

Primary reference: Intel *i960 Rx I/O Microprocessor Developer's Manual*,
272736-002, §§6.2.44, 7.1.2, 8.1.5, 8.2.9.1–2, 10.1.1 and appendix C. The
previously downloaded manual was read locally; these rules were checked against
actual linked assembly and the live captures, not inferred from an emulator.

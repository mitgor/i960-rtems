# Shared allocations and heap interrupt measurements

`--heap-shared` is an opt-in exclusive resident build layered on `--general-heap
--extra-ram --fault-owner --secondary-reset`. It keeps the same 69,952-byte
application heap and 128-slot external packet queue. It does not extend the
kernel workspace, task stacks, or RAM grant. The cooperative `autonet` server
remains a separate option. Reboot restores stock firmware ownership; do not
force-unload a retained exclusive session.

## Shared lifetime contract

Eight shared objects fit within the heap's existing 64-allocation limit. The two
actors are the actual resident worker tasks: API calls check `_Thread_Executing`
against their recorded RTEMS thread identities. A handle contains a 29-bit
monotonic generation and three-bit slot; generation exhaustion refuses further
creation instead of wrapping. A stale handle cannot acquire a reused slot.

| API | Contract |
| --- | --- |
| `resident_shared_new(actor, bytes)` | Allocate and create the owner's reference; return zero on refusal. |
| `resident_shared_acquire(handle, actor)` | Add one reference for the calling actor; duplicate references refuse. |
| `resident_shared_pin(handle, actor)` | Return a pointer while that actor holds a reference; one pin per actor. |
| `resident_shared_unpin(handle, actor)` | End pointer use before acknowledging cancellation. |
| `resident_shared_cancel(actor)` | Trusted cancellation request from either task; block the actor's new shared allocations, references and pins, mark existing references, and close its owned objects to new borrowers. |
| `resident_shared_ack(handle, actor)` | Return 2 while the actor is pinned, 1 on invalid use, or 0 after releasing its canceled reference. Free only after the last reference disappears. |
| `resident_shared_resume(actor)` | Clear cancellation only when the actor has no remaining references. |

Integer status APIs otherwise return zero for success and one for refusal.
The owner can acknowledge and resume while a borrower still holds the closed
object. That borrower retains its pointer until it unpins and acknowledges.
Raw `free` and `realloc` refuse registered shared pointers. Registry consistency,
heap metadata and redzones are checked before each operation; inconsistent
shared state enters terminal containment with heap error 11 and retains memory.

Pins protect **lifetime**, not concurrent data access. Applications must arrange
data synchronization separately. These APIs do not delete arbitrary tasks,
provide memory protection, or infer that an unresponsive task has stopped using
its pointer. Uncertain completion retains the allocation. Private raw allocations
remain the caller's responsibility. Normal STOP and the autonomous deadline let
both workers finish their current operation, cancel/unpin/acknowledge references,
free private blocks, and drain both saved interrupt contexts before parking.
Replay accepts an active STOP reason only after a recorded successful STOP, or
an active deadline reason only at/after the armed deadline. RNT7 permits up to
100 additional ticks for acceptance of in-flight work draining; the final state
still requires every reference, allocation and IRQ context drained. This is a
test acceptance limit, not a separate hardware watchdog or a demonstrated
worst-case shutdown bound.

## Shorter masked operations

The original guarded heap performed calloc zeroing and realloc copying at
interrupt priority 31. With `--heap-shared`, allocation and validation remain
serialized, but large zero/copy work runs after restoring the caller's priority.
A `busy` reservation prevents free or realloc of either in-flight buffer. The
caller reacquires the lock, validates the heap, and clears reservations before
publishing the result or freeing the old block. Abandoning an operation retains
its reserved buffers; it does not authorize another task to reclaim them.

An outer caller mask still applies. In particular, startup tests run before
normal task scheduling, so an unlocked copy during startup does not establish
runtime preemption. The runtime workload separately counts timer interrupts
observed across zeroing and copying, checks all resulting bytes, and keeps
ordinary worker allocations and shared cancellation active concurrently. Every
1,000 ticks, actor 0 attempts 56 KiB calloc and a 30 KiB realloc while actor 1 and
shared objects remain live. Fragmentation can legitimately refuse these large
requests: the loop counts refusals, checks the preserved realloc buffer, frees
it, and continues. It must not equate total free bytes with a contiguous block.

## Measurement method and telemetry

After exclusive RAM/exception/SCSI admission, this profile takes timer 0 at
`ff000300..ff000308`, masks its interrupt source (bit 12), and runs an autoreload
32-bit downcounter at bus/8. Timer 1 continues the validated 100 Hz scheduler
clock with reload 41,667 and interrupt mask bit 13. Timing reads only TCR0:
reading the mode register could acknowledge terminal count. Default/cooperative
builds do not take timer 0. The reported nominal scale is 4,166,700 counts/sec,
from the existing board clock calibration, not a new precision oscillator test.

Lock brackets measure protected heap work. Samples count lock sections,
including refused operations, rather than API invocations: optimized calloc and
realloc can contribute two sections per call. They exclude the final statistics
update/unmask overhead and any surrounding caller critical section. Empty
brackets supply an instrumentation reference. Per-operation maxima are observed
values, **not worst-case execution-time guarantees**. Interrupt records begin
at the timer ISR's C entry, not the physical interrupt edge; timer-1 entry phase
is modulo one 10 ms period. Independent timer-0 inter-entry gaps expose longer
interrupt delays. Unsigned deltas and a 64-bit accumulated counter support
counter wrap (about 1,031 seconds).

RNT7 retains the normal 64-word snapshot layout. Matching modules support
control op 7, argument 1, for a separate HSL1 diagnostic snapshot, then existing
op 5 word reads. Argument 0 still reads the normal page. The diagnostic trigger
uses token `0x96000000|epoch` and acknowledgement `0x97000000|epoch`. Modules reject
other diagnostic arguments. Exact image/module hashes and raw control replies
are retained for independent replay.

| Diagnostic words | Meaning |
| --- | --- |
| 0–4 | HSL1, schema version, nominal counter Hz, reload, ready |
| 5–11 | ISR samples, maximum gap/phase, 64-bit elapsed count, minimum gap, timer-1 reload |
| 12–43 | Eight groups of count/max/sum-low/sum-high: check, malloc, calloc, realloc, free, share, cancel, empty |
| 44–48 | Shared creates/retires/cancel requests/deferred acknowledgements/rejections |
| 49–51 | Live objects/references/pins |
| 52–55 | Completed cycles/content checks/error/self-test |
| 56 | Versions 1–2: generation; version 3: nonfatal large-workload allocation refusals |
| 57–58 | Versions 2–3: zero/copy calls spanning a timer interrupt; version 1: old timer-0 reload/count |
| 59–63 | Canceled actor mask, allocations, frees, live bytes, validity |

## Reproduction and evidence

```sh
python3 project/rtems/build.py --work scsi-drain --profile residentnet \
  --secondary-reset --fault-owner --extra-ram --general-heap --heap-shared
python3 project/rtems/residentnet/test_general_heap.py \
  --rtems scsi-drain/rtems-4.6.6 --out shared-native --shared
python3 project/rtems/residentnet/build_transport.py \
  --out residentnet-module-shared --payload scsi-drain/residentnet/kernel.bin
make -C residentnet-module-shared
sudo python3 project/rtems/residentnet/live.py \
  --payload scsi-drain/residentnet/kernel.bin \
  --module residentnet-module-shared/dac960auto.ko --output shared-endurance \
  --secondary-reset --fault-owner --extra-ram --general-heap --heap-shared \
  --ticks 180000 --rounds 40 --round-interval 45 --parallel --burst --deadline --drop-data
```

The Linux freestanding 32-bit harness compiles the actual RTEMS 4.6.6 allocator.
It supports `--iterations 100000` (200,000 worker updates) and covers
5,000 deterministic randomized shared API operations, 1,000 repeated
uncertain acknowledgements, stale/foreign actor rejection, generation exhaustion,
shared-registry corruption, busy buffer refusal, counter carry, and the existing
heap exhaustion and corruption cases. Its synthetic counter is not hardware
latency evidence. Physical captures, exact per-image measurements, and the
thirty-step ledger are in [the batch artifacts](../../artifacts/rtems-shared-heap-20261011/README.md).

## Endurance capture cost

The first corrected-heap endurance run timed out in HTTP after about twenty
minutes despite healthy heap snapshots and checksum-valid card responses. The
host test rewrote its entire packet history after every exchange; its 20.9 MB
history cost about 207 ms per rewrite on the Linux host. This can delay packet
forwarding and create a growing retransmission backlog.

`live.py` now appends each complete request/response record to
`packet-journal.jsonl` before returning it to the pump, and writes the compatible
`packets.json` array once in final cleanup. The verifier requires both to match
when the journal exists and rejects truncated, missing, duplicate or changed
records. Historical array-only captures remain readable. No audit bytes or
protocol checks are removed, and the card image is unchanged by this host fix.
`benchmark_packet_log.py` measures both recorder paths without touching the card.

## Accepted card results

The unchanged corrected image passed the repeat with the append recorder:
40 dual-stack rounds, 4,030 checksum-verified packets, timer wrap and 180,008
ticks. The deadline was 180,000; in-flight work drained in eight extra ticks.
All 194,154 application allocations and 14,764 shared objects were released.
There were 59,046 pinned acknowledgements deferred and 180 interrupt-spanning
zero operations plus 180 copies. The final measured protected-section maxima
were 261.36 µs for calloc and 1,985.02 µs for realloc, against baseline
14,803.80 µs and 11,064.15 µs. The whole-system maximum ISR gap remained
13,270.21 µs. See the artifact table for all operation samples and limitations.

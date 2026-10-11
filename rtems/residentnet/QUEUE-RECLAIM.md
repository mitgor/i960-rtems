# Reclaiming the fallback queue and preempting network work

`--queue-reclaim` requires `--heap-shared --general-heap --extra-ram
--fault-owner --secondary-reset` on the exclusive `residentnet` profile. It
adds a second application heap and runs the network worker at interrupt priority
20 except for short ownership transfers. The default/cooperative profiles remain
available. Exclusive admission still parks stock firmware and requires reboot
before restoring RAID/SCSI; no flash is written.

## Ownership transfer

The 68 × 1,500-byte fallback queue is needed during `network_init`, before the
external RAM probe/admission completes. Reclamation occurs only after checking
the original pointer, capacity, head, tail, occupancy and every frame length,
copying all queued bytes to the external 128-slot queue, and publishing its new
pointer/capacity/tail. This happens before worker execution. Repeat migration or
repeat reclamation is rejected. There is no transition back to the fallback.

The original 102,000-byte object is 16-byte aligned and wholly inside the already
owned mutable upload. Its first and last 64 bytes become guards. The interior
**101,872 bytes** becomes a separate RTEMS `Heap_Control`; the original external
69,952-byte heap remains intact. Total arena storage is **171,824 bytes**. This
is discontiguous storage, not a single allocation of that size. Allocator headers,
alignment and per-allocation redzones consume some of it. The wrapper rejects
requests above 101,808 bytes; available contiguous space can be smaller.

Allocation tries the external arena first, then the reclaimed arena. Exact
registered pointers choose the arena for free; realloc can cross arenas while
retaining its original block on failure. Physical/free-list metadata is validated
independently for each arena, including registry membership and saved alignment
offsets. The 64-live-allocation cap is global. Both arenas use the existing shared
reference/pin/cancellation rules. Neither kernel workspace nor task stacks grow. The object stays in the linked
BSS; reclamation changes its runtime owner, not the uploaded image footprint.
The lwIP static memory pools also keep their existing sizes.
No new firmware, cache or SCSI memory range is granted.

Admission tests simultaneous near-full allocations in both arenas and fills/checks
the reclaimed allocation before releasing it. Shared startup tests use an 80 KiB
object; every 32nd worker cancellation cycle also uses 80 KiB, forcing that object
into reclaimed storage. Guard failure is part of normal heap-entry admission.

## Network interrupt contract

Only worker 0 calls lwIP and removes frames from its output queue. Worker 1 does
heap/cancellation work. The ISR processes the PIO control channel, never lwIP.

RX `ready` remains asserted while worker 0 processes the packet. Host begin,
write and commit commands reject during that lease. Length, word count and ready
are released together under the short priority-31 mask. New RX arriving during
TX production belongs to the next pass.

TX `txlen == 0` hides the buffer while worker 0 clears and fills it. Reads and
acknowledgements reject while unpublished; a length query reports zero. Worker 0
publishes the completed length under a short mask. Once published, the buffer is
immutable until the host acknowledges it. The next worker pass reuses it only
after observing that acknowledgement. Shared publication fields are volatile;
mask/enable assembly has compiler memory clobbers.

The worker samples ticks before processing and advances `net_tick` to that sample,
not to the later completion time. Interrupts during processing therefore remain
due on the next lwIP pass. STOP asks workers to finish their in-flight work and
drain; it does not invalidate a leased packet or force-delete a task. The retained
terminal state still requires reboot.

## Tests and reproduction

Native tests exercise all 69 initial queue occupancies, 70,656 guard-bit
corruptions, invalid migration state, data isolation, ISR packet commands during
worker leases, unpublished TX reads, elapsed ticks and STOP retention. The actual
32-bit RTEMS allocator harness adds second-arena exhaustion, corruption and shared
cancellation stress. Linux native tests complement physical acceptance.

```sh
python3 project/rtems/build.py --work scsi-drain --profile residentnet \
  --secondary-reset --fault-owner --extra-ram --general-heap --heap-shared \
  --queue-reclaim
python3 project/rtems/residentnet/test_general_heap.py \
  --rtems scsi-drain/rtems-4.6.6 --out reclaim-native \
  --shared --queue-reclaim --iterations 100000
python3 project/rtems/residentnet/build_transport.py \
  --out residentnet-module-reclaim --payload scsi-drain/residentnet/kernel.bin
make -C residentnet-module-reclaim
```

Pass the same feature switches to `live.py`. Its RNT8 snapshot reports total
arena bytes in word 49 and the original external base in word 48. Build symbols
and `ram_audit.py` locate the second arena; never assume its linked address across
builds. Replay binds RNT8 and the new byte count to the image/build flags.

`--heap-test 5` corrupts the reclaimed lower guard; `--heap-test 6` corrupts its
first physical block extent. Use `live_fault.py --kind 4` and `verify_fault.py`,
archive the exact image/module/capture, and reboot after each terminal test.
Do not use fault-injection builds for service.

Physical results, measured latency, failures and the thirty-step ledger are in
[the batch artifacts](../../artifacts/rtems-queue-reclaim-20261011/README.md).

## Diagnostic version 4

The HSL1 page keeps 64 words. Version 4 replaces the old constant timer-0 reload
and ready fields (words 3 and 4) with counts of network-processing brackets and
TX-production brackets that span at least one timer tick. These count calls,
not interrupts. Timer 0 still reloads `ffffffff`; frequency, scheduler reload,
IRQ samples, gap/phase maxima and 64-bit elapsed time retain their existing fields.
Heap copy preemption counters remain words 57–58. Versions 1–3 remain replayable.
The counters demonstrate that interrupts occur across actual card work; they do
not supply a worst-case latency bound. Terminal guard injection retains resources
rather than trying to repair the arena.

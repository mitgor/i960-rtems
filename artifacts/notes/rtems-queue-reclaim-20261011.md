> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# RTEMS fallback queue reclamation — 2026-10-11

This batch reuses the obsolete internal packet queue as a second guarded
application heap, and moves lwIP processing and packet copying outside the
worker's interrupt mask. Contract and commands:
[QUEUE-RECLAIM.md](../../rtems/residentnet/QUEUE-RECLAIM.md).

The added arena has 101,872 bytes, making 171,824 bytes across two discontiguous
arenas. The external packet queue remains 128 × 1,500 bytes. No additional
firmware/SCSI RAM range is granted, no flash is written, and the kernel workspace
is unchanged. Exclusive sessions retain card/module resources until reboot.

## Captures

Each experiment archive contains its exact image, symbols, map, build flags,
matching module, source snapshot and raw capture. Unpack each into a separate
directory; symlink `residentnet` to `scsi-drain/residentnet` before invoking the
current independent verifier. `verify.py` checks network runs; `verify_fault.py`
checks terminal injection runs. `evidence/` contains the resulting reports.
The repository artifact inventory covers the compressed bytes.

| Archive | Result |
| --- | --- |
| `reclaim-endurance.tar.xz` | Final image: forty dual-stack rounds / 180,008 ticks; all 189,150 allocations and 14,138 shared objects drained. Full independent replay passed. |
| `reclaim-smoke-host-failure.tar.xz` | Image admitted; host burst lookup lacked RNT8 and raised KeyError before traffic. Preserved failed attempt, not an acceptance pass. |
| `reclaim-smoke-pass.tar.xz` | Three dual-stack rounds, saturation and TCP loss; host STOP parked at tick 5,310. All 5,709 allocations and 418 shared objects released. Independent replay passed. |
| `reclaim-guard.tar.xz` | Reclaimed lower-guard corruption: error 1, stable terminal record, 3 allocations / 564 live bytes retained, callbacks refused, STOP did not resume firmware. |
| `reclaim-metadata.tar.xz` | Reclaimed physical-extent corruption: error 2, stable terminal record, 3 allocations / 564 live bytes retained. Independent replay passed. |

The failed lookup is now shared between the burst driver and replay verifier in
`protocol.py`, with RNT8 included. RX busy responses during processing are expected
backpressure; the host retries the original packet. The passing smoke run did
not lose packet identity through those retries.

## Latency and scope

The first passing reclaimed-heap run measured a 10,349.92 µs maximum timer ISR gap
and 1,657.67 µs maximum entry phase. The previous thirty-minute RNT7 run measured
13,270.21 µs and 3,419.25 µs. Durations and shared-allocation workloads differ;
this comparison is observational, not an isolated A/B benchmark or a worst-case
bound. The final diagnostic extension records actual processing/copy brackets
that span timer interrupts.

Protected heap maxima in the smoke run were 348.24 µs (check), 2,208.70 µs
(malloc), 342.24 µs (calloc), 2,186.86 µs (realloc), 2,220.46 µs (free), 322.32 µs
(share), and 321.84 µs (cancel). A second arena adds validation work. Large
startup tests remain inside their outer admission mask; operation brackets do
not claim to measure all system latency.

## Final endurance result

Image SHA-256: `ca57958d685341d63d40c5da981ea36eee780b356804adaf6d0343ae56494b28`.
Boot: `60e13ffc-385f-4147-9788-63e28bd7387c`. Text/data/BSS are
126,848 / 468 / 325,360 bytes, with 1,824 bytes of unused mutable tail.
The reclaimed arena is `c0f4e060..c0f66e50` in this image; its linked address is
not an ABI. The external arena remains `c022ee80..c023ffc0`.

Forty concurrent IPv4/IPv6 UDP/TCP/HTTP rounds passed, with 4,524 independently
validated packets and 331 retransmitted segments. The burst submitted 160
requests, received 129 replies, filled all 128 queue slots and counted 31 drops;
10 RX-busy retries were handled during the burst. Intentional IPv4 and IPv6 TCP
data loss recovered. All 24 snapshot corruptions used by replay rejected.

The deadline requested shutdown at tick 180,000; both workers and IRQ contexts
had drained at 180,008. All 189,150 allocations and 14,138 shared objects were
released; references, pins and live bytes were zero, with ownership 31.
There were 14,136 completed sharing cycles, 55,619 deferred acknowledgements,
55,618 retained-content checks and no large-workload allocation refusals.
The final image observed 180 zero operations and 180 copy operations spanning
interrupts, plus 182 network-processing and 32,833 TX-production brackets.
The timer's accumulated high word advanced across wrap.

The largest ISR gap was **10,688.31 µs** (previous RNT7 endurance: **13,270.21 µs**),
maximum entry phase **1,535.27 µs**, and mean period **10,000.232 µs**.
This is a successful measured reduction with a changed shared-memory workload,
not a controlled single-variable benchmark or hard bound. Final protected heap
maxima were 348.96 µs check, 2,204.62 µs malloc, 340.32 µs calloc, 2,189.02 µs
realloc, 2,218.30 µs free, 321.60 µs share and 340.80 µs cancel. Empty timing was
1.44 µs. See `evidence/endurance-replay.json` for all counters.

The release native harness passed 200,000 worker updates, 5,000 randomized
shared operations, 1,000 deferred acknowledgements, cross-arena realloc,
32 second-arena free-list pointer mutations, and the existing guard/offset/
registry corruption tests. Shared single-arena regression passed another
200,000 worker updates; the basic profile passed 2,000. The complete offline
suite passed, and historical RNT5/RNT6/RNT7 captures still replay successfully.

## Thirty implementation and validation steps

1. Audited initialization, external migration and parked-firmware ownership.
2. Audited worker/ISR access to RX, TX and lwIP state.
3. Added the opt-in build dependency chain; cooperative/default paths remain.
4. Aligned and range-checked the complete internal fallback object.
5. Validated migration pointer, indices, occupancy and every frame length.
6. Preserved all queued frames before the irreversible external handoff.
7. Added first/last 64-byte guards and refused repeated reclamation.
8. Initialized a second real RTEMS heap in the remaining 101,872 bytes.
9. Routed allocation and exact-pointer free across the two arenas.
10. Validated physical blocks, free lists and registry membership per arena.
11. Preserved realloc data and ownership across arena changes and refusal.
12. Tested simultaneous near-full allocations and reclaimed-byte patterns.
13. Moved lwIP processing outside the priority-31 mask.
14. Retained the committed RX lease until processing completes.
15. Kept incomplete TX bytes unpublished and published length under a short mask.
16. Preserved timer ticks arriving during network processing.
17. Tested the actual worker handoff with simulated ISR commands and STOP.
18. Tested 69 migrations, 70,656 guard-bit mutations and data isolation.
19. Added 80 KiB shared/cancelled objects that must use the reclaimed arena.
20. Tested the actual 32-bit allocator, second-arena corruption and cross-arena realloc.
21. Bound RNT8 ownership/heap size to build flags and replayed historical captures.
22. Preserved and corrected the first physical attempt's host protocol lookup error.
23. Passed physical saturation, dual-stack loss recovery and explicit STOP/drain.
24. Added and passed reclaimed-guard corruption containment on the card.
25. Added and passed reclaimed-metadata corruption containment on the card.
26. Added version-4 network/copy interrupt-span counters and corruption checks.
27. Final native/basic/shared regressions and complete offline suite.
28. Thirty-minute network/cancellation endurance and timer-wrap acceptance.
29. Restore and verify the public cooperative IPv6 server after reboot.
30. Reconcile findings, narrative, exact binaries, raw evidence and Git inventory.

All thirty work units completed. These are implementation/validation steps,
not thirty independent card boots. Five recovery reboots returned without
physical intervention. The cooperative IPv6 server was restored on boot
`de71488a-5c13-4b83-a5d7-2f03531c86a4`; a Mac-side request returned HTTP 200
with the RTEMS/Vader page. `reclaim-production.tar.xz` preserves its exact
image/module/launcher and frozen startup metadata, excluding live traces and
visitor records. The service is left running.

## Remaining limits

- The two heaps are discontiguous. Aggregate capacity does not make a 171 KiB
  allocation possible; the wrapper caps a request at 101,808 bytes before
  fragmentation and live allocations are considered.
- This reassigns an existing BSS object. It does not enlarge the upload, kernel
  workspace, task stacks or lwIP's static pools, or establish further RAM ownership.
- Shared cancellation still needs explicit references, pins and acknowledgements
  from the two registered worker actors. Unknown pointer use retains memory.
- Network IRQ-span telemetry counts timed brackets; TX production includes clearing
  an unpublished buffer even when the output queue is empty. It is not a packet
  count. IRQ gap/phase results are observations, not worst-case guarantees.
- The resident harness remains bounded and reboot-only. A permanent resident
  service, broader task ownership and further control-path latency work remain
  separate follow-ups; the cooperative public server remains the service option.

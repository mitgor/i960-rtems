# RTEMS shared-heap and latency batch — 2026-10-11

This batch adds explicit shared-allocation lifetime control, measures heap
interrupt masking with an independent timer, reduces masked copy work, and
extends resident dual-stack network testing. It grants no new RAM and writes no
flash. Exclusive sessions retain the card/module/DMA resources until reboot.
The cooperative public server remains the production option.

Contract, telemetry and reproduction: [SHARED-HEAP.md](../../rtems/residentnet/SHARED-HEAP.md).
Archives contain the exact image, COFF/ELF, map/symbol/build files, matching Linux
module, source snapshot, and captures. Unpack each separately and symlink
`residentnet` to `scsi-drain/residentnet` for the current independent verifier.
Root `artifacts/SHA256SUMS` and `artifact-inventory.json` cover archived bytes.

## Physical experiments and acceptance

| Archive | Scope | Outcome |
| --- | --- | --- |
| `shared-heap-journal.tar.xz` | Final unchanged card image plus append recorder; 40 rounds / 180,008 ticks | Passed full independent replay, 194,154 allocations freed, all 14,764 shared objects retired |
| `shared-heap-smoke.tar.xz` | Locked-copy baseline; bounded 100 ticks, then resident 6,000 ticks / 3 dual-stack rounds | Passed, 6,604 allocations freed, 500 cancellation cycles, 2,001 deferred acknowledgements |
| `shared-heap-optimized.tar.xz` | Reserved/unlocked copies; host STOP after 6,737 ticks / 4 rounds | Passed, 7,401 allocations freed, 559 complete cycles, 2,236 deferred acknowledgements |
| `shared-heap-http-timeout.tar.xz` | Corrected card image, first 30-minute attempt | HTTP receive timeout after 118,070 ticks; heap healthy, timer wrap recorded; not an acceptance pass |
| `shared-heap-fragmentation.tar.xz` | Larger-workload first endurance attempt and extended native test | Host-aborted at 31,932 ticks after the native test found a false fatal assumption about contiguous free space; incomplete capture, not an endurance pass |

The baseline measured maximum protected calloc work of **14,803.80 µs** and
realloc work of **11,064.15 µs**. After moving memory work outside the allocator's
own mask, the STOP run measured **273.12 µs** for calloc and **1,984.54 µs** for
realloc; its largest malloc/free measurements were also below 2 ms. Empty
instrumentation was 1.44–1.68 µs. These are observed bracket values including
validation, not hard real-time bounds or whole-system interrupt latency.
The maxima include the startup large-buffer benchmarks; startup retained its
outer mask even in the optimized build. The small optimized workload observed one zero
operation spanning an interrupt and no copy operation spanning one, which is
why the next image increased the runtime buffers.

The STOP replay initially rejected a valid transitional snapshot: host STOP had
been acknowledged but both workers had not yet parked. The checker now accepts
that active reason only after the control journal records a successful STOP.
Unsolicited transitions still reject, as do undrained final snapshots. Deadline
transitions require the armed tick limit to have elapsed. RNT7 allows at most
100 additional ticks for final drain acceptance; this does not create a new
hardware watchdog or establish a worst-case bound.

The longer native run found fragmentation at worker tick 44,000. Its first
30 KiB allocation succeeded, but a same-size realloc could not find another
contiguous block. The allocator correctly returned null and kept the old block;
the test incorrectly asserted success. The initial native harness then jumped
to an uninitialized failure fixture and segfaulted. Both test problems were
corrected: expected large-request refusals retain/check/free the original data,
and unexpected native poison now exits with an explicit error. This was not a
hardware corruption. `evidence/native-fragmentation-debug.txt` records the
original native binary at poison 10, tick 44,000, with the old allocation still
registered. The partial live run was stopped at the host and the
machine rebooted with resources retained; no forced unload was attempted.

## Thirty-step implementation and validation ledger

1. Recovered the current card ownership and previous guarded-heap contract.
2. Audited allocator masking and the independent timer/interrupt registers.
3. Added an opt-in shared-heap build flag with the existing ownership dependencies.
4. Took timer 0 only after exclusive admission, leaving scheduler timer 1 intact.
5. Added protected-operation timing, maxima, sums and empty-bracket calibration.
6. Recorded timer ISR gaps, entry phase and 64-bit accumulated elapsed counts.
7. Added a separate diagnostic page through the existing monitor control channel.
8. Pinned diagnostic module behavior to the matching shared-heap image.
9. Implemented generation-tagged handles and actual RTEMS actor identity checks.
10. Added reference and pin tracking without authorizing raw-pointer reclamation.
11. Added cancellation requests, deferred acknowledgements and last-reference free.
12. Refused stale handles, wrong actors, duplicate borrowing and raw shared free/realloc.
13. Validated the shared registry before operations; corruption retains resources.
14. Added card worker cycles retaining and checking borrowed data across preemption.
15. Integrated cooperative allocation/reference drain with STOP and the deadline.
16. Added native randomized API, indefinite-acknowledgement and generation-limit tests.
17. Built and link-audited the baseline; passed restoring bounded entry on the card.
18. Measured locked-copy baseline latency during 6,000 resident ticks and networking.
19. Added busy reservations preventing reclamation of buffers being zeroed/copied.
20. Moved calloc/realloc memory work outside the allocator's own interrupt mask.
21. Tested optimized allocation and explicit host STOP on the card; all memory drained.
22. Fixed replay of the journal-authorized STOP transition and tested rejection cases.
23. Enlarged runtime memory operations and observed interrupts across both kinds.
24. Found the fragmentation assumption with extended native stress; preserved the partial card evidence and corrected the workload.
25. Passed 200,000 native worker updates, including a counted large-allocation refusal and 210,572 allocations freed; cross-built and audited the corrected image.
26. Checked malformed diagnostic records and replayed historical RNT5/RNT6 captures.
27. Diagnosed the HTTP endurance timeout and measured the full-history recorder cost; added a full-record journal and corruption tests.
28. Passed forty dual-stack rounds, timer wrap and complete packet/control replay at 180,008 ticks with the unchanged card image.
29. Rebooted successfully and restored cooperative public IPv6 HTTP; the Mac received HTTP 200 and the Vader/RTEMS page.
30. Documented the contract, narrative, failed attempts and accepted measurements; collected binaries/captures/native sources and the Git artifact inventory.

## Limits and follow-up

- Timing brackets exclude statistics update/unmask overhead and caller-owned
  outer critical sections. Whole-system IRQ gaps also include network work and
  other masked regions; the measured heap improvement does not establish a hard
  deadline for the entire resident system.
- Sharing is explicit and limited to two registered workers/eight objects. Pins
  preserve lifetime; they are not a data mutex or memory protection. A
  non-cooperative holder retains its memory. General task deletion/reclamation,
  arbitrary resource graphs and lwIP packet-lifetime integration remain open.
- Large allocation refusal is expected under fragmentation. Total free bytes do
  not promise a contiguous allocation. The existing heap size and RAM grant are
  unchanged; the RTEMS kernel workspace and task stacks are still separate.
- Shared-registry corruption and generation exhaustion are native tests in this
  batch, not new physical fault injections. Previous physical heap guard and
  metadata containment evidence remains in the general-heap batch.
- Endurance traffic is forty spaced local IPv4/IPv6 UDP/TCP/HTTP rounds, a queue
  saturation burst and deliberate TCP data loss. It is not saturated Internet
  throughput, a multi-day service test, or disk/RAID validation.

## The host recorder became part of the network problem

The corrected image reached 118,070 ticks before a client HTTP timeout ended
its first endurance attempt. Its last snapshots still had valid heap/ownership
checks, and the independent timer had wrapped. All 3,437 captured packets pass
checksum/stream validation; 245 retransmitted segments and repeated handshakes
show a deteriorating exchange. This is partial evidence, not a completed
networking or allocation-drain pass. The raw PCAP and packet analysis are saved.

The harness rewrote `packets.json` after every successful packet ioctl. At
3,297 records (20,870,137 bytes), this cost about 207 ms in the initial Linux
measurement. A matched ten-sample benchmark measured **188.43 ms per rewrite
versus 0.200 ms per appended full record**. The journal retains all request and
response bytes, produces the compatible full array once at close, and replay
checks exact equality. Four damaged-journal cases reject. Completed client
rounds now persist separately as progress. The repeat uses the same image hash
`a3a8d174d2651eac3daf8da1c37d0188645b6fd1abbddf4aed6b127dd172dbc8`.

The final link audit still shows a **102,000-byte internal fallback queue**
(68 × 1,500), even though live admission switches to the 128-slot external
queue. `queue_extend.h` copies queued initialization frames before changing the
pointer; that storage has not been reclaimed in this batch. Auditing a smaller
initial queue, or a proven post-transfer reuse, is a concrete future route to
more space inside the existing upload grant. It is not newly available memory
or a kernel-workspace expansion today. The static audit's `queue_slots: 68`
describes that linked fallback; live telemetry verifies the active capacity 128.

## Final accepted endurance result

`shared-heap-journal.tar.xz`, boot `955ae4ad-4612-46cb-b9f0-5a52cca92077`,
passed all forty rounds (560 client results). Independent replay checked all
**4,030 raw packets**, full TCP streams/checksums, packet-journal equality, image
and module hashes, original firmware identity, control replies and final drain.
The 160-request saturation burst returned 129 replies, dropped 31, and reached
the expected 128-slot queue peak. Intentional IPv4/IPv6 TCP data loss was retained;
208 retransmitted segments were verified. This is spaced endurance traffic,
not a high-throughput claim.

The autonomous deadline requested shutdown at 180,000 ticks. Parking occurred
at **180,008**: eight further ticks (nominally 80 ms) allowed in-flight work to
finish. Both workers and their saved IRQ contexts drained. All **194,154 heap
allocations** were freed and all **14,764 shared objects** retired, leaving zero
objects/references/pins/live bytes. There were **14,762 completed cycles**,
**59,046 deferred acknowledgements**, **29,528 rejected shared operations**, and
**59,045 retained-content checks**. Both zero and copy work spanned interrupts
in **180 calls each**. No large-request refusal occurred on this physical run;
the extended native run separately exercised and counted one.

The timer's elapsed accumulator crossed 32 bits and recorded a mean ISR period
of **10,000.221 µs**. Maximum inter-entry gap was **13,270.21 µs** and maximum
timer-1 entry phase **3,419.25 µs**. Those whole-system measurements include work
outside the heap and must not be confused with the shorter allocator brackets.

| Protected operation | Baseline max µs | Final max µs | Final mean µs |
| --- | ---: | ---: | ---: |
| check | 242.40 | 274.32 | 241.89 |
| malloc | 1927.18 | 1976.38 | 234.03 |
| calloc | 14803.80 | 261.36 | 226.66 |
| realloc | 11064.15 | 1985.02 | 218.75 |
| free | 1913.98 | 1968.22 | 266.07 |
| share | 234.48 | 248.40 | 219.39 |
| cancel | 239.52 | 252.00 | 222.18 |
| empty | 1.44 | 1.44 | 1.38 |

The final image has 125,440 bytes of text and 1,888 bytes left at the end of its
owned mutable region. No new RAM range is granted. The native allocator bundle
can be rebuilt on Linux using `project/rtems/residentnet/test_general_heap.py
--rtems shared-allocator-sources --out /tmp/shared-native --shared --iterations
100000` from the extracted archive. The synthetic native counter is not a
hardware timing measurement.

## Restored production service

The final reboot returned as `639e51d4-bb32-4fd7-8364-f9b3cc4a157f`.
The `i960-http6` service is active and the Mac fetched HTTP 200 from
`http://[2a02:8106:40:9000:f662:19ee:dbad:1f1e]:8080/`, including the Vader ASCII
and RTEMS page. `shared-heap-production.tar.xz` contains the unchanged cooperative
image/module, launcher and frozen startup/publication metadata. It deliberately
excludes active packet traces and visitor records; the service is left running
and its persistent visitor log remains on the host. This snapshot does not
claim a completed/closed production session.

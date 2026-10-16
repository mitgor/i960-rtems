> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# RTEMS general-heap batch — 2026-10-11

This batch turns the unused tail of the already validated cache-data range into
a general application heap and tests corruption containment while retaining
resident networking. No flash writes, additional RAM ranges, or changes to the
cooperative production image are involved.

Contract and reproduction: [GENERAL-HEAP.md](../../rtems/residentnet/GENERAL-HEAP.md).
Archives contain exact ELF/COFF, binary, map/symbol/build metadata, Linux module,
source snapshots and raw card captures. Unpack each into its own directory and
symlink `residentnet` to `scsi-drain/residentnet` before running the verifier.
Root `artifacts/SHA256SUMS` and `artifact-inventory.json` cover the archived bytes.

## Physical containment evidence

| Archive | Corruption | Error | Allocations / frees | Retained bytes | Worker operations |
| --- | --- | ---: | ---: | ---: | ---: |
| `general-heap-guard.tar.xz` | Outer queue/heap guard | 1 | 136 / 134 | 3,986 | 50 + 50 |
| `general-heap-redzone.tar.xz` | Allocation suffix | 3 | 136 / 134 | 3,986 | 50 + 50 |
| `general-heap-metadata.tar.xz` | Physical block extent | 2 | 136 / 134 | 3,986 | 50 + 50 |
| `general-heap-offset.tar.xz` | Saved alignment offset (hardened) | 2 | 200 / 198 | 3,986 | 50 + 50 |

All four records were read twice without change, accepted terminal STOP, rejected
firmware callbacks, and retained the module/DMA resources at close. They are
software-detected corruptions entering the terminal handler, not new hardware
fault or NMI tests. Reset and exception ownership remained valid. Each boot
repeated four RAM patterns / 262,144 checked words before granting the heap.
The first image also passed a restoring/unloading bounded smoke test.

`evidence/*-replay.json` binds captures to the exact payload/module and original
ROM. `guard-layout.json` checks linked storage against the existing upload
bounds. `native-tests.txt` contains the complete offline regression run.
`heap-snapshot-tests.txt` checks active/parked heap telemetry rejection paths.
The first archive includes the original 32-bit Linux allocator harness and the
three unmodified RTEMS allocator implementation files; expanded native coverage is
recorded with the metadata-injection image. The offset archive contains final
32-bit native coverage: 96 single-bit corruption cases and a null free-list link.
Its additional 64 startup allocations exercise the slot limit on the card.

## Thirty-step implementation and validation ledger

1. Recovered the prior RAM grant and verified the live card owner before testing.
2. Inspected RTEMS 4.6.6 heap implementation and contiguous-extension restriction.
3. Chose a separate application heap, preserving the RTEMS kernel workspace.
4. Calculated the 69,952-byte range without moving the external packet queue.
5. Preserved the queue-end and region-end guards around the heap.
6. Added opt-in build dependencies and separate injection selectors.
7. Integrated the actual RTEMS allocator and libc allocation entry points.
8. Added exact-pointer registration and a 64-live-allocation bound.
9. Added prefix/suffix allocation guards and checked address arithmetic.
10. Added bounded physical-block/free-list validation, then bound used blocks and saved alignment offsets to the registry.
11. Serialized allocation with saved/restored interrupt priority; refused ISR use.
12. Implemented calloc overflow/zeroing and realloc preservation semantics.
13. Tested initialization, exhaustion, alternating free and large-block coalescing.
14. Added two worker allocation streams retaining data across real preemption.
15. Added explicit worker drain and final allocation/free accounting.
16. Added terminal heap diagnostics without freeing uncertain allocations.
17. Built a 32-bit Linux harness from the actual pinned allocator sources.
18. Tested simulated workers, ISR rejection, 32 redzone, 32 offset and 32 pointer mutations.
19. Tested slot exhaustion, alignment, realloc shrink/zero and OOM preservation.
20. Cross-built and checked physical image boundaries and restoring bounded entry.
21. Injected outer-guard corruption on the card and replayed retained resources.
22. Rebooted, injected allocation-suffix corruption and replayed retained resources.
23. Injected allocator block-extent and saved-offset corruption and replayed retained resources.
24. Extended normal RNT6 heap/queue telemetry and corruption rejection tests.
25. Built non-injection images before/after offset hardening and repeated bounded bring-up.
26. Ran concurrent IPv4/IPv6 UDP, TCP and HTTP with continuous heap operations.
27. Saturated the 128-slot queue and deliberately lost TCP packets.
28. Checked autonomous deadline, both task IRQ drains and empty application heap.
29. Archived/replayed raw evidence, rebooted and restored public IPv6 HTTP.
30. Updated findings, Claude guidance and story; collected artifacts and hashes in git.

The measured results below are the acceptance record for the completed
implementation and validation steps.

## Networking evidence

`general-heap-network.tar.xz` is the first, pre-offset-hardening image. It passed
36,000 ticks and ten 30-second-spaced concurrent IPv4/IPv6 rounds: UDP,
4,096-byte TCP echo and HTTP, with intentional TCP data loss. All 36,036
allocations were freed before the final parked snapshots; both IRQ contexts
drained. The 160-request burst returned 129 replies, filled all 128 queue slots
and counted 31 drops. Raw replay validated 684 ingress and 384 egress bulk
transactions; observed transaction latency was 1.92–427.60 ms (mean 67.11 ms).
This latency includes the host/MMIO transport; it is not allocator latency.

Audit of `_Heap_Free` then found a saved alignment offset before the raw buffer.
The final implementation also validates that word and matches each used block
to the trusted allocation registry before entering RTEMS. The earlier images
are preserved as development evidence, not interchangeable release binaries.


`general-heap-hardened-network.tar.xz` is the final non-injection image. It passed
36,000 ticks and all ten rounds. Every one of its **36,100 allocations was freed**
at the autonomous deadline; both task IRQ contexts drained. Ownership was 31,
with no heap/outer-guard errors. Saturation again gave 129 replies / 31 drops and
queue peak 128. Replay checked 709 ingress and 399 egress bulk transactions,
full TCP byte streams, and 24 deliberately corrupted snapshots. Observed bulk
latency was 2.22–452.57 ms, mean 72.10 ms; no allocator-latency claim is inferred.
The final native harness also tests allocation with an empty free list.

The two traffic tests are separate six-minute sessions, not a twelve-minute
continuous service qualification. Three bounded smoke runs restored RAM and
unloaded normally; all six resident/terminal runs retained resources until reboot.
No forced unload or flash programming occurred.

Example final replay from the repository root:

```sh
mkdir -p /tmp/heap-replay
tar -xJf artifacts/rtems-general-heap-20261011/general-heap-hardened-network.tar.xz -C /tmp/heap-replay
ln -s scsi-drain/residentnet /tmp/heap-replay/residentnet
python3 rtems/residentnet/verify.py --root /tmp/heap-replay /tmp/heap-replay/general-heap-hardened-network
python3 rtems/residentnet/verify_bounded.py --root /tmp/heap-replay /tmp/heap-replay/general-heap-hardened-bounded
python3 rtems/residentnet/ram_audit.py /tmp/heap-replay/residentnet
```

## Remaining work

Measure worst-case masked-interrupt allocator latency and consider bounded work
or alternative locking; define task/shared-allocation ownership and cancellation
before reclaiming another task's buffers; qualify kernel-workspace growth
separately; run substantially longer resident networking endurance. The rest of
the 16 MiB RAM, graceful SCSI drain and direct NIC DMA remain outside this grant.


## Final host state

All six required reboots returned over SSH without physical intervention. Final
boot: `23b38c34-f329-496a-9f41-c462f825e766`. The original cooperative `autonet`
image and its pinned module were restored as `i960-http6`, using the existing
persistent visitor log. A Mac request to
[public IPv6 HTTP](http://[2a02:8106:40:9000:f662:19ee:dbad:1f1e]:8080/)
returned HTTP 200 and the Darth Vader page. Headers/body are saved under
`evidence/`; `general-heap-production.tar.xz` contains the production image,
module, launcher, boot/service identity and frozen open/preflight/request data.
The ongoing production packet/trace streams were not archived while being written.

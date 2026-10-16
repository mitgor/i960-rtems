> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# RAM ownership and resident networking batch — 2026-10-11

See [implementation and memory map](../../rtems/residentnet/RAM-OWNERSHIP.md).
The wider physical RAM grant remains closed. This batch expands usable packet
storage within the existing upload allocation, identifies firmware cache
geometry, and traces SCSI software bookkeeping without claiming hardware drain.

## Verified resident result

One ARM callback, then independent message-register control and networking:
60,000 timer ticks, six rounds with IPv4/IPv6 clients running concurrently,
60 maximum/varied-size UDP exchanges, twelve 4,096-byte TCP echoes and twelve
HTTP responses. One TCP data packet per family was intentionally withheld.
All 711 raw IP packets pass checksum/stream replay; 40 repeated TCP segments
are consistent with retransmission. Bulk packet ioctl latency was 1.43–241.60 ms
(mean 43.05 ms). This is functional PIO networking, not a throughput claim.

The separate initial saturation burst sent 96 UDP requests without reading TX:
65 exact replies, 31 counted drops, high-water 64. Six later traffic rounds
completed with no additional counted drops. Traffic finished around 54 seconds;
autonomous tasks/timers then continued to the deadline. This is a ten-minute
runtime soak, not ten minutes of continuous network load. At the deadline both
interrupt continuations drained, guards passed, and resources stayed retained
until reboot. The host observed parked state at 615.7 seconds; snapshot capture
itself grows slower as its JSON history grows.

- `residentnet-ram-resident.tar.xz` pins the gated target, generated module,
  bounded admission run, resident run, boot/PCI inventory and source snapshot.
- `evidence/resident-replay.json` independently verifies exact image/module
  hashes, one callback, raw traffic, burst contents and retained-close state.
- `evidence/bounded-gated.json` verifies the matching 100-tick bring-up.
- `evidence/ram-gated.json` checks the final resident link map.

## Evidence

- `residentnet-ram-probe.tar.xz`: initial 64-slot image/module, 14 read-only
  diagnostic pages, bounded 100-tick phase-2 test, complete close restoration.
- `evidence/resident-tested-cache_probe.h`: exact 14-page target header used
  for the resident soak; final source adds only fixed page 15 to that probe.
- `evidence/prior-replay.json`: older 32-slot / old snapshot format still replays.
- `evidence/allocation-mutations.json`: six damaged metadata fields rejected.
- `evidence/native-tests.txt`: complete offline `make -C rtems test` output,
  including ASan/UBSan queue and board checks.
- `evidence/allocations/`: 73,608 byte-checked disassembly rows underpin the
  selected excerpts; live allocator arithmetic is independently checked.
- `evidence/ram-probe.json`: complete linked-object interval check; 64 slots,
  98,304 queue bytes, 12,000 bytes unused mutable tail, no broader RAM grant.

Hardware run starts on boot `b73cb338-eb5f-4cd0-8367-ea65e2f799a9`.
The final resident image adds the board admission gate. A subsequent diagnostic
image only adds fixed page 15 for SCSI software counters; its bounded test is
separate from the resident network soak. Archives pin each image and module.
No flash programming, SCSI command, SCSI reset, destructive sizing test or
external cache command is part of this batch.

## Recovery and final diagnostic

The ordinary forced systemd reboot returned without physical intervention on
boot `c14e74cb-650d-492e-90e9-7124831db9f3`. The first postboot probe invocation
failed before accessing the card because the generated module had not yet been
compiled; its error log is preserved. After compiling it, the final 15-page
probe passed 100 phase-2 ticks, 17 callbacks, full restoration and module unload.
Page 15 read drive queue 0, I/O-descriptor queue 0, scheduler queue **4**, and
SCSI I/O count 0. This is software bookkeeping, not hardware drain evidence.

`residentnet-ram-scsi.tar.xz` includes this final image under
`ram-scsi/residentnet/`, the generated/built module, build logs, all 15 pages and
the preserved preflight failure. For `verify_bounded.py`, make a `residentnet`
symlink to `ram-scsi/residentnet` in the extracted archive root.
`evidence/bounded-scsi.json` and the updated allocation audit replay it.

`residentnet-ram-production.tar.xz` preserves the old service's normal close,
new service identity/open/preflight, pinned production binary/module and active
service status. The production service remains cooperative autonet, with its
existing visitor log. Public IPv6 HTTP returned 200 and the Darth Vader page
from the Mac after restoration; headers/body are in `evidence/`. This verifies
that path from this host, not reachability from every external network.

## Thirty-step ledger

These are investigation, implementation and validation steps, not thirty
reboots or thirty independent hardware trials.

1. Check SSH, boot identity and active production ownership.
2. Stop the cooperative web service with normal restoration.
3. Trace the firmware staging-buffer helper.
4. Trace its cache reservation arithmetic and failure path.
5. Locate cache line-size metadata.
6. Locate cache data and descriptor geometry.
7. Add fixed read-only allocation pages 8–14.
8. Cross-build the diagnostic target and matching module.
9. Run bounded phase-2 admission and 100 timer ticks.
10. Capture 14 pages and verify full restoration/unload.
11. Archive the first build before replacing it.
12. Reconcile the live 16 MiB report with 1,876 cache lines.
13. Identify the adjacent 240 KiB as firmware cache data.
14. Preserve the external-RAM rejection policy.
15. Expand resident queue storage to 64 slots inside the grant.
16. Audit all linked writable objects, guards and queue extent.
17. Add board/dispatch/staging admission checks.
18. Reject 224 single-bit identity mutations in native C tests.
19. Test actual queue full, wrap, backpressure, drain and oversize paths.
20. Add versioned queue-drop and high-water telemetry.
21. Implement a 96-datagram TX-withheld saturation test.
22. Add concurrent IPv4/IPv6 client rounds.
23. Cross-build the gated image and repeat bounded bring-up.
24. Run six dual-stack rounds, TCP loss and a 60,000-tick resident deadline.
25. Replay raw packet ioctls, queue telemetry and retained-close evidence.
26. Trace named SCSI counters and increment/decrement/busy call sites.
27. Add and test fixed read-only SCSI diagnostic page 15 after reboot.
28. Preserve exact builds/captures, then restore and check public HTTP.
29. Update findings, Claude instructions and the narrative with limitations.
30. Audit tracked artifact hashes and commit the batch.

## Remaining work

Identify the actual SCSI channel hardware and prove a bounded stop/drain
sequence before expanding physical RAM ownership. Enumerate all low-RAM
monitor and interrupt dependencies before relocating any of them. Then a
separate exclusive-only linker layout can be proposed with guards and a
non-aliasing test inside a legitimately transferred range. Resident networking
still uses host-relayed PIO, and this bounded soak is not an always-on service.
Production remains cooperative `autonet`.

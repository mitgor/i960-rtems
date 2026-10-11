# Exclusive fault/NMI ownership and fixed-range RAM — 2026-10-11

Physical exception tests and final RAM-backed resident networking passed.
The 30-step ledger below records the implemented investigation and acceptance.

## Captures preserved

Each `.tar.xz` contains the exact COFF image, flat binary, link map, symbols,
disassembly, image-pinned Linux module, generated source, build logs, target
source snapshot and raw session evidence. No rebuilt binary substitutes for a
captured one. Local replay reads the pinned files and raw transactions rather
than trusting a success summary.

- `fault-owner-real.tar.xz`: initial 100-tick bounded probe and real `faulte`
  containment. Original ordering installed exception ownership after reset.
- `fault-owner-synthetic.tar.xz`: revised install-before-reset ordering and
  synthetic local entry (kind 3). This is not evidence of hardware NMI delivery.
- `fault-owner-ram.tar.xz`: fixed 256 KiB destructive RAM probe, initial queue
  migration, then a real constraint fault with the RAM report preserved.
- `fault-owner-nmi.tar.xz`: repeated fixed-range probe followed by an external
  PCI doorbell NMI. Captured kind 2, hardware vector 248, doorbell `80000000`,
  IIMR `1f3` and IISR bit 3. New handler masks/clears that source and remains
  terminal with diagnostics. Both fixed-range tests checked 262,144 words.
- `fault-owner-net.tar.xz`: final guarded 128-slot build, 100-tick bounded
  bring-up (33 callbacks, restored/unloaded), then 24,000 ticks and six spaced
  concurrent IPv4/IPv6 rounds. Burst: 160 requests, 129 unique echoes, 31
  counted drops. Deliberate IPv4/IPv6 TCP loss recovered; both IRQ contexts
  drained at the deadline. Normal module has no NMI-test ioctl.
- `evidence/`: independent replays, native tests and linked RAM audit. The full
  native RTEMS suite passed. Final queue-pointer/guard changes passed targeted native tests and the
  final card run. Historical 72-slot captures still replay successfully.

All three terminal modes keep SCSI reset asserted, hold the Linux module and
allocation, and reject another firmware callback. Nothing resumes stock
firmware after takeover. All five exclusive-session host reboots returned
without physical intervention; capture boot IDs distinguish sessions.

## Thirty-step ledger

1. Read prior SCSI/RAM evidence and verify current host owner.
2. Resolve the pinned ROM PRCB and fault-table location.
3. Check Intel's local-call fault entries and hardware record layout.
4. Check NMI priority, cached vector and interrupt-stack behavior.
5. Implement guarded exception storage and non-returning assembly entry.
6. Implement whole fault-table installation and readback.
7. Add terminal snapshot/read/STOP diagnostics with resource retention.
8. Test 2,048 table-corruption bits and 64 failed writes natively.
9. Build an opt-in image; leave cooperative/default profiles intact.
10. Run bounded bring-up and verify exact restoration/unload.
11. Raise a real constraint fault on the card.
12. Replay its instruction address, frame, state and pinned image/module.
13. Archive and reboot before another experiment.
14. Move ownership installation before secondary reset.
15. Exercise synthetic NMI plumbing, distinctly labeled.
16. Audit surviving stack/table/interrupt and DMA dependencies.
17. Implement a fixed-range four-pattern RAM experiment.
18. Test 16 aliased address bits, 32 corrupt data bits and boundary failure.
19. Implement/test lossless queue migration for every occupancy 0–68.
20. Probe 256 KiB on the card with caches controlled and boundaries checked.
21. Raise another real fault and preserve the RAM report.
22. Find the documented external PCI doorbell NMI mechanism.
23. Implement an image-pinned, one-shot host trigger and admission tests.
24. Generate a real NMI and verify vector 248 plus its hardware source.
25. Archive/replay NMI containment and reboot.
26. Add queue-pointer validation and an immediate external-queue guard.
27. Run final bounded bring-up and sustained 128-slot IPv4/IPv6 networking.
28. Replay packet streams, saturation, loss recovery and terminal deadline.
29. Reboot, restore public cooperative HTTP and update findings/story/guidance.
30. Collect source/binaries/captures, verify Git hashes and commit.

## Scope

The grant is only the packet queue at `c0200040`, 192,000 bytes, inside a tested
256 KiB region. The rest remains reserved; the original internal queue is also
retained. This is not a general RTEMS heap extension, proof of all 16 MiB, or
returnable firmware coexistence. Fault/NMI containment is terminal. Corrupted
stacks and recurrent faults before safe handler entry remain limits. Other
hardware NMI sources and prolonged service still need further tests.

## Production restored

Final boot: `39332cc7-b410-4d68-927c-d0398d95316a`. The cooperative `i960-http6`
service is active, using the existing visitor log. The Mac received HTTP 200
and the 2,890-byte Vader/status page from the published IPv6 endpoint.
`fault-owner-production.tar.xz` preserves its image/module, startup/preflight
and publication metadata; the mutable live stream was not archived while being
written. Response headers/body are in `evidence/http-restored.*`.

## Remaining work

Extend this measured fixed queue grant into a separately tested RTEMS allocator
only after defining allocation/free/ownership contracts. Test live guard-failure
containment, additional hardware NMI sources and longer traffic soaks. Terminal
exception handling does not resume tasks; damaged hardware-delivery stacks and
recurrent faults before diagnostic entry remain limits. Cooperative firmware
coexistence remains the separate preserved path, not an exit from this takeover.

# Relocated code/data/BSS proof — 2026-10-12

**Physical acceptance passed on the first card attempt.** This is the small
reviewed probe, not the Doom engine. [Contract and implementation](../../game/doom/runtime/relocate/README.md).

## Exact build and execution

- Target SHA-256: `834f6483001fa6fc6c87cab220cc1a989696b1b8fdbdfabd64f5ad176b52ddf1`.
- Zero-base template SHA-256: `5baa46a0e96de9c405071fff22439efc8c66d1136987a59be186ee3c5f4cd0a0`.
- 176 bytes of code, eight bytes of initialized data, 128 bytes of BSS;
  184 file bytes / 320-byte allocation span. Six internal `R_960_32` sites.
- Actual image base `0xc02d0050`, entry `0xc02d0080`. The address comes from the
  allocated image, not a fixed-address assumption. Both physical calls used
  the same retained image handle 1537. Two different addresses are covered by
  native tests, not by two physical allocations at different addresses.
- Both real i960 calls returned **1228486293** (`(5 * 33) ^ 0x49393630`). Each
  allocated and freed 512 bytes through the existing runtime table. The loader
  verified initially zero BSS, all 32 computed counters, unchanged initialized
  code/data and the relocated pointer into BSS; it restored the template/zero
  BSS and synchronized caches before allowing the next call.
- Observed command times were **18.934 ms and 6.486 ms**. These include host
  transport/scheduling under audits; they are not isolated CPU execution times
  or a throughput benchmark.
- Eight command-13 refusals: no image, four incomplete images, changed entry,
  changed code and changed initialized data. Corrupt files had correct ordinary
  CRCs, so these exercise the exact whitelist independently of CRC acceptance.
  Deliberately nonzero BSS refusal is native-tested only.

## Audits and regressions

All existing full paired snapshots, protected-code checks, allocation guards,
CRC preparation and task/IRQ drain checks stayed enabled. No flash write, wider
memory claim, forced module unload or second firmware callback was used.

- Six dual-stack network rounds, burst saturation, deliberate packet loss,
  **776 independently replayed packets**, 14 retransmitted segments.
- **593 recorded upload commands** (592 sequence numbers plus the deliberate
  replay), **1,511 upload ioctls**, complete actual-C native replay with sanitizers.
- The existing WAD probe also passed normal/CRC/short/error/timeout/recovery:
  ten requests, nine replies, 500-tick deadline unchanged, zero final loans.
- STOP at **tick 14,903** drained both worker/IRQ owners and reclaimed the
  remaining partial image and retained allocations. Parked state/handle zero;
  cancellation count eight. Maximum observed IRQ gap **10.480 ms**.
- **24 snapshot mutations, eight WAD mutations and seven relocation evidence
  mutations rejected**. Native tests also cover repeated entries at two allocator
  addresses, wrong entry/code/data/BSS and loading-state refusals.
- Three independent links at `0x10000`, `0x200000`, `0xc02d0050` still match the
  offline relocation implementation byte for byte; ten malformed-object checks
  pass. The complete RTEMS offline suite passed.
- Upper protected code is **22,784 bytes**; BSS ends at `c0f8b940`, with 34,496
  bytes before protected upper code. Existing boundaries are unchanged.

### A verifier issue, with the original evidence preserved

The first independent network replay rejected a TCP “gap”. Inspection found
that Linux reused host port 38592 for a second connection to card port 9600.
Both handshakes and both previous FIN directions are present; the old verifier
merged the two different initial sequence numbers under one four-tuple.

The verifier now assigns a separate connection only after a fresh SYN with a
new identity and captured closure/reset of the old one. SYN-ACK must acknowledge
that SYN. It still rejects gaps within a connection, conflicting retransmission
bytes and unequal echo contents. Regression tests cover reuse, exact duplicates
and five invalid cases. The unchanged capture and the previous runtime-entry
capture both pass. `replay-before-flow-fix.log` preserves the initial rejection.
This is a host-verifier correction; no target, module or physical capture was
changed after the card run.

## Evidence and reproduction

`accepted-evidence.tar.gz` contains the exact physically tested project snapshot,
target ELF/binary/map/symbols, generated whitelist and linker-oracle binaries,
kernel module source/binary, build logs, RAM audit, raw paired snapshots and all
network/upload/WAD/STOP journals. Archive SHA-256:
`eff2d3a17cb2f444481bd2094625a52d7b95c60a7506f700ff432c21c3b45485`.
`verification-update.tar.gz` overlays the later verifier fix/test sources; extract
it after the acceptance archive for self-contained replay. Separate files here
hold replay, sanitizer/offline logs, tamper results and service restoration.

Remote workspace: `/home/mit/i960-relocate-20261012`. Build flags:

```
--profile residentnet --secondary-reset --fault-owner --extra-ram
--general-heap --heap-shared --queue-reclaim --owned-mib 12
--resident-upload --doom-heap --doom-shared --doom-runtime
```

Live flags omit `--profile` and add `--upload-concurrent --ticks 24000 --rounds 6
--round-interval 2 --burst --parallel --drop-data --wad WAD`. The unchanged
Freedoom 0.13.0 IWAD is already tracked in `artifacts/doom-m1-20261011/`:
28,795,076 bytes, SHA-256
`7323bcc168c5a45ff10749b339960e98314740a734c30d4b9f3337001f9e703d`.
It is not duplicated in this archive.

After extracting both archives into ROOT, run from ROOT/project:

```
python3 rtems/residentnet/verify.py --root ROOT ROOT/live
python3 rtems/residentnet/verify_upload.py ROOT/live --doom-heap --doom-shared --doom-runtime --wad WAD --output replay.json
python3 rtems/residentnet/test_relocate.py --entry ROOT/residentnet/entry
python3 rtems/residentnet/test_relocate_evidence.py ROOT/live --build ROOT/residentnet/entry/relocate --output relocation-tamper.json
python3 rtems/residentnet/test_runtime_evidence.py ROOT/live --wad WAD --output runtime-tamper.json
python3 rtems/transport/test_validate_packets.py
```

Use absolute ROOT and WAD paths. Native replay models the short i960 arithmetic
while running the actual allocator/runtime/loader; it does not emulate the ISA.
The physical capture establishes real i960 execution.

## Remaining work

The engine still has **44 unresolved imports** and has not run on the card.
Next: libc/platform imports, target WAD-cache integration and an updated complete
image/runtime/zone/cache/allocator/stack budget, then bounded engine startup.
This proof restores application data after every return; a persistent engine
needs its own admitted lifetime and STOP/drain contract. Idle IRQ ownership and
firmware recovery remain outside this acceptance.

## Public service

After the required exclusive-release reboot, boot ID is
`bc5b1fb0-33ef-41c0-a721-14ff1003be01`. The original cooperative IPv6 service was
restarted as PID **3808** with its original payload/module and visitor log.
The Mac independently received **HTTP 200** from the public IPv6 URL.
See `production-restore.json`, `service-status.txt` and the HTTP check files. Visitor
statistics remain on the host and are not copied into Git.

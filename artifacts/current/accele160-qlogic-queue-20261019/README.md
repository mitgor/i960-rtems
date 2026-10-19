# Accele160 QLogic queue-state snapshot, 2026-10-19

[Profile 16](../../../rtems/accele160/ownership/PROFILE16.md) adds only fixed
firmware RAM reads to the profile-14 inventory. It verifies the exact context
pointer and never traverses pending lists or ring pointers. Its scope excludes
new PCI transactions, chip MMIO, queue mutation and memory reclamation.

- `build.txt`, `native-tests.txt`, `entry-object-check.txt`: source/build and
  whitelist/refusal/decoder/exception-entry checks.
- `firmware-audit.json`, `firmware-tests.txt`, `accounting-dependencies.dis`:
  pinned context/ring dependencies and accounting semantics.
- `previous-final.tar.xz` and check: prior normal service's clean STOP.
- `tested-live.tar.xz`: complete build bundle, binaries/modules/firmware,
  paired flash reads, Doom frames/WAD service, owned snapshots and console test.
- `tested-final.tar.xz`: STOP snapshot, QUIE/ACK and retained callback/pins.
- `restored-live.tar.xz`, replay, prompt/services and `recovery.json`: normal
  profile-5 service restored on a fresh boot with firmware checks.

Replay from the repository root:

```sh
bash rtems/accele160/fault/test.sh
python3 rtems/accele160/ownership/verify_inventory.py artifacts/current/accele160-qlogic-queue-20261019/tested-live.tar.xz
python3 rtems/accele160/ownership/verify_stop.py artifacts/current/accele160-qlogic-queue-20261019/tested-live.tar.xz artifacts/current/accele160-qlogic-queue-20261019/tested-final.tar.xz
python3 rtems/accele160/fault/verify_runtime.py --live artifacts/current/accele160-qlogic-queue-20261019/restored-live.tar.xz
```

Equal software indices do not establish chip DMA drain or permanent exclusion.
The three packed accounting words have different/partially unresolved meanings.
No engine is disabled and no additional RAM is granted by this profile.

The initial decoder's 128/64-entry hypothesis was disproved by the physical
context (256/128). The immutable test bundle preserves that decoder and kernel.
`analysis-qlogic_queue.py` is the corrected offline decoder; replay reports both
source hashes. `corrected-ready-analysis.json` validates the initial raw capture
with the corrected capacities. No card probe or binary changed for this fix.

## Result and final running service

Test session `20261019T101018Z` passed 64 frames, 5045 WAD reads and
709 external exchanges with no errors. All four snapshots match
(`observations.json`): capacities 256/128, pending head/tail zero, request
indices 37/0, response indices 22/22, accounting words 0/0/578. The corrected
layout and pointer/index bounds pass. This grants no RAM or hardware ownership.

Clean STOP retained the callback and pins. Recovery used a fresh boot,
`9086e6f3-5eb2-424e-a210-d4dee54608dd`, and two full matching firmware reads. The normal
profile-5 session `20261019T101634Z` completed 64 frames, 5045 WAD reads
and 709 external exchanges. Prompt and gateway are restored; the owner is
left running at verified idle. The normal kernel remains the accepted immutable
`55dc845a43b53fe0e84aba8ed180f28e0331999b74857c96d5e8ff2bb2d5d002`.

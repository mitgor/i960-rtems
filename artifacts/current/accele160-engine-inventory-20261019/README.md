# Accele160 P3j: core-engine inventory and firmware SCSI dependencies

The opt-in profile 14 passed on boot `4b6636cc-ec67-49ad-b90e-45f1c71d858e`,
session `20261019T074605Z`. Kernel SHA-256:
`0dfb8e25d5d6e4b4ad13e871b985d385b4a7d7b88e8a1767ea1ef11553f68adf`.
It completed 64 frames, 5045 WAD reads and 709 external console exchanges,
then clean STOP with retained callback/pins. Three live and one final snapshots
show the persistent DMA1 descriptor, enabled arbiters, quiet AAU words/queues,
and channel-0 QLogic `1077:1016` metadata at register mapping `8bf00000`.

[Protocol, address map, dependencies and limits](../../../rtems/accele160/ownership/PROFILE14.md).

- `tested-live.tar.xz`: exact kernel/image, manifest, sources, modules, engine,
  firmware input, raw snapshots, guarded DMA frames and console evidence.
- `tested-replay.json`: full runtime, frame/WAD/console replay, decoded inventory
  and pinned firmware dependency audit. It intentionally precedes global STOP.
- `tested-final.tar.xz`, `stop-replay.json`: clean STOP, phase-1 report, guards,
  QUIE/ACK and retained resources; tied to the live archive hash.
- `previous-final.tar.xz`, `previous-final-check.json`: prior normal session's
  shutdown, with its complete live acceptance already in the previous batch.
- `build.txt`, `native-tests.txt`, `native-linux.txt`, `decoder-tests.txt`:
  cross build, actual C whitelist/boundary test, owned-runtime simulation,
  identity/sequence rejection and C/Python ordering check.
- `firmware-layout.json`, `firmware-audit.json`, `firmware-dependencies.dis`:
  pinned decompression and machine-code anchors for stock DMA1/AAU submission,
  QLogic setup/callbacks and alternate Symbios/configuration paths.

```sh
python3 rtems/accele160/ownership/verify_inventory.py artifacts/current/accele160-engine-inventory-20261019/tested-live.tar.xz
python3 rtems/accele160/ownership/verify_stop.py artifacts/current/accele160-engine-inventory-20261019/tested-live.tar.xz artifacts/current/accele160-engine-inventory-20261019/tested-final.tar.xz
```

The inventory adds 48 fixed reads, no engine control writes. It reads firmware
metadata, not live SCSI PCI configuration. The added inventory reads no CSR/ASR or unknown chip register. This batch
performs no flash write, reclaim or SCSI reset. The ordinary runtime
still performs its established DMA, timer and vector operations. Quiet words
and successful normal operation do not prove permanent exclusion.


`first-live.tar.xz`, `first-final.tar.xz`, `first-replay.json`,
`first-stop-replay.json` and `first-build.txt` preserve the first run before
fixing a source-level assembly profile guard. The older cloned wrapper already
omitted that diagnostic code; the kernel bytes are identical in the repeat.
`entry-object-check.txt` verifies equality with the accepted profile-5 object,
including an explicit profile-14 compiler invocation. See the design note for
the exact limitation and correction; neither run injected a fault/NMI.

The captured build wrapper differs from the current repository wrapper only in
passing the terminal profile to assembly (`build-wrapper-diff.txt`). The
explicit profile-14 object check closes that difference without changing the
kernel bytes. The FreeBSD ISP PCI source's `1077:1016` definition is linked in
the design note; no chip-register sequence was borrowed or executed from it.

## Recovery and preserved prompt

The final reset returned without physical intervention. Both complete firmware
reads matched the expected programmed image. `recovery.json` links the repeat
boot to normal profile 5, session `20261019T075249Z`, boot `49c4d3c5-df8d-438f-810a-82a343636e52`.
The immutable bundle remains `/home/mit/i960-owned-runtime-20261018/bundle`,
normal kernel `55dc845a43b53fe0e84aba8ed180f28e0331999b74857c96d5e8ff2bb2d5d002`.

Normal acceptance passed 64 frames, 5045 WAD reads and
717 external console exchanges with zero errors. `restored-live.tar.xz`
and `restored-replay.json` contain and verify that run. Prompt is at verified
idle with no zone loan; gateway 8088 returns HTTP 200 (`restored-prompt.txt`,
`restored-services.txt`). All profile switches used clean STOP and reboot;
no retained allocation was adopted or freed by a second owner.

```sh
python3 rtems/accele160/fault/verify_runtime.py --live artifacts/current/accele160-engine-inventory-20261019/restored-live.tar.xz
```

# Accele160 P3b candidate and prior-session shutdown evidence

Status: **both actual hardware exception tests and both reset-recovery gates
passed; normal prompt restored and left live**. Final recovery boot:
`aea81f51-24ce-493b-a7d2-114195611d5b`. Both guarded full firmware reads
match. The accepted mode-0 normal image completed 64 Doom frames, verified idle
and 577 external console exchanges without connection errors. `~/rtems-console`
now answers `apps`, `mem` and `stats`; Mac `./rtems-console` uses the same client.

The normal session is `/home/mit/i960-fault-20261018/sessions/20261018T204122Z`.
Do not reset this working prompt just to finish bookkeeping. Its own global
STOP/post-reset is not claimed. It is the prior software-terminal-only image;
normal runtime with new owned vectors/ISP remains a separate qualification.

- `mode0-restored-live.tar.xz`: exact normal bundle, full live session snapshot
  and `restored-console.json` with all 577 external exchanges. It preserves all
  64 guarded DMA frames, paired PIO receipts, WAD requests and console wire log.
- `verify_restored.py`, `restored-replay.json`: independent manifest/firmware,
  frame/guard/FNV, WAD, idle and console replay. The new boot and firmware pair
  close mode 4 recovery, superseding the pending state in mode4-replay.json.
- `restored-prompt.txt`: installed shortcut replies (`run=1`, `idle=1`,
  `frames=64`, `zone_loaned=0`) and active service status.

Mode 3: fresh boot `b748d05a-16d1-40bf-b96d-973127ab6856`, actual `faulte`
at tick 18, IP `c0716230` = `_accele_raise_fault+4`, fault entry `c0716150`,
NMI entry `c0716160`, ISP `c0779040`. Mode 4: boot
`5caaf490-19ac-4b1b-ab1c-c01cacc9c924`, actual MU-doorbell NMI at tick 18,
raw hardware record `2002,9002,f8,0` (vector 248), fault entry `c0716270`,
NMI entry `c0716280`, ISP `c0779040`. NISR/IISR/IDR/IIMR: `100,f,80000010,73`.
Both verified all table entries and guards, stable raw records after STOP,
pending admission, and intact retained DMA pins. Neither injected active DMA.

Mode 4's paired guarded full firmware reads close mode 3's reset gate.
The prior normal-runtime recovery was closed by mode 3's prechecks. The final
mode-0 restoration closes mode 4 recovery. No normal owned-ISP runtime claim is
made. The restored bundle is `/home/mit/i960-fault-20261018/bundle`; the exceptions
bundle still contains deliberate NMI mode 4 and must not be used for the prompt. See
[`OWNED-EXCEPTIONS.md`](../../../rtems/accele160/fault/OWNED-EXCEPTIONS.md).

- `mode4-tested.tar.xz`: exact executed mode-4 bundle and complete
  `sessions/20261018T203301Z`, including paired firmware prechecks and raw
  READY/stale/armed/terminal/stable/after-STOP captures.
- `mode4-replay.json`: independent archive replay, including vector 248 and
  NMI source evidence, symbols, kernel/image/source hashes and firmware pair.
- `mode3-recovery.json`: links mode 4's fresh prechecks to completed fault-test
  recovery. It supersedes the earlier pending reset state in mode3-replay.json.
- `console-deployment.txt`: installed Linux client/shortcut hashes, verified
  missing-socket message, and the accepted normal image's identity/build mode.
  The Mac shortcut now calls the installed Linux shortcut. This receipt preceded the now-restored service.

- `mode3-tested.tar.xz`: exact executed current mode-3 bundle and complete
  `sessions/20261018T202453Z`, including both guarded firmware reads and raw
  READY/stale/terminal/stable/after-STOP snapshots.
- `mode3-replay.json`: independent `verify_archive.py` output. Checks exact
  symbols/fault IP, table/ISP/guards, kernel/image/source hashes, firmware pair
  and retained admission/pins. Raw record: `2002,9002,50001,c0716230`.
- `previous-normal-recovery.json`: links the fresh paired reads to the prior
  normal runtime's reset gate. Supersedes the earlier pending recovery receipt.
- `mode4-prepared.tar.xz` and `mode4-prepared-identity.json`: exact next NMI
  test bundle, archived before execution; mode4-tested contains the actual run. Kernel
  `dbb43a389db7d6cd101284c8759e9ce2e6a37046ff83388171aed32fadad9ed4`.

- `previous-normal-final.tar.xz`: complete prior normal session
  `sessions/20261018T195841Z`, collected after clean global STOP. Raw
  `run/persist/quiescent-page.bin` contains QUIE/ACK, 128 drained frames and
  no remaining DMA sources. Admission remains pending; pin guards unchanged.
- `previous-normal-stop-replay.json`: independent checks of that raw page,
  admission and pin status. This historical receipt preceded the now-verified recovery.
- `mode3-prepared.tar.xz`: exact isolated bundle and first cross-built mode-3
  kernel, map, symbols and disassembly. **Superseded prepared revision, never
  run.** The subsequent mode3-tested archive is the executed revision. Preserve this archive.
- `prepared-identity.json`: hashes of that prepared kernel and upload image.
  Kernel: `befd4fc800551eb8a20fdd7247bcef1c839c4d47ae4e0cb4d570cc9c9f93b800`.
  Image: `a9121e456edae637300abe9a6ae6d4d90d8d3ef121b5ec92f23f888b550b6a3c`.
- `native-tests.txt`: current actual C/mock-MMIO and host negative tests,
  including all 2,048 stock-table and 2,048 owned-table bit corruptions,
  dropped vector write, stack guards and one-write NMI alias gate.
- `legacy-replay.json`: current validator accepts the historical physical
  mode-1 and mode-2 captures. This does not qualify the new hardware paths.
- `manual-source.json`: Intel 80303 manual source, document hash and reviewed
  sections; manual scan is referenced rather than duplicated here.

Remote working copy: `/home/mit/i960-exceptions-20261018/bundle`, now mode 4.
Previous normal boot: `f999aba6-1276-470b-9130-1c589ed25d55`.
Previous normal kernel:
`4a9c0278ff23815ea94d546a7fc43bfc3566c8ff916b70d0c2b0e7e42582ad3e`.
The firmware remains
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
No firmware programming was performed. SCSI/cache exclusion, active-DMA fault
containment and owned-ISP normal runtime remain separate unclosed gates.

Checksums cover this batch only. The unrelated pre-existing artifact symlink
`artifacts/current/accele160-flat-20261018/post-0/data.bin` still prevents a
clean whole-repository inventory audit; this batch does not modify it.

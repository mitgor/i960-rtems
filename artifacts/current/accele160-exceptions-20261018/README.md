# Accele160 P3b candidate and prior-session shutdown evidence

Status: **mode 3 actual processor fault passed; mode 4 NMI awaits recovery**.
Fresh boot `b748d05a-16d1-40bf-b96d-973127ab6856` and its paired firmware reads
closed the previous normal runtime's reset check. The real `faulte` then passed
at tick 18, exact fault IP `c0716230` = `_accele_raise_fault+4`, with owned
fault entry `c0716150`, NMI entry `c0716160`, ISP `c0779040`, all fault entries,
intact guards, stable records and retained resources after STOP.

The reset after this successful fault test again left SSH refusing connections.
Mode 3 post-test reset recovery remains pending. Mode 4 has been cross-built
and saved but has NOT run. Prompt remains offline. See
[`OWNED-EXCEPTIONS.md`](../../../rtems/accele160/fault/OWNED-EXCEPTIONS.md).

- `mode3-tested.tar.xz`: exact executed current mode-3 bundle and complete
  `sessions/20261018T202453Z`, including both guarded firmware reads and raw
  READY/stale/terminal/stable/after-STOP snapshots.
- `mode3-replay.json`: independent `verify_archive.py` output. Checks exact
  symbols/fault IP, table/ISP/guards, kernel/image/source hashes, firmware pair
  and retained admission/pins. Raw record: `2002,9002,50001,c0716230`.
- `previous-normal-recovery.json`: links the fresh paired reads to the prior
  normal runtime's reset gate. Supersedes the earlier pending recovery receipt.
- `mode4-prepared.tar.xz` and `mode4-prepared-identity.json`: exact next NMI
  test bundle, cross-built and not run. Kernel
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
containment, real NMI delivery, owned-ISP runtime and reset recovery remain
separate unclosed gates.

Checksums cover this batch only. The unrelated pre-existing artifact symlink
`artifacts/current/accele160-flat-20261018/post-0/data.bin` still prevents a
clean whole-repository inventory audit; this batch does not modify it.

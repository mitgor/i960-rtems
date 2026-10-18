# Accele160 P3b candidate and prior-session shutdown evidence

Status: **hardware fault/NMI tests pending physical recovery**. No candidate
has been run on the card. PC `192.168.2.75` refused SSH after the reset from the
previous normal runtime. The prompt is offline. Source and resume instructions:
[`OWNED-EXCEPTIONS.md`](../../../rtems/accele160/fault/OWNED-EXCEPTIONS.md).

- `previous-normal-final.tar.xz`: complete prior normal session
  `sessions/20261018T195841Z`, collected after clean global STOP. Raw
  `run/persist/quiescent-page.bin` contains QUIE/ACK, 128 drained frames and
  no remaining DMA sources. Admission remains pending; pin guards unchanged.
- `previous-normal-stop-replay.json`: independent checks of that raw page,
  admission and pin status. Reset recovery is still false/pending.
- `mode3-prepared.tar.xz`: exact isolated bundle and first cross-built mode-3
  kernel, map, symbols and disassembly. **Superseded prepared revision, never
  run.** Current source adds further checks, earlier priority masking and mode 4;
  overlay/rebuild/re-manifest before any card run. Preserve this archive.
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

Remote working copy: `/home/mit/i960-exceptions-20261018/bundle`.
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

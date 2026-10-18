# AcceleRAID P3a terminal diagnostics — 2026-10-18

Status: **both software-terminal tests passed; mode-2 reset/normal-runtime tests open**.
No firmware was written. P3 fault/NMI/hardware engine ownership is not complete.
[Source, layout and runbook](../../../rtems/accele160/fault/README.md).

## Physical result

The PC returned on fresh boot `1eaf5d65-1ede-40da-a02c-8888d6b91e9f`, without
a prior service or retained module. Two independent full guarded firmware reads
matched `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`,
with status/residual/guard changes zero. These also close the previous P1/P2
service's reset gate; its raw QUIE/ACK shutdown record is independently replayed.

The candidate kernel SHA-256 is
`75e8cc17a0f504651d6931b834af97adf764c9b292cdecba657d165176c257ae`;
image SHA-256 `5b7df5fdf7bb329c8b0ea48723ec4d621e1d89f2035c463d83401c9de2a816af`.
Build text/data are 42,352/4,496 bytes, ordinary BSS ends `c071c3c0`, below
the unchanged IRQ boundary `c0724000`. NOLOAD reserves the diagnostic/stack
pages without extending the 29-page admission image. Disassembly shows the
priority-31/mask stores, timer-1 disable, stack switch to `c0778100`, and final
non-returning record call. This is a software entry, not a hardware vector.

Session `20261018T193520Z` passed stale nonce refusal, explicit fatal code
`7d001`, DONE at tick 18, intact guards, stable repeated raw captures, and
unchanged record after host STOP. Admission stayed `started=1 done=0 released=0`;
DMA pin state remained `retained=1 guard_changes=0`. No Doom image was admitted
and no frame DMA was started. The three CCR/NDAR/BCR triplets were all zero.
This idle observation does not prove independent bus-master exclusion.

Captured live state: PRCB `feffdd20`, ISP `c0001000`, cached NMI `c00521b0`,
RTEMS timer vector `c0715e50`, ICON `6000`, interrupt mask zero after terminal
entry. The first sixteen RAM fault entries were `(c0053400,0)`; the remaining
sixteen were `(0,0)`. No exception vector or fault-table entry was changed.
Original software-entry FP/SP were `c074d9c0`/`c074da00`.

The first harness invoked the isolated terminal test immediately after READY.
Replay independently checks its saved full-bank report and arena claim. The
final source moves injection after the existing host bank/arena/tail checks,
and suppresses the unused browser endpoint for test profiles. This host-only
ordering correction passed in mode 2; the immutable mode-1 archive retains
the precise earlier runner, not the corrected source.

## Files and replay

- `mode1.tar.xz`: exact bundle, source, firmware/kernel/modules, link map,
  disassembly, build log, manifest and complete physical session. The pinned
  Freedoom WAD is referenced from the existing archive rather than duplicated.
- `previous-service-final.tar.xz`: complete final P1/P2 session including its
  late global STOP captures, collected after recovery. Exact original bundle
  remains in `../accele160-service-20261018/followup.tar.xz`.
- `previous-service-shutdown.json`: actual shutdown result from boot
  `97e816ae-5c7f-467e-a59a-4235ef11c519`.
- `rom-audit.json`: independently reproducible pinned-firmware PRCB inspection.
- `native-tests.txt`: sanitizer policy/actual-C tests (mock MMIO), host retention
  and corruption tests, and existing production pump tests. No native test is a
  substitute for target assembly execution.
- `verify.py`, `replay.json`: bundle hash, pre-reset firmware, ready bank/claim,
  raw terminal/guards/retention, deliberate corruption rejection, and prior
  service shutdown/reset validation. No post-mode-1 reset claim yet.

```sh
python3 artifacts/current/accele160-fault-20261018/verify.py
```

## Guard-corruption test — accepted before reset

On fresh boot `03bd813b-ac1c-4925-9270-34e1f0a1fad8`, session
`20261018T194400Z` ran compiled test mode 2. Its two guarded full-flash reads
matched the same firmware with zero status/residual/guard changes, closing
mode 1's post-reset gate. No old daemon or retained module was present.

Kernel SHA-256:
`6f5bcab84c78d529cfef5a9009007dadd4e32f28ede000e331b10bd349bece71`.
After the bank/arena/tail checks, the stale nonce was rejected. The valid trigger
changed the first private stack guard word and entered the software-terminal
path. The record correctly reports `guards_intact=false`, code `7d002`, ticks
18, and the same original FP/SP and stock NMI/ISP/fault-table contents as mode 1.
Repeated capture and post-terminal STOP did not change the record. Admission
remained `started=1 done=0 released=0`; DMA buffers remained retained with zero
DMA guard changes. Private stack-guard corruption and DMA guards are separate
observations. This deliberate test is not a real stack overflow or proof that
arbitrary corruption will be detected automatically.

`mode2.tar.xz` holds its exact 248 included bundle files, binaries, build and
manifest, disassembly, service log and complete session. Independent replay
checks both modes, malformed-record rejection and mode 1's reset proof. The
existing pinned WAD is referenced rather than duplicated.

## Exact resume boundary

Mode 0 (`ACCELE_TERMINAL=1 ACCELE_TERMINAL_TEST=0`, service enabled) is built
in `/home/mit/i960-fault-20261018/bundle`, with regenerated manifest/bundle
hashes. `mode0-prepared.tar.xz` preserves that complete prepared bundle and
build logs locally. Its kernel SHA-256 is
`4a9c0278ff23815ea94d546a7fc43bfc3566c8ff916b70d0c2b0e7e42582ad3e`;
image SHA-256 `d1423bbbbc7bff195dff7006ca0f26f094aaf44f8aa71d00389475984555038e`.
All included file hashes replay, but this kernel has not run on the card.

The PC again refuses SSH after rebooting from mode 2. The user was asked to
power-cycle if stuck. **The prompt is offline.** After recovery, verify fresh
boot/no old owner and launch the isolated mode-0 bundle with full guarded
prechecks; those reads close mode 2's reset gate. Run two bounded Doom games,
console client tests, idle/rearm/global STOP and capture everything, then
verify reset and restore a live prompt using the accepted service profile.
Do not adopt or free retained mappings. No new source overlay is currently
needed; the remote mode-0 bundle already includes the corrected test ordering.

Remaining P3: real owned fault/NMI entry and stack policy; controlled hardware
fault/NMI tests; all interrupt routes; SCSI/cache/other bus-master exclusion;
terminal state with genuinely active/stalled DMA; independent watchdog research.
The PG coexistence route is unchanged.

The full repository artifact auditor still encounters the unrelated historical
symlink noted in the P1/P2 ledger. Only this batch's hashes and incremental
inventory are verified here; no whole-repository audit success is claimed.

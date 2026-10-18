# AcceleRAID P3a terminal diagnostics — 2026-10-18

Status: **mode-1 software-terminal physical test passed; reset/next tests open**.
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
ordering correction still needs physical use in mode 2; the immutable mode-1
archive retains the precise earlier runner, not the corrected source.

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

## Exact resume boundary

Mode 2 is built in `/home/mit/i960-fault-20261018/bundle`; its manifest and
bundle hashes were refreshed before reboot. The PC now refuses SSH after that
reset. The user was asked to power-cycle if stuck. **The prompt is offline.**

After recovery, overlay the final `doom_dma/run_bridge.py` ordering correction,
refresh bundle identities, check fresh boot/no old owner, and launch the isolated
mode-2 bundle with the existing full guarded prechecks. Those reads close mode
1's reset gate. Save the complete mode-2 capture before another reset. Then
verify its reset and build mode 0 for ordinary Doom/console/STOP qualification;
restore the prompt only after passing. Do not adopt or free retained mappings.

Remaining P3: real owned fault/NMI entry and stack policy; controlled hardware
fault/NMI tests; all interrupt routes; SCSI/cache/other bus-master exclusion;
terminal state with genuinely active/stalled DMA; independent watchdog research.
The PG coexistence route is unchanged.

The full repository artifact auditor still encounters the unrelated historical
symlink noted in the P1/P2 ledger. Only this batch's hashes and incremental
inventory are verified here; no whole-repository audit success is claimed.

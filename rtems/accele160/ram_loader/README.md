# Resident RTEMS RAM loader

## Flash identity diagnostic prepared offline

`flash_identify_payload.c` is a separate one-page RAM1 payload. Once RAM1 has
booted on the spare and the return-value payload has passed, it can issue only
the Intel read-array (`FF`) and read-identifier (`90`) commands. It reports
`SID1` in RAM1 control word 13, manufacturer in word 14, device in word 15,
master lock in word 16, and all sixteen block lock bits in word 17.
It returns zero only for ID `89/A6` with all those locks clear. The payload
restores read-array mode before publishing its result. Its offline build helper
is `build_flash_identify.sh`; neither the helper nor the diagnostic erases or
programs flash. This probe cannot measure VPP or prove that the board permits
flash writes.

The 2026-11-20 Slot 5 image boots native RTEMS and implements UPD1 RAM staging.
It has no RAM execution command and no flash writer. It cannot start a host
downloaded program as it stands. The loader below is the next ROM image to
build and test offline, then install on a stock-booting spare through the
previously tested stock `FLASHIMAGE` command. Keep the external programmer as
recovery if a native image fails before the host can reach it. Once it
works, ordinary application iterations should need only a host upload and a
card reset, not a flash write.

## Boot and memory contract

Keep the stock reset block, stock x86 ROM, stage-two PCI retry release, and
current RTEMS base. The resident RTEMS owns the host control transport. A
separate app window starts at `0xc0710000` and ends before `0xc07f0000`
(896 KiB maximum). It is outside the resident RTEMS image and its entry
stack (`0xc0010000..0xc003ffff`) and below the upper 8 MiB arena. It is the
same base used by the earlier Doom RTEMS RAM experiments. Verify the window
with a physical alias and pattern audit before enabling `RUN`.

Use two host visible odd 4 KiB pages for a distinct `RAM1` protocol:

| Local address | Purpose | Host PIATVR value |
| --- | --- | --- |
| `0xc0805000` | control and result | `0xc0804000` |
| `0xc0807000` | one 4 KiB upload page | `0xc0806000` |

These do not overlap the current UPD1 pages at `0xc0801000` and `0xc0803000`.
The host maps the odd page through BAR0 offset `0x1000`, restores PIATVR to
`0xc0000000` after every session, and checks the PCI identity before and
afterward. UPD1 and RAM1 sessions are mutually exclusive; no flash command is
part of RAM1.

The first payload is a flat, fixed address i960 image. Its host manifest pins
load address, padded byte length, entry offset, and SHA-256. `BEGIN` checks
the bounds; sequential 4 KiB `CHUNK` commands copy to the app window and
verify FNV32 per page; `SEAL` checks SHA-256 over the complete image. `RUN`
is accepted only after seal. The resident RTEMS starts a task with a small
versioned API table and a private stack; the app returns a result code and
never takes over the reset path. A timeout or fault leaves a diagnostic and
requires a card reset before another run. Do not claim clean return until the
task, interrupt, DMA, and allocation lifetime has been audited on hardware.
Before `RUN`, flush data writes and invalidate the i960 instruction cache;
the existing Doom RAM entry uses `icctl 2` for this purpose. Recheck the
loaded SHA after the cache transition and before branching to the entry.

## Milestones

1. **Read-only current-card gate:** confirm the UPD1 control magic through a
   reversible PIATVR mapping, record PCI stability, and leave the card idle.
2. **Offline loader core:** validate bounds, sequential chunks, hashes,
   entry range, and abort; reject every malformed payload before execution.
3. **Offline host transport:** add `RAM1` upload/verify and restore-on-error
   logic using the existing BAR code, with a QEMU card model and fault tests.
4. **First payload:** compile a tiny i960 RTEMS task that increments a counter,
   returns a known value, and reports through the control page. Test it in
   the i960 interpreter and QEMU before a stock `FLASHIMAGE` to the spare.
5. **Physical first run:** use stock `FLASHIMAGE` while the spare still runs
   stock firmware to install the loader ROM, cold boot, upload the tiny
   payload, run once, reset, and
   repeat. Keep the other stock card out of the PC.
6. **Doom:** first port the existing 867,792-byte relocatable engine to the
   resident RTEMS task/API. Reserve the proven upper 8 MiB arena for engine,
   6 MiB zone, WAD cache, and framebuffer. Reuse the already tested frame,
   key, STOP, and WAD transports. Full Doom is a later test after the tiny
   task and repeated RAM-only runs pass.

The initial loader should be an RTEMS application service, not a second RTEMS
kernel. Jumping into a second full RTEMS image from an already running RTEMS
instance would require an explicit interrupt, timer, cache, and scheduler
handoff. Keep that as a separate reboot-only mode if module integration proves
too restrictive.

## Current implementation checkpoint

The read-only UPD1 probe on the flashed card passed at uptime 3310 seconds:
magic `UPD1`, version 2, idle sequence/state, PIATVR restored, and PCI identity
responsive. Its receipt is in
`../../../artifacts/current/accele160-restored-first-spare-updater-20261120/remote-evidence/upd1-readonly-probe.json`.

`loader.c` now implements the RAM image admission core: fixed maximum size,
aligned in-range entry, ordered 4 KiB chunks, per-chunk FNV32, whole-image
SHA-256, seal-before-entry, and abort only before execution. Its native host
test passes. `manifest.py` creates the corresponding fixed-address image
manifest and rejects invalid size or entry geometry; its tests pass. None of
this new loader code has been linked into the resident RTEMS build or run on
the card. The next code step is the `RAM1` host-visible service and upload tool.

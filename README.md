# Tetris on an Intel i960

**Current work (2026-10-11):** card-hosted IPv6 HTTP and stock-coexisting autonomous RTEMS now pass live tests. A hardware timer delivered 2,009 ticks/task wakeups during 20 seconds without host polling; the network build advanced 509 ticks during five silent seconds. IPv6 Internet HTTP, dual-stack echo, a one-minute IPv6 stress run, and kernel STOP-before-restore cleanup passed. See [current work report](artifacts/rtems-web-autonomous-20261011/README.md) for artifacts, failed trials, limitations and the published server.

**Current development roadmap:** [loader memory extension, RTEMS and remaining gaps](DEVELOPMENT-PLAN.md). Next: M1, generalize the proven larger RAM profile; preserve scalar/BIO1 compatibility.


**Current index (2026-10-11): [findings, evidence and unresolved questions](CURRENT-FINDINGS.md).** Earlier milestone notes below retain their historical context.

**IPv6 is implemented and tested on the card (2026-10-11):** dual-stack ping, UDP/TCP echo, AAAA and IPv6 Internet HTTP. [Usage](rtems/README.md#ipv6-usage-and-scope), [preserved evidence](artifacts/rtems-ipv6-20261011/README.md). Use the new `i960-rtems-ipv6-20261011` launcher with `--ipv6` or `--internet6`; the latter also routes IPv4 DNS. The cooperative execution model and RAM limits remain unchanged.

**RTEMS now runs on the card (2026-10-11): [implementation and usage](rtems/README.md).** RTEMS 4.6.6 tasks persist across bounded firmware callbacks; lwIP 2.1.3 provides ICMP, UDP/TCP echo and card-originated DNS/HTTP through a Linux TUN/NAT gateway. The original `net` profile uses host-supplied ticks; the newer `autonet` profile uses hardware timer interrupts with bounded work and preserves stock firmware service. [Exact artifacts and findings](artifacts/rtems-20261011/README.md). No additional flash programming or reboot.


**T4 complete (2026-10-10): [play Tetris over SSH](TETRIS-TERMINAL.md).** The terminal client passed a 30-minute real-SSH test: 35,846 native-matching frames, 68 restarts, 19.91 Hz. Quit, Ctrl-C, connection loss/reconnect and resize cleanup passed. Use `ssh -t mit@192.168.2.75 /home/mit/i960-tetris-t4/play.sh`. Full RAM restored, module unloaded; no reboot or flash.


**T5 complete (2026-10-10): [persistent BIO1 sessions](PERSISTENT-SESSION.md).** 1,000 frames matched native output at 41.1 ms median; a separate 400-frame run sustained 20 Hz. Process-kill/ownership cleanup and full final RAM restoration passed. `host/session/` keeps paired code/payload checks every frame and full staging audits every 32 frames and close. The subsequently completed T4 terminal client uses this transport; no reboot or flash.


**T3 complete (2026-10-10): [long Tetris hardware replay](TETRIS-REPLAY.md).** 1,000-call main replay plus 64 repeat calls matched native state/frame bytes; all RAM restored and probes unloaded. Median full CLI latency 306 ms (~3.26 updates/s), payload-command interval ~6.18 ms. This baseline motivated the now-completed T5 session optimization; T4 terminal play is now complete; see the latest milestone above. No reboot or flash.

**T2 complete (2026-10-10): [bounded Tetris steps](TETRIS-STEP.md) run on the card.** Explicit 240-byte state, 20-tick bound, 24×80 rendering; 1,024 native/interpreted transitions agree, and nine live transactions match the native reference byte for byte. RAM restored; no reboot/flash. T3 replay, T5 persistent sessions and T4 terminal play subsequently passed.

**T1 complete (2026-10-10): [bounded text/framebuffer I/O](BUFFER-IO.md) is hardware validated.** BIO1 supports 4 KiB input / 8 KiB output; live text, 24×80 frame, capacity rejection and repeat/scalar regression passed with RAM restored. T2 subsequently converted the blocking game into hardware-tested returning steps.

**Latest hardware milestone (2026-10-10): [runtime software loader](SOFTWARE-LOADER.md) works after PC startup.** Three live executions (two C programs) passed without reboot or another flash write. Use `host/loadrun/` and `loader/runtime/` from the repository root; earlier internal-RAM and pre-programming plans below are historical. Supports cooperative returning functions up to 64 KiB, with one argument and a 32-bit result. RAM restored and module unloaded after each run. Recovery remains untested.


**Current hardware (2026-10-10): [patched firmware is programmed and boot-validated](FIRMWARE-PROGRAMMED.md).**
One 2B/1 programming command succeeded; paired full flash readbacks match
candidate SHA256 `a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`.
After reboot, table C001F9BC points to FEFE001C and two 6F commands returned
017E; stock health checks passed. Probe unloaded. The card is no longer stock;
use the postboot validator, not old stock-preimage rehearsals. Recovery untested.
Evidence: `artifacts/programmed-rom-20261010/` from repository root. Older
pre-programming sections below are historical and superseded by this result.


Latest: [one-shot programming harness](ONE-SHOT-PROGRAMMING.md) is implemented in `host/program/`
(repository-root relative). Native transport/failure tests and a 105-command live
RAM-only rehearsal passed. Wrong activation token rejected before driver
registration; no programming doorbell issued. Full stock RAM restored and probe
unloaded. Exact binaries/captures are in `artifacts/one-shot-harness-20261010/`.
At this rehearsal milestone programming was still pending. Programming, full
readback and patched boot subsequently passed; see FIRMWARE-PROGRAMMED.md.
Recovery testing remains excluded.


Latest (2026-10-10): [programming preflight and live CPU verification](PROGRAMMING-PREFLIGHT.md)
passed. The CPU read all 512 KiB of the candidate through programmer alias
C1F2C000 with explicit cache invalidation and matched CRC32 2012D01F. All 105
commands completed cleanly; original staging/table/code restored, probe unloaded.
The descriptor policy and bytewise post-program flash-readback route are now
documented. Next implement the one-shot programming state machine and its
failure tests. No flash programming or recovery test occurred. Exact evidence
is in `artifacts/programming-preflight-20261010/` from the repository root.


## Live staging rehearsal

[Live staging rehearsal](STAGING-REHEARSAL.md) passed: six full 512 KiB captures verify the original
stock image, the patched candidate in RAM, and complete stock restoration.
All 74 commands completed cleanly; probe unloaded. Exact binaries, source,
logs and validation are in `artifacts/staging-rehearsal-20261010/` (relative
to the repository root). No flash programming or recovery test occurred.


Repurposing a retired Mylex DAC960PG RAID controller (Intel **i960RP**) into a
general-purpose computer that runs Tetris. Hobby/bench project, all on the owner's
own hardware.

## Status

- ✅ **Tetris runs as real i960 machine code.** Built with a from-source i960
  cross-toolchain; a small interpreter executes the actual i960 instructions and
  acts as a text terminal (framebuffer + keyboard over shared memory). Two
  self-checks prove the interpreter decodes i960 correctly (below).
- ✅ **Full in-system flash dump recovered and validated.** A constrained
  coherent-DMA kernel module read the card's flash while installed, yielding a
  512 KiB image whose firmware, boot block and x86 BIOS each match independent
  references exactly, with a checksum-valid i960 IBR. See
  [SNAPSHOT-RECOVERY.md](SNAPSHOT-RECOVERY.md) and
  [artifacts/ROM-DUMP-WORKLOG.md](artifacts/ROM-DUMP-WORKLOG.md).
- 🔬 **Live handoff and flash fetch verified; custom ROM not flashed.** A
  reversible host upload changed the card's `0x6F` command-table word, and a
  RAM callback called a stock flash `RET` after startup. The stock table and
  both RAM sites were restored. See [ROM-FETCH-LIVE.md](ROM-FETCH-LIVE.md).
  The new `FEFE001C` handler still needs a validated update procedure and a
  live programmed-image test.
- ⏸️ **General-purpose flash loader: in progress.** The dump corrected
  the real boot geometry (512 KiB flash based at `0xFEF80000`; live IBR at
  `0xFEFFFF30` → boot block, not the firmware payload). A blocker was also found:
  the i960 faults on instruction fetch from internal data RAM, so loaded code must
  live in external DRAM. See [loader/README.md](loader/README.md) and
  [PROJECT-REVIEW.md](PROJECT-REVIEW.md).

The same Tetris binary and I/O model are what would run on the physical card once a
custom-firmware path is finished; today it runs under the interpreter with no
hardware risk. The card boots its own flash firmware at power-on (reset **Mode 2**,
from EBCR `0x0018`), so code can't be loaded purely in software as-wired — hence the
reflash/loader route.

## Layout
- `game/` — the i960 side: `tetris.c`, `io.h` (shared-memory contract), `i960.ld`, `Makefile`.
- `host/` — the Ubuntu side: `emu.c` (i960 interpreter + ANSI terminal), self-checks,
  `kmod/` (PG mailbox probe), `dump/` (the flash-dump kernel module + validators).
- `loader/` — flash loader and Linux sender (paused); see [loader/README.md](loader/README.md).
- `toolchain.sh` — builds the i960 cross-toolchain (binutils 2.27 + gcc 3.3.6).
- `artifacts/` — the validated 512 KiB dump, vendor firmware references, BIOS, logs;
  start at [artifacts/ROM-INVENTORY.md](artifacts/ROM-INVENTORY.md).

## Build & run (on the Ubuntu box, toolchain already in ~/i960/tools)
```
cd ~/i960/game && make                 # -> tetris.elf (i960)
cd ~/i960/host && gcc -O2 -o emu emu.c  # host interpreter
./emu ../game/tetris.elf                # play:  a/d move, w rotate, s drop, q quit
```

## Verify it really executes i960 code
```
./emu -t test.elf        # CPU self-check: must match ./ref        (-135781)
./emu -t test_clear.elf  # line-clear logic: must match ./ref_clear (200110)
```
Each test runs the *same* C compiled both for i960 (under the interpreter) and natively;
matching outputs prove the interpreter decodes i960 instructions correctly.

## Documentation

**ROM dump & flash (current work):**
- [SNAPSHOT-RECOVERY.md](SNAPSHOT-RECOVERY.md) — the validated 512 KiB capture, exact
  4.07-0-29 match, and corrected flash layout.
- [artifacts/ROM-DUMP-WORKLOG.md](artifacts/ROM-DUMP-WORKLOG.md) — how the dump was done,
  what validates it, and the honest limits (staging read, not a certified physical backup).
- [artifacts/ROM-INVENTORY.md](artifacts/ROM-INVENTORY.md) — index of every archived file.
- [host/dump/README.md](host/dump/README.md) — the dump kernel module and validators.
- [DRAM-ANALYSIS.md](DRAM-ANALYSIS.md), [VENDOR-READ-PATH.md](VENDOR-READ-PATH.md),
  [FIRMWARE-HANDLERS.md](FIRMWARE-HANDLERS.md), [FIRMWARE-40729.md](FIRMWARE-40729.md),
  [DUMP-ATTEMPT.md](DUMP-ATTEMPT.md) — supporting analysis.

**Reference:**
- [FINDINGS.md](FINDINGS.md) — consolidated technical findings (hardware, command channel,
  GlobalFlash encoding, firmware protocol, BIOS, toolchain).
- [PROJECT-REVIEW.md](PROJECT-REVIEW.md) — broader review, including the loader blocker.
- [MANUAL.md](MANUAL.md) — build/run the toolchain, game, and emulator; card facts.
- [FIRMWARE-PROTOCOL.md](FIRMWARE-PROTOCOL.md) — the host→i960 mailbox channel and register map.
- [FIRMWARE-PACKAGE.md](FIRMWARE-PACKAGE.md) / [FLASHER.md](FLASHER.md) — Fujitsu firmware
  package, GlobalFlash decoding, and the DOS flasher / MIMG format.
- [BIOS-ANALYSIS.md](BIOS-ANALYSIS.md) — the card's x86 option ROM disassembly.
- [MODE0.md](MODE0.md) / [REFLASH.md](REFLASH.md) — reset-strap and reflash routes to custom code.
- [SESSION.md](SESSION.md) — full session context / handoff.
- [host/globalflash_decode.py](host/globalflash_decode.py) — verified GlobalFlash decoder.

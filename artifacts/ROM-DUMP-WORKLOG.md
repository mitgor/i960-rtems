# ROM dumping work log and findings

**Current hardware (2026-10-10): [patched firmware is programmed and boot-validated](../FIRMWARE-PROGRAMMED.md).**
One 2B/1 programming command succeeded; paired full flash readbacks match
candidate SHA256 `a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`.
After reboot, table C001F9BC points to FEFE001C and two 6F commands returned
017E; stock health checks passed. Probe unloaded. The card is no longer stock;
use the postboot validator, not old stock-preimage rehearsals. Recovery untested.
Evidence: `artifacts/programmed-rom-20261010/` from repository root. Older
pre-programming sections below are historical and superseded by this result.


Latest: [one-shot programming harness](../ONE-SHOT-PROGRAMMING.md) is implemented in `host/program/`
(repository-root relative). Native transport/failure tests and a 105-command live
RAM-only rehearsal passed. Wrong activation token rejected before driver
registration; no programming doorbell issued. Full stock RAM restored and probe
unloaded. Exact binaries/captures are in `artifacts/one-shot-harness-20261010/`.
Actual flash programming, post-program physical readback and patched boot remain
untested. Recovery testing remains excluded.


Latest (2026-10-10): [programming preflight and live CPU verification](../PROGRAMMING-PREFLIGHT.md)
passed. The CPU read all 512 KiB of the candidate through programmer alias
C1F2C000 with explicit cache invalidation and matched CRC32 2012D01F. All 105
commands completed cleanly; original staging/table/code restored, probe unloaded.
The descriptor policy and bytewise post-program flash-readback route are now
documented. Next implement the one-shot programming state machine and its
failure tests. No flash programming or recovery test occurred. Exact evidence
is in `artifacts/programming-preflight-20261010/` from the repository root.


## Live staging rehearsal — 2026-10-10

[Live staging rehearsal — 2026-10-10](../STAGING-REHEARSAL.md) passed: six full 512 KiB captures verify the original
stock image, the patched candidate in RAM, and complete stock restoration.
All 74 commands completed cleanly; probe unloaded. Exact binaries, source,
logs and validation are in `artifacts/staging-rehearsal-20261010/` (relative
to the repository root). No flash programming or recovery test occurred.


## Later live execution result — 2026-10-10

[ROM-FETCH-LIVE.md](../ROM-FETCH-LIVE.md) records the completed RAM-dispatch
and post-startup flash-fetch work. A wrapped `0x21` offset changed `0x6F`'s
RAM table word; target-built callbacks returned `017E` and `017F`. One early
flash call timed out because the disassembly label `FEFC8208` was not the
physical address of those bytes in the saved 512 KiB image. Read-only live
windows established the 8-bit flash-bus low-lane mapping. A corrected call to
the stock `RET` at `FEFB022C` returned successfully after startup; stock
dispatch and all altered RAM were restored. No flash programming or recovery
check occurred. The new `FEFE001C` handler remains unflashed.

Current result, 2026-10-10: the card remained installed in the PC and yielded a
validated 512 KiB software snapshot. The main firmware is exactly 4.07-0-29.
All source packages, ROMs and capture sessions are now stored locally; start with
[ROM-INVENTORY.md](ROM-INVENTORY.md). Directory timestamps ending in `Z` are UTC;
for example `125336Z` is 14:53:36 in Europe/Berlin on this date.

## Investigation sequence

1. Reviewed the project and loader. Improved loader protocol bounds, fresh
   sequence handling, address policy, host checks and software validation, and
   documented outstanding hardware gates. Native tests do not prove hardware
   execution: the i960 internal RAM at 0x000–0x3FF is data-only, so the old
   hello-at-0x200 plan cannot work. See `loader/REVIEW.md`, `loader/PROTOCOL.md`,
   `loader/CLAUDE.md` and `PROJECT-REVIEW.md` in the project.
2. Explored the authorized SSH host, Ubuntu 6.8.0-138-generic, controller
   0000:37:09.1, PCI 1069:0010, with i960 bridge at .0. The card reports
   4.07-0-29. A PCI expansion-ROM read recovered the 28 KiB x86 BIOS, but did
   not expose the complete i960 program. BAR0 is an 8 KiB aperture; it is not
   a general mapping of flash or arbitrary local registers. Unbinding myrb had
   wedged previously; the subsequent experiments used an already driverless card.
3. Obtained Fujitsu's PG 4.07-0-39 package. Decoded the GlobalFlash transform:
   apply XOR 0xC3, then permute bit index i to i XOR 6 (see the archived decoder).
   Normalized firmware containers by removing their 512-byte header and ten-byte
   trailer. The executable and firmware then became available for static analysis.
4. Built a constrained coherent-DMA kernel experiment. Enquiry2 succeeded.
   The initial 0x21 experiment left host buffers unchanged. Later corrected
   symbol parsing and vendor dataflow showed why: 0x21 uploads host bytes to
   staging. Its final 0x5A fill contaminated staging; it was not a dump.
   No ProgramImage command was issued. Preserve this mistake as evidence;
   do not repeat it. See `DUMP-ATTEMPT.md` and `VENDOR-READ-PATH.md`.
5. Corrected DOS public-symbol parsing: address fields precede names. Verified
   0x20 card-to-host and 0x21 host-to-card directions. Restricted the harness to
   Enquiry2 and 0x20. Paired small reads confirmed working DMA, but returned
   staging fills or unidentified compressed-looking data, not a validated image.
6. Extracted the firmware's standard PKZIP method-6 ZIP1 program with Info-ZIP,
   validating output length, CRC and hashes. This is ZIP Implode, not DCL/blast.
   Recovered opcode dispatch, board callbacks, DMA descriptors and a helper that
   copies flash into staging once, then reuses the staging pointer. A previous
   upload therefore affects future reads until staging is renewed.
7. Analyzed memory initialization. Found static-bank register writes and board
   register profiles 0x257C203C / 0x231C201C. These are useful initialization
   evidence, not decoded DRAM timing values. Bit-field meanings, clock-dependent
   timings and their applicability to the installed boot block remain open.
   See `DRAM-ANALYSIS.md`; its older FWPJBBLK reference is not the recovered
   FWTCBBLK. No DRAM profile was programmed.
8. Downloaded the user's Fujitsu PRL 4.07-0-29 reference. Its bootstrap and
   relevant read/copy/DMA handlers match the 4.07-0-39 reference; decompressed
   programs differ by 555 bytes. This removed version mismatch as an explanation
   for the unexpected read offsets. See `FIRMWARE-40729.md`.
9. Read the entire initially allowed 256 KiB window. Found the first 64 KiB
   of the exact main firmware at offset 0x30000, with its ZIP at 0x37000.
   The previous expected offset 0x8000 had come from a different startup profile.
10. The host became briefly unreachable and returned with uptime below one minute.
    A reboot had been authorized, but this agent did not issue it. A fresh read
    now began with an intact EZAssist ZIP. Firmware at 0x30000 and BIOS at 0x28000
    supported the alternate 512 KiB profile, source FEF80000, descriptor FEFF9C00.
11. Extended the tested PG harness bound to 0x80000 and captured nine chunks,
    each twice with different host fills and Enquiry2 before/after. All 36
    completions had correct IDs, zero status, intact guards and pending=0.
    Both assembled 524,288-byte images are identical. Full-image SHA-256:
    `43d661af9dee28f531dcce525f8997e5fd11fc879d4a4e8bb07c5ac54a872a93`.
12. Validated main firmware against the vendor 4.07-0-29 payload, boot block
    against FWTCBBLK, and BIOS against the independently read PCI ROM. All are
    exact matches. ZIP1 extracts to 304,120 bytes with CRC 8a9d7f6c; EZAssist
    extracts to 545,516 bytes with CRC 9c5a2a90. No missing bytes were filled
    from vendor images. Removed the module after completion; controller remained
    driverless with PCI command 0006. Kernel build and 14 offline tests passed.
13. Copied both original Fujitsu packages, extracted package members and metadata,
    decoded references, all three snapshot sessions, disassemblies and collector
    to this Mac's `artifacts/` folder. Rechecked package hashes and ROM identities,
    and created a local file inventory and checksums.

## Findings that govern future work

- 0x20 reads firmware staging, not necessarily fresh physical flash on every call.
  0x21 uploads; 0x22 programs. Only 0x1C and 0x20 belong in this read harness.
- Success status and repeatable bytes alone are insufficient. Identity was
  established with full payload comparisons, archive CRCs and the independent BIOS.
- Firmware raw offsets and relocated runtime addresses differ. The copied
  bootstrap uses raw offset + C0009000; decompressed code begins at C0010000.
  Static disassembly labels using FEFC8000 do not establish the live image's base.
- The live image places firmware at 0x30000, BIOS at 0x28000, descriptor at 0x79C00,
  and boot block at 0x7C000. The prior 256 KiB limit was a mistaken generalization
  from the standalone startup path. See `SNAPSHOT-RECOVERY.md` for the full layout.
- PRL package main firmware and boot block exactly match this card. Its BIOS
  differs, and the PG package's FWPJBBLK also differs. Whole-package interchangeability
  has not been established.
- A command timeout is not DMA cancellation. The harness retains DMA memory and
  pins itself on uncertain completion; do not force unload or reuse that state.
- Paired reads came from one staging snapshot. Physical chip capacity, an
  independent programmer comparison and restoration have not been tested.
  The existing independent-backup gate before flashing remains applicable.

## Remaining work

The dumping objective is achieved for the installed main firmware and the 512 KiB
software image. Further work can proceed offline: trace the recovered FWTCBBLK
startup, decode descriptor/component records, and map DRAM profile bit fields
against the correct board hardware. Loader execution and reflashing are separate
unfinished goals; nothing in this dump validates the old internal-RAM execution plan.

Older reports retain the observations and hypotheses available at each stage.
For current status, this log and `SNAPSHOT-RECOVERY.md` take precedence over older
claims that dumping is impossible, that 0x21 reads, or that no valid image exists.

## Git preservation update

At the user's request, removed the exclusions for `artifacts/vendor-fujitsu/`
and `artifacts/private-dumps/`. Original packages, decoded firmware, hardware
captures and supporting analysis are intended to be committed with their provenance
and checksums. Existing directory names remain unchanged so links keep working.

## Remote completeness audit

Compared 295 remote project files with local content and archived 20 additional
items, including the Enquiry2 control log, historical analysis scripts, alternate
BIOS disassembly, old probe source and exact acquisition/target builds. See
[the audit report](remote-audit-20261010/README.md). No modified original files
were found in GCC 3.3.6 or binutils 2.27 sources compared with their upstream
tarballs. The important firmware and capture data were already local.

## Offline loader prototype

Recovered the installed boot block's metadata-based copy/decompression/handoff
path and direct DRAM-controller writes. Built a separate experimental loader
image preserving the stock boot block and compressed program. The prototype
patches a RAM instruction after early PCI setup, then accepts DRAM payloads.
Details, validation and outstanding hardware gates: [POSTINIT-LOADER.md](../POSTINIT-LOADER.md). No flash writes or custom execution occurred.

## Live-test preparation, revision 2

Read-only PCI preflight passed on the remote host. Archived the v2 candidate,
preflight JSON and build evidence in `postinit-preflight-20261010/`; the first
prototype remains preserved. See [LIVE-TEST-PREFLIGHT.md](../LIVE-TEST-PREFLIGHT.md)
for the earlier hook, ROM suppression, DMA guard and unresolved installation gates.
No custom code has executed on the card.

## Programming audit and offline MIMG — 2026-10-10

Archived `postinit-update-20261010/`: experimental firmware component, manifest, programming map and evidence excerpts. The candidate reconstructs exactly; 14 Python tests and the native dispatcher test passed. The matching programming route rewrites lower 496 KiB, with boot block conditional. No remote or flash operation occurred. See [PROGRAMMING-RECOVERY.md](../PROGRAMMING-RECOVERY.md).

## Boot-block recovery analysis — 2026-10-10

`boot-recovery-20261010/` contains the extracted 0x2A00-byte recovery monitor, relocated disassembly, evidence excerpts and offline audit. Descriptor/bootstrap-checksum failures reach this monitor; it sets PCI ID 1069:0011 and supports 20/21/2B commands. No hardware entry or programming was attempted. Native test plus 18 Python tests passed. See [BOOT-RECOVERY.md](../BOOT-RECOVERY.md).

## SSH recovery-entry investigation — 2026-10-10

Archived `ssh-recovery-investigation-20261010/` with read-only live preflight and static evidence. Device remains normal-mode 1069:0010. Traced an unchecked staging-relative address-add lead; staging address and safe handoff remain unknown. No hardware writes or flash. Serial setup instructions and investigation status are in [SSH-RECOVERY-ENTRY.md](../SSH-RECOVERY-ENTRY.md).

## Staging allocator and live control — 2026-10-10

`staging-allocation-20261010/` archives fresh Enquiry2 and paired offset-zero reads, allocator evidence and the checked geometry report. Predicted staging base C0F2C000 remains unobserved directly. Three bounded control runs completed cleanly; the first two exports failed locally, as documented in [STAGING-ALLOCATION.md](../STAGING-ALLOCATION.md). Native test and 21 Python tests passed. No out-of-window read, upload or flash.

## Live staging pointer confirmed — 2026-10-10

`staging-pointer-20261010/` archives the six-command transcript, all captures, exact source/header, compiled module and verification report. Two four-byte reads returned C0F2C000 at the derived C0112A70 address; all statuses and guards clean, pending=0. Module removed, card driverless. No upload/execution/flash. See [STAGING-POINTER-VERIFIED.md](../STAGING-POINTER-VERIFIED.md).

## Runtime code and board callbacks verified — 2026-10-10

`runtime-read-20261010/` preserves initial and hardened captures, exact executed sources and modules. The paired reads verified C004A2E0 entry bytes, board C0110780, alias C1000000 and the active callbacks. Both 13-command runs completed cleanly; module removed, card driverless. Native guard and 17 Python tests passed. No upload, execution, recovery or flash. See [RUNTIME-READ-VERIFIED.md](../RUNTIME-READ-VERIFIED.md).

## Reversible RAM upload verified — 2026-10-10

`ram-scratch-20261010/` archives exact executed source/headers/module, 20 capture blobs, 22-command transcript and verification. Sixteen bytes at C0FAC010 were uploaded, read back and restored; paired surrounding 64-byte reads verified no neighboring changes. Status/guards clean; pending=0, scratch-dirty=0. Module removed; card driverless. Two native guard tests and 20 Python tests passed. No execution/recovery/flash. See [RAM-WRITE-VERIFIED.md](../RAM-WRITE-VERIFIED.md).

## Live execution handoff boundary — 2026-10-10

This historical boundary was superseded by the later wrapped-offset live
callback experiment at the top of this log.

Reviewed the stock dispatcher and every relevant board callback after the RAM
write result. Host opcode 0x21 reaches only the staging-relative upload handler;
the dispatcher uses fixed firmware continuations and offers no live callback-table
write or branch-to-staging command. `live-handoff-20261010/` preserves a 20-byte
i960 return-status callback linked at C0FAC100, built with the archived target
toolchain and verified byte-for-byte. It was not uploaded or executed. See
[LIVE-EXECUTION-HANDOFF.md](../LIVE-EXECUTION-HANDOFF.md).

## Offline stock-preserving command hook — 2026-10-10

`stockhook-20261010/` preserves an 84-byte target-built metadata hook and a
524,288-byte candidate image. It copies a returning PING handler to candidate
DRAM C0120000, replaces unsupported opcode 0x6F in the decompressed RAM
dispatch table, and branches to the original stock entry. Only padding and
the metadata entry/checksum differ from the pinned dump (76 bytes). Two offline
tests passed. No card execution or flash operation occurred. See
[STOCK-PRESERVING-HOOK.md](../STOCK-PRESERVING-HOOK.md).

## Handler storage audit and ROM successor — 2026-10-10

`dram-hook-audit-20261010/` archives a clean 15-command fixed read, including
two 64-byte zero snapshots of C0120000. The installed bootstrap clears the
site before the hook, and the reviewed allocator starts at C0140000, but
indirect later use is not excluded. Further disassembly found three stock
flash/error paths that free the staging allocation and clear its pointer,
so its extra block cannot safely host a permanent dispatch-table target.

Built a second offline image in `romhook-20261010/`: a 48-byte metadata hook
points opcode 0x6F to a 20-byte PING handler in verified flash padding at
FEFE001C. The new raw image differs from stock in 48 bytes, preserving the
boot block, BIOS, descriptor, bootstrap and compressed program. Both image
test suites passed. Post-startup ROM instruction fetch, cache visibility,
recovery and programming interaction remain untested; no card write or custom
execution occurred. See [ROM-HANDLER-STEP3.md](../ROM-HANDLER-STEP3.md).

## 2026-10-10 — Runtime software loader implemented and exercised

Implemented `host/loadrun` and `loader/runtime`; see [SOFTWARE-LOADER.md](../SOFTWARE-LOADER.md).
Uploaded and ran Fibonacci(10)=55, Fibonacci(20)=6765, then a distinct rotate/XOR
program returning 0x8c2f3b20, all in boot a9429ca4-0144-452d-8a80-7189608ce99b.
Each transaction completed 110 commands and restored the complete staging image,
PING dispatch and temporary code/result RAM. Enquiry2 passed; probes unloaded.
No reboot or flash programming was needed. Added CLI, bounded 64 KiB payload ABI,
one-shot execution/self-disarm, failure tests and evidence validation. Native
ASan/UBSan model covered 194 command-boundary faults. Existing loader tests pass.
Artifacts: software-loader-20261010/. Recovery remains excluded/untested.

## 2026-10-10 — T1 text/framebuffer output passed on hardware

Added opt-in BIO1 input/output blocks to the returning loader. Four runs returned
text/transformed input, a full 24×80 frame, a clean insufficient-capacity error,
and different text after the error. Each completed 128 commands with paired output
capture, immutable-region checks, full restoration and clean unload. Scalar
Fibonacci(20)=6765 still passed with the updated module (110 commands). No reboot
or flash write; same boot as previous loader runs. Independent checks validate all
returned bytes. Native tests cover 230 buffer and 194 scalar command-boundary
faults, six response corruptions, request/response bounds and live captures.
See ../BUFFER-IO.md and buffer-io-20261010/. Next is T2, cooperative Tetris steps.

## 2026-10-10 — T2 bounded Tetris runs on the card

Refactored the game into explicit state/init/update/render with a 20-tick limit.
BIO1 transports a 256-byte request and 2,160-byte state/frame response. A 4,064-byte
payload passed nine live transactions: init, left, rotation, drop, quit, restart,
two-line clear, game over and excessive-tick rejection. Every output byte matched
a native oracle; all 128-command transactions restored RAM and unloaded. No
reboot/flash. Native sanitizer and i960 interpreter tests agree over 1,024
transitions and gameplay/bounds cases. Added missing interpreter setbit support
and failure exit for unsupported instructions; separate instruction tests pass.
See ../TETRIS-STEP.md and tetris-t2-20261010/. T3 long live replay and T4 terminal
play remain planned; nine acceptance calls are not an interactive session.

## 2026-10-10 — T3 long replay and latency passed

Ran 1,000 deterministic returning Tetris calls, then a separate 64-call repeat;
1,037 were actual updates, the remainder initializations/quits. Every state/frame
matched native reference bytes, with clean guards, complete restoration and
unload. Same boot, no flash/reset. Main replay: 466.56 s including evidence
archive verification; full CLI median 306.27 ms, payload command mean 6.18 ms.
The conservative path is ~3.26 updates/s, so 20 Hz needs the planned session
optimization. All captures are preserved losslessly and independently checked
locally. See ../TETRIS-REPLAY.md and tetris-t3-20261010/. T4 interactive play remains.

## 2026-10-10 — T5 persistent BIO1 session

Implemented kernel-owned OPEN/STEP/CLOSE in `host/session/`, retaining the stock
firmware between bounded callbacks and exclusive file ownership. The existing
one-shot module remains available. First conservative persistent smoke averaged
63.85 ms; narrowing routine audits to the entire code/BIO payload and avoiding
redundant inter-frame cache handshakes gave 41.52 ms mean in a 1,000-call replay.
Every returned Tetris state/frame matched the native oracle. A separately paced
400-call run sustained 20.007 Hz, with 13 late frames, maximum lateness 5.84 ms.

Paired payload/code audits occur every call, full staging audits every 32 calls
and at close, followed by full paired restoration/hash checks. The tradeoff is
up to 31 calls' delayed detection outside the payload. All borrowed table/code/
result regions were restored too. No flash command and no reboot; boot ID stayed
`a9429ca4-0144-452d-8a80-7189608ce99b`.

Thirteen SIGKILL delay cases during open/step/close, protocol ownership tests and
last-inherited-descriptor cleanup passed twice. Native ASan/UBSan exercised 292
command-boundary failures plus stale/malformed and output-corruption cases;
existing 194 scalar/230 BIO fault cases still pass. Hardware completion failures
were not deliberately induced. Full Mac reconstruction checked the long replay,
paced output, and all 30 restoration captures. Module unloaded, card driverless.

Evidence and exact binaries: `artifacts/tetris-t5-20261010/`; design and limits:
`PERSISTENT-SESSION.md`. STORY.md gained Act XIX; Claude guidance and the Tetris
plan now mark T5 complete. T4 terminal interaction/30-minute test remains next.

## 2026-10-10 — T4 playable SSH terminal and 30-minute acceptance

Added `host/session/terminal.py` and installed
`/home/mit/i960-tetris-t4/play.sh`. Letter/arrow controls, Space/drop, restart,
urgent quit/Ctrl-C, 32-action input queue, elapsed 50 ms ticks with capped
catch-up, ASCII-only differential rendering and terminal-size pause are working.
The frontend manages the existing T5 session/module and saves evidence on exit.

Real `ssh -tt` automated play ran for 1,800.236 seconds: 35,846 frames, 68
restarts, 19.91 Hz. Median call 42.33 ms; p95 43.54 ms; maximum 59.06 ms.
Host/SSH scheduling was not perfectly periodic: 2,971 late frames, maximum
lateness 380.43 ms, 159 skipped render slots; no dropped simulation ticks.
The input flood deliberately dropped 96 actions. Every frame matched the native
C game independently on the Mac. Phase counts (running/game-over/quit) were
15,733 / 20,112 / 1; restarts were periodic scripted input, not human play.

Additional native-matching tests: 244-frame smoke/normal quit, 102-frame real
SSH connection loss (remote EOF), 64-frame reconnect/Ctrl-C, and 124-frame
installed-launcher resize/pause/resume/quit. All five sessions restored full
staging/table/helper/runner/result RAM and unloaded. Normal SSH exits preserved
remote `stty -g`; frontend tests also cover exception restoration on Linux/Mac.
No flash write or reboot; same boot as T5. Card left driverless and ready to play.

All 36,380 frame comparisons, exact binaries, sources, ANSI/key traces and
captures are in `artifacts/tetris-t4-20261010/`. TETRIS-TERMINAL.md gives the
one-line play command. STORY.md gained Act XX, and Claude guidance/plan now mark
T4 complete. RTEMS and recovery remain separate work.

## Preservation audit — 2026-10-11

[Final audit](preservation-audit-20261011/README.md) reconciles 7,859 remote
project files and preserves 41 missing historical files. The exact compiler
installation and original upstream sources are in [toolchain-20261011](toolchain-20261011/README.md).
A separately observed terminal session completed during collection: all 2,224
frames independently matched, full RAM restoration and unload passed. No card
commands, reboot or programming were performed by the audit. See
[the current findings index](../CURRENT-FINDINGS.md) for remaining unknowns.

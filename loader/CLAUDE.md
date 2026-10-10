# Loader guidance for Claude Code

**RTEMS extension (2026-10-11):** [cooperative RTEMS + lwIP](../rtems/README.md) uses a separate RIO1 transport and a larger, explicitly bounded private workspace inside the established staging allocation. The original scalar/BIO1/Tetris layouts remain unchanged. See the RTEMS guide for the correct module, memory map and host-routing commands.


**Current index (2026-10-11): [findings, evidence and unresolved questions](../CURRENT-FINDINGS.md).** Earlier milestone notes below retain their historical context.

**T4 complete (2026-10-10): [play Tetris over SSH](../TETRIS-TERMINAL.md).** The terminal client passed a 30-minute real-SSH test: 35,846 native-matching frames, 68 restarts, 19.91 Hz. Quit, Ctrl-C, connection loss/reconnect and resize cleanup passed. Use `ssh -t mit@192.168.2.75 /home/mit/i960-tetris-t4/play.sh`. Full RAM restored, module unloaded; no reboot or flash.


**T5 complete (2026-10-10): [persistent BIO1 sessions](../PERSISTENT-SESSION.md).** 1,000 frames matched native output at 41.1 ms median; a separate 400-frame run sustained 20 Hz. Process-kill/ownership cleanup and full final RAM restoration passed. `host/session/` keeps paired code/payload checks every frame and full staging audits every 32 frames and close. The subsequently completed T4 terminal client uses this transport; no reboot or flash.


**T3 complete (2026-10-10): [long Tetris hardware replay](../TETRIS-REPLAY.md).** 1,000-call main replay plus 64 repeat calls matched native state/frame bytes; all RAM restored and probes unloaded. Median full CLI latency 306 ms (~3.26 updates/s), payload-command interval ~6.18 ms. This baseline motivated the now-completed T5 session optimization; T4 terminal play is now complete; see the latest milestone above. No reboot or flash.

**T2 complete (2026-10-10): [bounded Tetris steps](../TETRIS-STEP.md) run on the card.** Explicit 240-byte state, 20-tick bound, 24×80 rendering; 1,024 native/interpreted transitions agree, and nine live transactions match the native reference byte for byte. RAM restored; no reboot/flash. T3 replay, T5 persistent sessions and T4 terminal play subsequently passed.

**T1 complete (2026-10-10): [bounded text/framebuffer I/O](../BUFFER-IO.md) is hardware validated.** BIO1 supports 4 KiB input / 8 KiB output; live text, 24×80 frame, capacity rejection and repeat/scalar regression passed with RAM restored. T2 subsequently converted the blocking game into hardware-tested returning steps.

**Planned next work:** [Tetris with host console](../TETRIS-ON-CARD-PLAN.md), then [RTEMS with host-routed networking](../RTEMS-HOST-NETWORK-PLAN.md). Tetris T1–T5 are complete; RTEMS remains planned. RTEMS needs a historical i960/toolchain audit and independent transport before firmware takeover.

**Latest hardware milestone (2026-10-10): [runtime software loader](../SOFTWARE-LOADER.md) works after PC startup.** Three live executions (two C programs) passed without reboot or another flash write. Use `host/loadrun/` and `loader/runtime/` from the repository root; earlier internal-RAM and pre-programming plans below are historical. Supports cooperative returning functions up to 64 KiB, with one argument and a 32-bit result. RAM restored and module unloaded after each run. Recovery remains untested.


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


Latest: [STAGING-REHEARSAL.md](../STAGING-REHEARSAL.md) records a successful
full-image RAM staging rehearsal. Candidate and restored-stock hashes matched;
probe unloaded. Flash programming and the new handler remain untested. Next
resolve programming CPU cache visibility, updater inputs, handler lifetime and
fresh physical readback. Recovery testing is excluded by the user.

Current live boundary: [ROM-FETCH-LIVE.md](../ROM-FETCH-LIVE.md) documents
confirmed RAM command-table dispatch via wrapped `0x21` and a successful
post-startup call to a stock flash `RET` at FEFB022C. The earlier FEFC8208
timeout addressed unrelated image bytes. The exact test restored all RAM and
unloaded cleanly. The new FEFE001C handler remains unflashed and unexecuted;
no recovery check was performed.

Step 4: [ROM-HANDLER-STEP4.md](../ROM-HANDLER-STEP4.md) adds an offline
MIMG wrapper for `romhook/` and verifies the live stock opcode-`0x6F` table
preimage through a fixed read-only probe. ROM instruction fetch after stock
EBCR setup, table-write visibility, update-time handler lifetime and recovery
are still unproven. Do not treat the wrapper as flash-ready.

Current step-3 direction: [ROM-HANDLER-STEP3.md](../ROM-HANDLER-STEP3.md) and
`romhook/`. PING is now placed in the verified FEFE001C flash slot, avoiding
unowned C0120000 and the stock staging block, which stock error/program paths
can free. The new raw image is offline only; do not flash until the documented
instruction-fetch, recovery and programming gates are resolved.

Latest: [DRAM-HOOK-AUDIT.md](../DRAM-HOOK-AUDIT.md) verified startup order,
allocator lower bound and a live zero snapshot at C0120000. None establishes
exclusive lifetime ownership. Do not flash the `stockhook/` candidate; find
firmware-owned handler storage before rebuilding it.

Current offline candidate: [STOCK-PRESERVING-HOOK.md](../STOCK-PRESERVING-HOOK.md). `stockhook/` contains the pinned opcode-0x6F PING boot hook, raw-image builder and tests. It copies the handler to candidate DRAM C0120000 and resumes original firmware entry; exclusive DRAM ownership is unresolved. Do not treat its raw image as flash-ready.

Historical execution analysis: [LIVE-EXECUTION-HANDOFF.md](../LIVE-EXECUTION-HANDOFF.md) missed wrapped 32-bit staging offsets. The later live probe in ROM-FETCH-LIVE.md established a RAM callback handoff.

Latest: [RAM-WRITE-VERIFIED.md](../RAM-WRITE-VERIFIED.md). Fixed 16-byte scratch upload/readback/restoration passed at C0FAC010 in the extra staging allocation block. All 22 commands clean; original 64 bytes restored, probe removed. No execution/recovery/flash.

Latest: [RUNTIME-READ-VERIFIED.md](../RUNTIME-READ-VERIFIED.md). Paired live reads verified entry bytes, board C0110780, alias C1000000 and 512 KiB callbacks. Hardened exact read allowlist passed; no upload/execution/recovery/flash.

Latest: [STAGING-POINTER-VERIFIED.md](../STAGING-POINTER-VERIFIED.md). Live paired four-byte reads confirmed C0F2C000 at C0112A70. Fixed-purpose read gate only; no upload, execution, recovery entry or flash. Probe removed cleanly.

Allocator derivation: [STAGING-ALLOCATION.md](../STAGING-ALLOCATION.md). Enquiry2 plus the traced allocator predicted C0F2C000; [STAGING-POINTER-VERIFIED.md](../STAGING-POINTER-VERIFIED.md) later confirmed it by direct read. The normal harness still rejects out-of-window offsets.

Latest: [SSH recovery-entry investigation](../SSH-RECOVERY-ENTRY.md) and [serial preparation](../SERIAL-RECOVERY-SETUP.md). Physical access is available; serial comes later. Read-only SSH preflight passed; RAM-offset lead remains unproven and no recovery transition was attempted.

Latest: [BOOT-RECOVERY.md](../BOOT-RECOVERY.md) establishes an embedded recovery monitor (PCI 1069:0011) and partial vendor validation. Entry/restoration remain untested; continue over SSH without forcing a flash fault.

Latest programming audit: [PROGRAMMING-RECOVERY.md](../PROGRAMMING-RECOVERY.md). The matching 512 KiB route uses 2B/1 and rewrites the lower 496 KiB; 22 returns an error on this route. An offline experimental MIMG package is archived, but vendor acceptance and recovery remain unverified.

Experimental successor: [postinit/README.md](postinit/README.md) and [../POSTINIT-LOADER.md](../POSTINIT-LOADER.md). The POSTINIT_PROFILE uses external DRAM; the legacy default remains data-only. Prototype is offline, not hardware validated.

> **2026-10-10 architecture correction:** Intel i960 Rx manual §4.1 forbids
> instruction fetch from internal data RAM (0x000..0x3ff). The hello-at-0x200 /
> GO milestone described below is invalid on hardware. Current C tests check
> software behavior only. See [PROJECT-REVIEW.md](../PROJECT-REVIEW.md), item 12.
> Executable payloads need verified external memory; code has not yet been fixed.

Read README.md, PROTOCOL.md, and REVIEW.md before editing this subproject. They
record the 2026-10-10 review, implemented fixes, validation, and unresolved hardware
assumptions. The root CLAUDE.md points here for discoverability.

- Run `make -C loader test` from the repository root after software changes.
  Tests compile and exercise the actual C sender and firmware dispatcher.
- Protocol constants and address policy belong in mu.h. Keep sender, dispatcher,
  tests, README, and PROTOCOL.md consistent when changing the contract.
- Never reset the host sequence to zero without synchronization. Never accept a
  matching old acknowledgment or retry an unacknowledged WRITE automatically.
- Keep OMR0's HANDOFF acknowledgment stable. The demo's execution marker belongs
  in OMR1. Matching source builds are required; old binaries are incompatible.
- Payload RAM is `[0x200,0x400)`. Lower RAM is reserved. Do not widen the range to
  DRAM without verified board initialization/address evidence and revised tests.
- Register access must stay explicit and must not overwrite protocol registers.
  Do not fabricate DRAM timing values or treat the allowed policy window as a
  verified register map.
- Firmware has no data/BSS initialization. Preserve linker/image gates. Inspect
  target disassembly and frame usage whenever target code changes.
- `make all check` and `make image STOCK=...` need the real i960 toolchain. Local
  native test success does not establish hardware safety or target compilation.
- No flashing, remote box access, or hardware bring-up has been performed in this
  implementation session. Record measured results in REVIEW.md. Follow the
  existing backup requirement in ../REFLASH.md before flash replacement.
- Linux PCI ownership checks and advisory locking coordinate loadctl instances;
  they do not prevent unrelated tools or concurrent driver binding.

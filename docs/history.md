# Historical documents by topic

Milestone documents now live in topic directories. Root aliases were removed
after updating live navigation and artifact index links. Start
with [reproduction](reproduce.md) for the current route; these reports retain
their historical results, including superseded plans and failed approaches.

## Firmware, dump and programming

- [DAC960PG x86 BIOS (option ROM) analysis](firmware/BIOS-ANALYSIS.md)
- [Preserved boot-block recovery service — 2026-10-10](firmware/BOOT-RECOVERY.md)
- [In-system firmware dump attempt — 2026-10-10](firmware/DUMP-ATTEMPT.md)
- [Matching-version reference found — 2026-10-10](firmware/FIRMWARE-40729.md)
- [Firmware handler analysis — 2026-10-10](firmware/FIRMWARE-HANDLERS.md)
- [Official DAC960PG firmware package (found + archived on the box)](firmware/FIRMWARE-PACKAGE.md)
- [Patched firmware programmed and boot-validated — 2026-10-10](firmware/FIRMWARE-PROGRAMMED.md)
- [In-system firmware access via the DAC960 mailbox (feasibility + map)](firmware/FIRMWARE-PROTOCOL.md)
- [DAC960FL.EXE — the DOS flash utility (decoded) + the MIMG image format](firmware/FLASHER.md)
- [Forcing i960RP Mode 0 on the Mylex DAC960PG — hardware-mod manual](firmware/MODE0.md)
- [One-shot programming harness — 2026-10-10](firmware/ONE-SHOT-PROGRAMMING.md)
- [Programming preflight and live CPU staging test — 2026-10-10](firmware/PROGRAMMING-PREFLIGHT.md)
- [Programming-path audit and offline update package — 2026-10-10](firmware/PROGRAMMING-RECOVERY.md)
- [Reflashing the DAC960PG boot flash to run your own i960 code](firmware/REFLASH.md)
- [Serial preparation for DAC960PG recovery](firmware/SERIAL-RECOVERY-SETUP.md)
- [In-system firmware recovery — 2026-10-10](firmware/SNAPSHOT-RECOVERY.md)
- [SSH-only recovery-entry investigation — 2026-10-10](firmware/SSH-RECOVERY-ENTRY.md)
- [Vendor read-path reconstruction and live result — 2026-10-10](firmware/VENDOR-READ-PATH.md)

## RAM, hooks and software execution

- [T1: returning text and framebuffer buffers — hardware validated](loader/BUFFER-IO.md)
- [Memory initialization findings from remote firmware analysis](loader/DRAM-ANALYSIS.md)
- [Opcode 0x6F handler DRAM audit — 2026-10-10](loader/DRAM-HOOK-AUDIT.md)
- [Live RAM execution handoff — 2026-10-10](loader/LIVE-EXECUTION-HANDOFF.md)
- [Next step toward live execution — 2026-10-10](loader/LIVE-TEST-PREFLIGHT.md)
- [T5 persistent session — hardware validated 2026-10-10](loader/PERSISTENT-SESSION.md)
- [Firmware patch prototype — 2026-10-10](loader/POSTINIT-LOADER.md)
- [Reversible live RAM upload verified — 2026-10-10](loader/RAM-WRITE-VERIFIED.md)
- [Live RAM dispatch and post-startup flash fetch — 2026-10-10](loader/ROM-FETCH-LIVE.md)
- [Step 3: ROM-resident command handler — 2026-10-10](loader/ROM-HANDLER-STEP3.md)
- [Step 4: update wrapper and live dispatch preflight — 2026-10-10](loader/ROM-HANDLER-STEP4.md)
- [Live firmware and board-descriptor reads — 2026-10-10](loader/RUNTIME-READ-VERIFIED.md)
- [Runtime software loader — hardware validated 2026-10-10](loader/SOFTWARE-LOADER.md)
- [Staging allocation located by geometry — 2026-10-10](loader/STAGING-ALLOCATION.md)
- [Live staging-pointer verification — 2026-10-10](loader/STAGING-POINTER-VERIFIED.md)
- [Live staging rehearsal — 2026-10-10](loader/STAGING-REHEARSAL.md)
- [Stock firmware command hook — offline candidate, 2026-10-10](loader/STOCK-PRESERVING-HOOK.md)

## Applications and operating system

- [Games on the Mylex: CHIP-8, framebuffer, raycaster, Doom](games/GAME-PROGRESSION.md)
- [RTEMS and host networking: roadmap entry point](rtems/RTEMS-HOST-NETWORK-PLAN.md)
- [Preemptive RTEMS and DMA networking plan](rtems/RTEMS-PREEMPTION-DMA-PLAN.md)
- [Plan: Tetris on the card, terminal on the host](games/TETRIS-ON-CARD-PLAN.md)
- [T3: long hardware replay and latency — passed](games/TETRIS-REPLAY.md)
- [T2: bounded Tetris state/update/render — implemented and tested](games/TETRIS-STEP.md)
- [T4 — play Tetris on the card over SSH (validated 2026-10-10)](games/TETRIS-TERMINAL.md)

## Project context

- [Current findings and evidence — 2026-10-13](../CURRENT-FINDINGS.md)
- [Integrated plan: loader memory, RTEMS and remaining gaps](rtems/DEVELOPMENT-PLAN.md)
- [i960 / Mylex DAC960PG — consolidated technical findings](../FINDINGS.md)
- [i960 Project — Execution Manual (handoff for next session)](project/MANUAL.md)
- [Project review: in-system firmware dump](project/PROJECT-REVIEW.md)
- [Session handoff — i960 project (context for a future session)](project/SESSION.md)
- [Teaching a dead RAID controller to run Tetris — a field report](../STORY.md)
- [Repository guidance for Claude Code](../CLAUDE.md)

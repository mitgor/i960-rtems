# Research and evidence map

These experiments remain useful even when they are not the current deployment.
Read each report's observed result and limitations; “next” in an old report is
not today's backlog. [Current findings](../CURRENT-FINDINGS.md) and dated
acceptance reports take precedence.

## Stock firmware and our code together

- [Reset mode 0 investigation](firmware/MODE0.md): original ambition and actual boot constraints.
- [Postinit loader](loader/POSTINIT-LOADER.md), [stock-preserving hook](loader/STOCK-PRESERVING-HOOK.md), [DRAM hook audit](loader/DRAM-HOOK-AUDIT.md): candidate execution paths and memory-ownership limits.
- [Live execution handoff](loader/LIVE-EXECUTION-HANDOFF.md), [flash fetch](loader/ROM-FETCH-LIVE.md), [ROM handler steps 3](loader/ROM-HANDLER-STEP3.md) and [4](loader/ROM-HANDLER-STEP4.md): RAM dispatch and post-startup flash execution proofs.
- [Programmed hook](firmware/FIRMWARE-PROGRAMMED.md) and [RAM runtime](loader/SOFTWARE-LOADER.md): accepted path to applications after boot.
- [Autonomous RTEMS](../artifacts/rtems-web-autonomous-20261011/README.md): timer-driven RTEMS while preserving the stock service path.
- [Resident RTEMS](../artifacts/notes/rtems-residentnet-20261011.md): later owned execution, distinct from firmware coexistence.

## Memory, interrupts and networking

- [Integrated early plan](rtems/DEVELOPMENT-PLAN.md), [preemption and DMA plan](rtems/RTEMS-PREEMPTION-DMA-PLAN.md).
- [Large RAM](../artifacts/notes/rtems-large-ram-20261012.md), [resident uploads](../artifacts/notes/rtems-resident-upload-20261012.md), [segmented loader](../artifacts/notes/segmented-loader-20261012.md).
- [DMA research](../artifacts/dma-research-20261011): preserve the Mylex↔host-RAM↔NIC work and direct-device questions; it is not an accepted direct-NIC driver.
- [Recovery entry](firmware/SSH-RECOVERY-ENTRY.md), [serial setup](firmware/SERIAL-RECOVERY-SETUP.md), [programming recovery](firmware/PROGRAMMING-RECOVERY.md): hypotheses and boundaries, not a recovery acceptance claim.

## Doom progression

| Stage | Preserved report |
| --- | --- |
| Engine/toolchain and RAM budget | [M1](../artifacts/doom-m1-20261011/README.md) |
| Deterministic native reference | [determinism](../artifacts/notes/doom-determinism-20261012.md) |
| Runtime/libc, shared ownership | [runtime](../artifacts/notes/doom-runtime-20261012.md), [shared arena](../artifacts/notes/doom-shared-20261012.md) |
| Relocation, entry and lifetime | [relocation](../artifacts/notes/doom-relocate-20261012.md), [entry](../artifacts/notes/doom-entry-20261012.md) |
| Host WAD batching | [batch](../artifacts/notes/doom-batch-20261012.md) |
| Startup and checkpoint localization | [startup](../artifacts/notes/doom-startup-20261013.md), [checkpoints](../artifacts/notes/doom-checkpoints-20261013.md), [height](../artifacts/notes/doom-height-20261013.md) |
| Comparison/compiler workaround | [side fix](../artifacts/notes/doom-sidefix-20261013.md), [ACK follow-up](../artifacts/notes/doom-sidefix-ack-20261013.md) |
| Global shutdown and replay | [shutdown](../artifacts/notes/doom-shutdown-20261013.md) |
| Verified visible browser frames | [visible](../artifacts/notes/doom-visible-20261013.md) |

The raycaster's [project guide](../game/raycaster/README.md) links its transport
and queue experiments. Keep those results for future optimization, while the
current user priority is interactive Doom rather than another isolated benchmark.

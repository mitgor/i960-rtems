# AcceleRAID 160: six-hour offline runs toward a minimum native RTEMS diagnostic

Started 2026-11-16, Kyiv time. Work proceeds without per-step approval while it uses saved images, local builds, source, and the exploratory emulator/QEMU model. Each run is a **maximum six-hour work block**, not a claim that six hours have elapsed. Start the next block automatically if useful offline work remains; stop when the next decisive experiment requires the remote PC, external programmer, or physical instrumentation. No remote contact, card programming, or live-card register writes are part of these runs.

## Run 1 — diagnostic image and evidence package

| Track | Owner | Deliverable | Acceptance |
| --- | --- | --- | --- |
| Early firmware | `diag_rom` | A second-spare-specific minimum RTEMS image with stage-two, RTEMS entry/scheduler and bounded host-progress markers; SCSI slot 4 stays unanswered. | Direct emulator trace of ordered markers and failure states; malformed mailbox/ring negative; image diff confined to intended firmware region with descriptor and stock reset/x86 ROM preserved. |
| Reproducibility and recovery | `repro_gate` | One-command local rebuild/check where possible, exact tool/source/image hashes, candidate provenance, per-card stock recovery and programmer checklist. | Fresh output directory, pinned inputs, machine-readable PASS/FAIL receipt; no candidate marked flash-ready. |
| Return-to-hardware kit | `remote_kit` | Read-only inventory and optional guarded two-read kit for stock second spare, plus concise operator order for HP settings and first-spare external programmer reads. | Local tests and fake-sysfs dry run; explicit BDF/card/boot-ID and stop conditions; no live execution. |
| Integration | Architect | Compare all artifacts and update the hardware decision record. | Reproduce key gates, resolve conflicting assumptions, state the first remote-only observation needed. |

## Run 2 — conditional offline falsification

If Run 1 finds a material local gap, use another block of at most six hours to repair it and rerun only the affected checks. Priorities are (1) reset-to-entry and first host-visible marker ordering, (2) negative controls for readiness and DMA bounds, and (3) toolchain/image reproducibility. Do not spend this block inventing a QLogic ISP response to the slot-4 INQUIRY. The [stock forensic receipt](../artifacts/current/accele160-stock-next-static-20261116/slot4-isp-boundary-receipt.json) shows a posted request with no modeled response, so the `myrs` probe cannot be completed faithfully with current evidence.

## Stop and handoff

Stop offline work when the diagnostic candidate, recovery base and read-only collector are reproducible and any remaining uncertainty needs a physical observation. The first requested remote session begins with the known-booting stock configuration, HP F10 setting photos and host PCI inventory; optional guarded flash reads follow only if their pinned modules and identity checks pass. The first spare's programmed chip is read twice externally before any restore. A physical test of any new candidate is a separate decision because the original native spare stopped the HP PC before beep. See the [pre-beep audit](hardware/ACCELE160-POST-FAILURE-AUDIT.md).

## Current state

Run 1 completed within its six-hour timebox. The [passive and service package receipts](../artifacts/current/accele160-minimal-diagnostic-package-20261116/README.md) pass byte-for-byte reconstruction and same-card identity checks; the [direct marker gate](../artifacts/current/accele160-minimal-diagnostic-20261116/direct-emulator-v3.json) observes `SGT2` → `ENT0` → `ENT1` → RTEMS/PASS for both images. The [service/control Debian pair](../artifacts/current/accele160-minimal-diagnostic-20261116/coupled-pair-receipt.json) PASS: all four stock-matched output/status pairs are identical, and both stop at the unanswered slot-4 ISP INQUIRY. The [service readiness negative](../artifacts/current/accele160-minimal-diagnostic-20261116/service-readiness-negative.txt) confirms that markers did not bypass modeled host PCI readiness. The [offline release receipt](../artifacts/current/accele160-minimal-diagnostic-package-20261116/release-offline-gate.json) and [return-to-hardware kit](../artifacts/current/accele160-offline-return-kit-20261116/README.md) pass. The remaining questions require physical POST/entry evidence, stock-card host inventory or the first-spare programmer repeat; Run 2 was not started because it would repeat the same model assumptions without narrowing those questions.

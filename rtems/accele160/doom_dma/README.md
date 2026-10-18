# AcceleRAID Doom: direct ping-pong DMA qualification

**Persistent play is now a separate build mode:** follow the
[one-command guide](../../../game/doom/play/accele160/README.md) and
[1,058-frame acceptance](../../../artifacts/current/doom-persistent-20261018/README.md).
`DOOM_PERSISTENT=1` removes the 32-frame/global play limit in favor of the
owned host heartbeat and graceful engine STOP. The default build and the
legacy `run_live32.sh` path below remain bounded.

This isolated subproject ports the old DAC960PG optimized engine and direct
presentation to AcceleRAID 160 `0000:37:09.1`. The old card stays unbound.
The original mode is a bounded 32-frame acceptance harness. See its evidence in
[accele160-doom-dma-20261017](../../../artifacts/current/accele160-doom-dma-20261017/README.md).

## Ownership and transport

The admitted engine owns two contiguous 64 KiB render slots. Channel 0 copies
a completed slot directly into one of two coherent host buffers, then a second
descriptor writes an epoch/generation/source completion marker. Channel 1 and
2 register snapshots must remain unchanged. Source reuse requires proven DMA
drain; destination reuse requires the exact host ACK. These are separate
conditions. Preparation, checks and polling run in task context.

`host/accele160/frame_dma` pins two guarded 19-page allocations for the exact
new-card PCI/subsystem identity and existing `myrsread` driver. Each contains
4 KiB prefix, 64 KiB payload, 32-byte marker and 8,160-byte suffix. It starts
no DMA. Its self-reference deliberately prevents unloading until reset,
including after process death, STOP or uncertain completion. Never force-unload
it. A 50-tick DMA deadline quarantines resources; clearing CCR is not an abort.

The first four frames also receive complete independent odd-page PIO captures
and byte comparisons. Every frame retains full coherent-buffer guards, native host FNV,
marker and ownership checks before binary HTTP publication and ACK. Card
transport FNV defaults on; explicitly set `CARD_FNV=off` to remove that one
per-frame pass. It does not disable final-frame/text checks or full audits. The host
uses the identical FNV algorithm in a hash-pinned native helper, tested against
seven Python vectors. Full RTEMS, arena, loader, lower-bank, owner and STOP
audits remain. No firmware write is part of this path.

## Build and bounded test

Use `build.sh RTEMS_BUILD TOOLCHAIN_BIN OUTPUT` with `DOOM_FPS_FRAMES=32`.
`write_manifest.py SOURCE BUILD ENGINE_MANIFEST DMA_MODULE` binds the kernel,
image, engine metadata, descriptor/copy source, engine identity, host validator
and pin module. The wrapper uses qualified-host absolute paths for resident-worker command
modules, RTEMS build and old engine admission. It is a reproducible test
runbook for this host, not a generic installer. The archive supplies the exact
engine/admission and native helper; the old source builder is
`game/doom/runtime/platform/build.py` plus `engine/admit.py`.
The admitted engine and WAD must have the exact manifest
identities; never substitute geometry or hardcoded entry addresses.

On a fresh qualified boot, select the new card explicitly, obtain two guarded
complete READIMAGE reads and leave the old card unbound. `run_live32.sh`
accepts the isolated project/build/output and both readback directories, plus
an optional HTTP port. `CARD_FNV=on|off` selects the per-frame card hash. It deliberately stalls host ACK at generation 8 for
three seconds and verifies the held buffer remains unchanged. The first four
frames are paired with PIO. Compare steady frames 12–31 against the old-card
low-detail profile, and report the inclusive run separately. Low detail is
fixed here only to match that historical benchmark; it is a quality setting,
not a processor-speed claim. Flat planes and half-height are disabled.

After STOP/quiescence, archive the exact sources, binaries and complete
captures before reset. Obtain two further guarded complete flash reads on
the new boot. Native `test_dma.c` and `test_copy.c` exercise actual production
headers under 32-bit ASan/UBSan, including descriptor reuse, peer isolation,
admission rejection, timeout retention, aligned/unaligned copies and protected
tails. Physical DMA acceptance, native tests and firmware audits are separate
gates. Both bounded DMA/hash modes passed physical frame/STOP tests; see the evidence
record for the final flash-audit status. WAD service currently remains 4 KiB scalar; shared request/completion
rings, larger read-ahead and multi-hour persistent-play qualification remain
follow-up work. The separate persistent build and launcher are linked above.

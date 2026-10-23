# Dated card evidence

This directory contains tested batches and rejected attempts. It is an evidence
archive, not a menu of images to flash or launch. Use the source and current
operator instructions linked below, then the named batch's README for its
exact binaries, audits and limitations.

| Current topic | Evidence | Source / operation |
| --- | --- | --- |
| AcceleRAID stock and programmed ROM | [stock dump](accele160-guarded-20261016/README.md), [programmed helper](accele160-flash-candidate-20261016/README.md) | [firmware guide](../../subprojects/firmware/README.md) |
| Reboot-only RAM ownership and RTEMS | [full-bank acceptance](accele160-fullbank-20261017/README.md), [bounded RTEMS](accele160-rtems-20261017/README.md) | [board RTEMS](../../rtems/accele160/README.md) |
| Playable AcceleRAID Doom | [reusable games](doom-rearm-20261018/README.md), [flat planes](accele160-flat-20261018/README.md), [keyboard FIFO](doom-key-fifo-20261018/README.md), [pushed frames](doom-stream-20261018/README.md) | [Doom commands](../../doom_commands.md) |
| CHIP-8 | [repeated card sessions](chip8-stream-20261018/README.md) | [CHIP-8 commands](../../chip8_commands.md) |
| Host routing and mixed services | [card IPv6](accele160-reclaim-ipv6-20261019/README.md), [combined service](accele160-combined-20261019/README.md), [packet DMA](accele160-packet-dma-20261019/README.md) | [host guide](../../host/README.md) |
| Performance options | [cache map](cache-map-20261018/README.md), [renderer](renderer-tune-20261018/README.md), [old-card flat](flat-planes-20261016/README.md), [half-height](half-height-20261016/README.md) | [Doom backlog](../../game/doom/BACKLOG.md) |

The full file list and checksums are in [the artifact inventory](../artifact-inventory.json)
and [SHA256SUMS](../SHA256SUMS). The previous bulk curation is documented in
[the parent index](../README.md) and recoverable from its named Git commit.
Keep full accepted audits and evidence for unresolved failures. Generated
`__pycache__`/`.pyc` files and scratch builds under `/private/tmp` are not
source artifacts. Other tasks may be using scratch directories, so remove
only confirmed disposable copies rather than cleaning all ignored files.

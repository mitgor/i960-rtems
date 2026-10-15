# Bulk host-to-card WAD delivery

The newer [shared WAD ring](wad_ring/README.md) is a separate opt-in path.
Its matched bounded run reduces first-frame loading from 290.09 to 186.57 seconds,
but warm restart regresses from 2.84 to 4.24 seconds. This 4 KiB path remains the
default/fallback; [exact evidence](../../artifacts/wad-ring-20261015/README.md)
includes both profiles with the same binaries and full audits.

This opt-in path is selected by `game/doom/play/run.py --pipeline --wad-dma`.
The DMA-capable resident kernel and matching driver must be rebuilt together.
`--wad-dma` removes WAD payload CRC, as requested. Framebuffer CRC is a separate
choice (`--no-crc`). The previous CRC-checked mailbox WAD transport remains the
comparison/fallback path. Neither engine-image admission nor full system audits
are disabled.

## Ownership and transfer

The existing immutable host WAD snapshot and 4 KiB runtime read limit remain.
The Linux driver allocates one coherent 12 KiB mapping: 4 KiB guard, 4 KiB data,
4 KiB guard. Userspace supplies file offset, length, sequence and bytes, never a
bus address or a card destination. EOF and short blocks are zero-padded.

The RTEMS engine task borrows its output allocation and a separate 12 KiB guarded
staging allocation. IRQ handlers only stage the kernel-provided source address,
queue a generation, expose completion, or acknowledge it. The owning task uses
DMA1 with descriptor command 6 (PCI Memory Read), fixed length 4096, no interrupt
and no dual-address cycle. The hardware contract comes from Intel 80960RP manual
272736-002, section 20.7.9, tables 20-11/20-12. The manual was already retained in
`/tmp/i960-exclusive-research/27273602.pdf`; its SHA-256 is recorded in the older
`artifacts/dma-owned-20261014/manual-sha256.txt`.

Before publishing completion, the task requires an error-free, inactive DMA
engine, consumed next-descriptor pointer, matching current descriptor, zero byte
count, intact descriptor/data guards, bus mastering disabled and the complete
exclusive isolation contract. Scheduled peers may recognize only the current
owned DMA1 descriptor; unrelated engines and reset/arbitration fields retain
strict checks. Frame DMA and WAD DMA execute serially in the same owning task.

The task keeps staging pinned until the host validates the frozen completion and
ACKs that exact generation. Only then may it copy bytes into Doom's borrowed
output allocation and release staging. Teardown masks interrupts and refuses
queued/unacknowledged DMA, closing the late-submit/cancellation race. Timeout,
uncertain completion or guard failure quarantines resources until reboot; a
channel disable alone is never considered an abort proof.

There is no WAD payload checksum on this path. Guards detect boundary damage;
sequence and geometry checks detect protocol misuse. They do not detect an
arbitrary in-bounds changed pixel, texture or level-data byte. Offline evidence
replay compares all submitted source bytes with the pinned WAD, and acceptance
also compares rendered output with the native engine and mailbox run.

## Interface

Ioctl `0xd0204d09` uses 4128 bytes: eight little-endian words and 4096 data bytes.
The header is operation, epoch, sequence, file offset, wanted bytes, WAD bytes,
zero, zero. Operations:

1. Submit one block. The driver checks the frozen live WAD request, fills its
   coherent mapping, stages its private address and queues the sequence.
2. Poll and finish. Payload must be zero. Pending returns EAGAIN; success returns
   the 12-word completion report and acknowledges it. Submit is never retried
   after an uncertain exchange.

Completion: sequence, source bus address, card staging destination, 4096,
CSR, DAR, NDAR, BCR, DCR, poll count, descriptor address, error.
The driver checks DCR=6, report identity/ranges and host guards before ACK.

MU opcode 0x77 indices 1–5 stage address, submit, query phase, read report word,
and ACK. Index 0 retains the legacy fragment protocol. Existing public upload
ioctls cannot inject these indexed requests; only the dedicated checked driver
path supplies them. All mappings remain retained with resident ownership.

After the first bulk submit, only WAD metadata (0x75/0x76) and indexed bulk
control (0x77) exchanges use at most 16 short polls before the existing
50–100 microsecond sleep fallback. The 20,000-iteration and absolute ten-second
limits, masks, doorbell, exact token and request-clear checks are unchanged.
Legacy WAD payload, frame and system-audit commands retain their policy. A
native test exercises the actual generated function, including inactive mode.

## Testing and measurement

Run `test_wad_target.py`, `test_wad_host.py`, and `test_wad_client.py`. These execute
the actual target/driver/client code with modeled hardware, including 25 exchange
failure points, 256 descriptor bit mutations, pending/stale/bounds/padding/owner
checks, timeout/error/guard quarantine, atomic teardown and 22 replay mutations.
The DMA build entry point includes these tests and `test_wad_poll.py` against the generated driver.

`--pipeline --pipeline-test --wad-load-test` runs 52 frames with four exact
mailbox/frame-DMA pairs, all full audits, menu-driven New Game, and STOP/drain.
Add `--wad-dma` for bulk WAD; omit it for the CRC-checked mailbox baseline. Both
runs use the same admitted engine and resident kernel. The frame CRC pattern is
unchanged across runs. The verifier marks its within-run CRC FPS comparison
invalid for this menu/reload profile: those blocks contain different scenes. Reload the same first level, so results describe a warm
restart, not arbitrary later levels or a fully cold new map.

`verify.py` checks full system audits. `verify_play_pipeline.py` checks every
frame, ownership/ACK order, comparisons and controls. `verify_wad.py --wad FILE`
checks bulk source identity, each block, padding, report and completed sequence.
None replaces the others. Keep both successful and preliminary evidence.
Report startup-to-first-frame separately from engine upload, and menu-confirm to
new-level frame separately from steady-state FPS. The browser receives immutable
binary bytes; HTTP receipt is not a browser paint-rate measurement.

Physical results and exact provenance: [dated evidence](../../artifacts/wad-dma-20261014/README.md).
Player instructions: [PLAY.md](../../game/doom/play/PLAY.md).

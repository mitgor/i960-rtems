# AcceleRAID 160 bounded RAM execution

Status, 2026-10-16: **persistent flash and two bounded returning RAM calls passed on the new card.** This proves execution of one pinned 80-byte payload. It is not an RTEMS, web-server or Doom run. The old DAC960PG `0000:37:04.1` stayed unbound and untouched.

## Exact image and command

The previously accepted late-PING image has SHA-256 `e708c1dadbc4813dd378e8ca8c6f0e929cc29064614b9f8a27210e5e2b23d3d0`. The programmed 1 MiB [candidate.bin](candidate.bin) has SHA-256 `1f13799b880d7e3de2c2037c44fff7e78c0a8f3f391cd05df4a67c41f36c4aaf`. It changes 346 bytes relative to late-PING, confined to the copied-loader cave and two checksum fields. The runtime, boot block, late hook and original PING operation are preserved. The [offline receipt](receipt.json), [disassembly](handler.dis) and 16 helper tests pin the image and reject altered inputs. The 412-byte handler has no ELF relocations.

Operation 2 accepts the zero-DMA 64-byte envelope with version 1, operation 2, `I960` signature and nonzero nonce. Its local addresses are fixed. It invalidates the card D-cache, compares all 80 bytes at `c000f900` against its embedded exact payload, invalidates the I-cache, then calls the payload normally. The payload writes four words at `c000f800`; the handler validates them before stock completion. A mismatch goes to stock unsupported completion. No host-supplied address, length or DMA descriptor is dereferenced.

The 80303 PIATVR is 8 KiB aligned; BAR0's upper 4 KiB maps **PIATVR + `0x1000`**. With PIATVR at `c000e000`, the host sees the erased loader page `c000f000..ffff`. [loader-f000-before.bin](loader-f000-before.bin) matched the accepted flash slice `0x46000..0x46fff` byte for byte. The result and code slots were `0xff` before the calls.

## Physical sequence and evidence

On boot `bdc099fb-36ee-4a5b-a9d0-a5983f8590f4`, exact-BDF `myrsread` owned only the new card. A guarded preflight full-flash read matched late-PING. `STOREIMAGE` staged the new image; a separate guarded 1 MiB `READIMAGE` matched it, each with zero residual and unchanged DMA guards. One `FLASHIMAGE` completed in 37.1 seconds, status 0 and residual 0. The software reboot bound stock `myrs` first; a warm `myrsread` rebind failed mailbox initialization with status 2 before any RAM command. A temporary `myrs` blacklist and rebuilt initramfs preceded a physical power cycle. The blacklist remains active at `/etc/modprobe.d/i960-accele160-temporary.conf` to allow exact `myrsread` first bind on future cold boots; remove it when ending new-card development.

On the resulting boot `bee73454-ba41-417b-9c32-ac1f436ee5e6`, `myrsread` initialized the new card. Two independent full selector-9 `READIMAGE` captures each returned status 0, residual 0, guard changes 0 and the exact new-candidate SHA. Valid PING returned status 0; a one-byte-bad signature returned stock status 2. The old card remained unbound.

The purpose-built [RAM session](../../../host/accele160/helper/ram_probe_session.c) stages only the fixed 16-byte result and 80-byte code slots. It saves and compares the whole 4 KiB page, reads back every staged byte, restores PIATVR before command submission, waits at most five seconds for completion, captures the post-call page, restores the slots, compares the full page again, and releases the command companion. On uncertain completion it retains the module and RAM for diagnosis. The [orchestrator](../../../host/accele160/helper/run_ram_probe.py) pins all four input binary hashes, exact card identity/driver, old-card unbound state and two same-boot full-flash readbacks. The exact Linux `6.8.0-138-generic` [kernel companion](ram_probe_command.ko) and [session executable](ram_probe_session) are archived here with their source; their SHA-256 values are `1b98c11c…f4d0899` and `4331140c…61a9`.

Both calls returned command status/residual zero and exact result words `444f4e45,16102671,000001f0,80114670`; both reported full-page restoration, PIATVR `c0000000` and module release. Independent comparison of their post-call page captures found exactly 96 modified bytes, confined to the result and code slots. Both preimages equal the earlier loader snapshot, and both companions unloaded. An independent read-only [final page](live/final-f000.bin) after the second call equals that 4 KiB preimage byte for byte. A further guarded full-flash read after the first call still matched the programmed image with zero residual/guard changes. Compact receipts and 4 KiB captures are under [live/](live/); the redundant 1 MiB live reads remain on the PC at `/home/mit/i960-accele160-ramprobe-20261016/` and are byte-identical to [candidate.bin](candidate.bin). Replay with `python3 host/accele160/helper/verify_live_ram_probe.py artifacts/current/accele160-ramprobe-20261016 artifacts/current/accele160-startup-20261016/probe.bin`; a deliberate byte change outside the two slots is rejected.

A [bounded read-only DRAM survey](../../../docs/hardware/accele160-memory-map.md) sampled five pages twice and restored PIATVR. Four high pages were stable zeros. This observation does not prove that those pages belong to a new runtime.

Further static tracing identified the stock 32 KiB block allocator. Two more
read-only surveys captured its caller table and block-count/owner arrays; both
rounds matched byte for byte. The exact [decoded table](allocator-table.json)
shows 38 free contiguous lower-pool blocks and 47 free contiguous upper-pool
blocks, with stock reservations elsewhere. [Disassembly](allocator-core-6430.dis)
and the [memory-map analysis](../../../docs/hardware/accele160-memory-map.md)
record the call chain and limits. No dedicated allocator probe or RTEMS memory
reservation was issued; the stock image-read path used its usual transient
allocations.

## Next implementation gates

1. Use the decoded stock allocator to reserve and release a small block in a bounded test, checking the entire count/owner table before and after. Then retain an owner-tagged allocation for minimal RTEMS, or build an explicit exclusive handoff for a larger arena. A zero page is not a reservation.
2. Implement bounded chunked upload with per-chunk and whole-image validation, an owned code/data/stack destination, cache handoff, timeout and STOP. Preserve exact-card selection, PING and stock fallback.
3. Port a minimal RTEMS task/clock/STOP image to the new board. Then adapt the host IPv4/IPv6 relay and web service, followed by WAD loading, browser framebuffer delivery and Doom.

Archived minimal RTEMS kernels are roughly 40–315 KiB and Doom needs an 8 MiB arena. They do not fit this 80-byte entry contract. Do not run DAC960PG images or reuse DAC960PG fixed DMA/IRQ addresses on this card.

Source: `host/accele160/helper/{ram_probe_handler.S,ram_probe_handler.ld,audit_ram_probe.py,stage_ram_probe.py,flash_ram_probe.py,ram_probe_command.c,ram_probe_session.c,snapshot_cave.sh,run_ram_probe.py,run_ping_pair.sh}`.

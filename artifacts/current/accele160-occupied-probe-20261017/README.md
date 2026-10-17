# Bounded borrowing of an occupied firmware page

The exact RAM-only image SHA-256
`6bf2a9d170cd404abb13fffc08d562c5f14f19b51e64b4258bdac3d1e16d5dba`
ran twice on the AcceleRAID 160 during boot
`ed14ddb9-6cf2-4dbc-8645-1383eda72c2d`. Its owned operation-13 callback
paused the stock CPU path at priority 31. Before touching data, the card
observed CCR, NDAR and BCR idle on all three DMA channels. It read, changed
and restored four words at `+0x80` on each of two pages: zero upper page
`c0f01000` and nonzero **stock expanded-runtime** page `c0011000`.

Both card reports are `XCL2, c0f01000, 76efddc5, 76efddc5, c0011000,
0df5e76b, 0df5e76b, 0`. The host's full `upper-before/after.bin` pages
match exactly (SHA-256 `ad7facb2586fc6e966c004d7d1d16b024f5805ff7cb47c7a85dabd8b48892ca7`),
as do the full `stock-before/after.bin` pages (SHA-256
`8744a95d48eb4deafc76573c28ebb742eecee33a66ff6711cfae6a0309ab85cf`).
The card verifies DMA idle again after restoration.

Exact STOP ended in 55.561 ms after a stale token remained pending; no-host
timeout ended after 2,000,000 polls in 1,510.372 ms. Both runs restored
firmware SP `c0002100`, RTEMS and entry stacks, loader page, staging and all
512 allocator count/owner words. The two full guarded reads immediately
before this run are in the [preceding acceptance](../accele160-exclusive-probe-20261017/README.md);
two post-run reads again matched firmware SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
The old DAC960PG remained unbound. No flash write occurred; PIATVR and stock
descriptor were idle after cleanup.

Source is in [`rtems/accele160/occupied_probe`](../../../rtems/accele160/occupied_probe/README.md),
the exact host runner and replay in [`host/accele160/occupied_probe`](../../../host/accele160/occupied_probe/README.md).
`python3 host/accele160/occupied_probe/verify_live.py` passes; changing a
card report or one restored stock byte makes it reject.

This proves reversible borrowing of **selected** stock-occupied bytes during
a synchronous exclusive callback. Stock firmware resumes at completion. It
does not establish a persistent 8 MiB arena or permit overwriting firmware
pages needed for boot, recovery, interrupts or the host transport.

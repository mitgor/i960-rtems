# AcceleRAID 160 live memory map and RTEMS gates

**2026-10-17 update:** [New-board RTEMS bounded acceptance](../../artifacts/current/accele160-rtems-20261017/README.md) now proves a 512 KiB stock-owned grant, 15-page RTEMS task image, synchronous software ticks and normal return with full restoration. The chronological 2026-10-16 text below describes earlier observation gates; its statements that no block was allocated or no task ran are superseded. Hardware timer/interrupt ownership and independent STOP remain open.

2026-10-16. This records observations on the new AcceleRAID 160 `0000:37:09.1` after the accepted bounded RAM-call image was programmed. The old DAC960PG `0000:37:04.1` was unbound and untouched. This is an observation map, not a free-memory map.

| Local address | Evidence | Ownership conclusion |
| --- | --- | --- |
| `c0000000..c0000fff` | Boot/reset state and recovery table | Firmware-owned |
| `c0001000..c0001fff` | Default BAR0 translated window; earlier self-restoring 256-byte round trip | No resident grant |
| `c000a000..c000ffff` | Verified 24 KiB loader copied from flash | Firmware-owned; `c000f800` result and `c000f900` code are an exact self-restoring 80-byte test exception only |
| `c0010000..c00b77ab` | Verified expanded runtime; sampled `c0011000` is stable nonzero | Firmware-owned |
| `c00c027c`, `c00c3690`, `c04016a0`, `c043bfc4`, `c048e6f0`, `c04ad650` | Runtime absolute references and stores | Firmware state extends beyond expanded image and 4 MiB |
| `c03852a0..c03856a0`, `c03856a0..c0385aa0` | Stock allocator's 256 block-count and caller-owner words, captured twice | Describes stock's own 32 KiB block claims, not an RTEMS reservation |
| `c04d0000..c05fffff` | 38 contiguous zero-count/zero-owner blocks in stock lower allocation pool | 1,245,184 bytes currently available to stock allocator; may change later |
| `c0618000..c078ffff` | 47 contiguous zero-count/zero-owner blocks in stock upper allocation pool | 1,540,096 bytes currently available to stock allocator; may change later |
| `c0501000`, `c0801000`, `c0c01000`, `c0f01000` | Two read-only 4 KiB snapshots each, two seconds apart, all zero and stable | **Unknown**; zero is not a reservation |
| `fef00000..feffffff` | 1 MiB flash mapping, including recovery/boot block | Never application RAM |

Controller information reports 16 MiB RAM and 8 MiB cache. The observed DRAM addresses lie within the hypothetical `c0000000..c0ffffff` extent, but no contiguous extent, firmware allocator grant or exclusive takeover has been proven. The 80303 BAR0 is only 8 KiB: its first 4 KiB is the Messaging Unit, and its second 4 KiB is translated local memory. PIATVR at PCI config `0x44` is 8 KiB aligned, so BAR offset `0x1000` selects local `PIATVR + 0x1000`. The default PIATVR is `c0000000`. External PCI writes do not snoop the i960 caches; the proven fixed handler invalidates D-cache before reading its payload and I-cache before calling it.

The [survey script](../../host/accele160/startup/survey_dram.sh) requires exact new-card PCI identity, `myrsread` binding, old card unbound and the global card lock. Its successive runs read five, six and seven selected 4 KiB pages respectively in two rounds, check every PIATVR remap, and restore the default after each sample and at exit. Boot ID and per-page SHA-256 hashes are in [live evidence](../../artifacts/current/accele160-ramprobe-20261016/live/dram-survey-0/). Four zero-page SHA-256 values are `ad7facb2586fc6e966c004d7d1d16b024f5805ff7cb47c7a85dabd8b48892ca7`; the runtime sample is `8744a95d48eb4deafc76573c28ebb742eecee33a66ff6711cfae6a0309ab85cf`. PIATVR read back `c0000000` after the survey, and the new driver and old-card states were unchanged.

## Stock allocator trace and live block table

The expanded stock runtime SHA-256 `09e84895…07e3db` contains a concrete
allocation route. The live word at `c04ad650` is `c048b520`; the callback at
`+0xec` is `c0050850`. The image-read callback reaches `c0050ac0`, which
calls `c0066b90` with the requested size and caller ID. That routine calls
`c0066430` with mode 1, an output pointer and the caller ID. The stock release
path `c0051040` calls `c0066fc0`, which checks the allocation through
`c00665b0`. These are disassembly and pointer-table facts; a new call from our
handler has **not** been tested.

The core allocator rounds requests up to 32 KiB, scans its 256 block-count
words at `c03852a0`, writes a caller ID to parallel words at `c03856a0`, and
returns a local address calculated as `c0000000 + block_index × 0x8000`.
Mode 0 searches blocks 152–191; mode 1 searches 192–255. The exact
[live table capture](../../artifacts/current/accele160-ramprobe-20261016/live/dram-survey-2/c0384000-0.bin)
and [pinned decoder](../../host/accele160/startup/analyze_allocator_table.py)
show this stable state across two reads:

| Blocks | Local range | Count / owner | Interpretation |
| --- | --- | --- | --- |
| 0–151 | `c0000000..c04bffff` | 1 / `aa55aa55` | Stock reserved |
| 152–153 | `c04c0000..c04cffff` | 2 / `aacc0001` | Stock allocation |
| 154–191 | `c04d0000..c05fffff` | 0 / 0 | 38 free lower-pool blocks |
| 192–194 | `c0600000..c0617fff` | 1 / `aa55aa55` | Stock reserved |
| 195–241 | `c0618000..c078ffff` | 0 / 0 | 47 free upper-pool blocks |
| 242–255 | `c0790000..c07fffff` | 14 / `e006e6c0` | Stock allocation |

The total stock free count at this instant is 85 blocks, 2,785,280 bytes,
split into two noncontiguous pools. This is enough in principle for a minimal
or IPv6 RTEMS image, but no block has been allocated to our task. The
allocator's 8 MiB request bound does not mean it can satisfy an 8 MiB request;
its largest currently free contiguous run is 47 blocks (1,540,096 bytes).
The reported 16 MiB physical RAM extends beyond this 8 MiB block table; the
upper half's ownership remains unknown. [Disassembly snapshots](../../artifacts/current/accele160-ramprobe-20261016/allocator-core-6430.dis)
and [pointer-page capture](../../artifacts/current/accele160-ramprobe-20261016/live/dram-survey-1/c04ac000-0.bin)
preserve the trace. The next bounded firmware experiment should reserve and
release a small stock allocation, verify its pointer lies in the expected pool,
and compare the entire block table before, during and after. Only then build a
retained, owner-tagged reservation for RTEMS.

The bounded RAM-call experiment is accepted: two exact 80-byte payloads executed and returned normally with full-page restoration, plus paired pre-call and one post-call full-flash audits. It does **not** provide arbitrary upload or long-lived allocation. Existing DAC960PG RTEMS images range from about 40 KiB for a minimal bounded build to 315,108 bytes for the archived IPv6 build; the Doom arena is 8 MiB. A new-board RTEMS port needs these gates in order:

1. Decode stock allocation and cache layout, then obtain an owned arena through a firmware allocator or an explicit exclusive handoff that stops/drains stock RAID work and DMA. Snapshotting zero pages is not sufficient.
2. Add a bounded chunk upload/validation protocol and normally returning call into that arena. Keep full flash, DMA-guard, image, ownership and RAM before/after audits.
3. Port the new board's timer, interrupt context, DMA/PCI transport and STOP semantics. Run a minimal RTEMS task/clock/STOP image before networking.
4. Adapt the host-backed IPv4/IPv6 relay and web service, preserving the old card's network oracles but using new board-specific transport.
5. Only then port Doom's WAD service and framebuffer path, with an independently proven 8 MiB arena and browser frame audits.

Do not infer that an address is free from its contents or reuse old DAC960PG IRQ, DMA, firmware-loader or fixed RAM addresses.

## Stock allocator operation accepted (2026-10-16)

The [allocator-probe artifact](../../artifacts/current/accele160-allocator-20261016/README.md) records a persistently programmed exact image, two same-boot guarded full-flash reads, two bounded stock allocator calls and post-call readback. The fixed 256 KiB mode-1 request returned `c0750000`; the matching stock free call left all 256 count and 256 owner words byte-identical to their preimage. The first harness's whole-page comparison caught two bytes of unrelated firmware state at offset `0xaa0`, beyond the arrays; a guarded cleanup restored its result slot. A corrected second call passed full loader-page restoration, command release and independent replay. This proves transient stock allocation and release, **not** a retained RTEMS grant. The free-run observations above remain the bound for a future owner-tagged allocation. Doom's 8 MiB requirement still exceeds the largest contiguous stock run.

## Retained 512 KiB owner proof (2026-10-16)

The [retained-grant artifact](../../artifacts/current/accele160-retained-20261016/README.md) proves fixed stock allocation at `c0710000..c078ffff` for owner `0x96016004` while a host command completed, followed by a separate stock release command. Exactly 16 previously free blocks carried count 16 and that owner ID during the grant; all 512 metadata words restored after release. Two same-boot guarded full-flash reads preceded the commands, and post-call flash, loader-page and metadata snapshots passed. This establishes 512 KiB *temporary* ownership under stock firmware, not yet a persistent RTEMS process or code upload. BAR0's odd-page aperture is the immediate upload constraint.

A second same-boot experiment wrote and read back 4 KiB at the first owned odd page `c0711000`, restored every byte before release, and repeated full flash, loader-page and allocator metadata audits. This establishes a bounded reversible write into the grant, while even pages remain inaccessible directly through BAR0. The [upload design](accele160-upload-plan.md) uses one owned odd page as staging and a card-side validated copy into indexed even or odd destination pages.

## Card-side even-page copy (2026-10-17)

The [page-copy artifact](../../artifacts/current/accele160-pagecopy-20261016/README.md) records persistent firmware and a fixed 4 KiB copy from host-addressable odd staging page `c078f000` to otherwise inaccessible even page `c0710000` inside the owner-tagged 512 KiB grant. The card computed the expected destination FNV; staging, loader controls and allocator metadata restored, with paired flash and post-call audits. This removes the basic even-page aperture obstacle for a bounded uploader, and indexes 0, 1 and 126 and both bad-hash and out-of-range rejection have passed with full restoration. Do not yet classify the entire grant as an admitted executable image.

## Contiguous digest and owned-code gate (2026-10-17)

The [digest artifact](../../artifacts/current/accele160-digest-20261017/README.md) records two copied contiguous 4 KiB pages under one stock owner and a matching card-computed FNV over the entire 8 KiB image. Wrong expected hash and count 128 returned stock status 2 without modifying the directly readable target. Staging, controls, loader page, allocator metadata and PIATVR restored; guarded full flash matched after all tests. This establishes bounded transfer admission, not yet an executable owned task.

An [exact 80-byte owned-leaf candidate](../../artifacts/current/accele160-ownedexec-20261017/README.md) completed programming but awaits post-reboot flash and live call tests. Do not infer an RTEMS-sized executable arena until that gate passes.

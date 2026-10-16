# AcceleRAID 160 live memory map and RTEMS gates

2026-10-16. This records observations on the new AcceleRAID 160 `0000:37:09.1` after the accepted bounded RAM-call image was programmed. The old DAC960PG `0000:37:04.1` was unbound and untouched. This is an observation map, not a free-memory map.

| Local address | Evidence | Ownership conclusion |
| --- | --- | --- |
| `c0000000..c0000fff` | Boot/reset state and recovery table | Firmware-owned |
| `c0001000..c0001fff` | Default BAR0 translated window; earlier self-restoring 256-byte round trip | No resident grant |
| `c000a000..c000ffff` | Verified 24 KiB loader copied from flash | Firmware-owned; `c000f800` result and `c000f900` code are an exact self-restoring 80-byte test exception only |
| `c0010000..c00b77ab` | Verified expanded runtime; sampled `c0011000` is stable nonzero | Firmware-owned |
| `c00c027c`, `c00c3690`, `c04016a0`, `c043bfc4`, `c048e6f0`, `c04ad650` | Runtime absolute references and stores | Firmware state extends beyond expanded image and 4 MiB |
| `c0501000`, `c0801000`, `c0c01000`, `c0f01000` | Two read-only 4 KiB snapshots each, two seconds apart, all zero and stable | **Unknown**; zero is not a reservation |
| `fef00000..feffffff` | 1 MiB flash mapping, including recovery/boot block | Never application RAM |

Controller information reports 16 MiB RAM and 8 MiB cache. The observed DRAM addresses lie within the hypothetical `c0000000..c0ffffff` extent, but no contiguous extent, firmware allocator grant or exclusive takeover has been proven. The 80303 BAR0 is only 8 KiB: its first 4 KiB is the Messaging Unit, and its second 4 KiB is translated local memory. PIATVR at PCI config `0x44` is 8 KiB aligned, so BAR offset `0x1000` selects local `PIATVR + 0x1000`. The default PIATVR is `c0000000`. External PCI writes do not snoop the i960 caches; the proven fixed handler invalidates D-cache before reading its payload and I-cache before calling it.

The [survey script](../../host/accele160/startup/survey_dram.sh) requires exact new-card PCI identity, `myrsread` binding, old card unbound and the global card lock. It reads only five 4 KiB pages in two rounds, checks every PIATVR remap, and restores the default after each sample and at exit. Boot ID and per-page SHA-256 hashes are in [live evidence](../../artifacts/current/accele160-ramprobe-20261016/live/dram-survey-0/). Four zero-page SHA-256 values are `ad7facb2586fc6e966c004d7d1d16b024f5805ff7cb47c7a85dabd8b48892ca7`; the runtime sample is `8744a95d48eb4deafc76573c28ebb742eecee33a66ff6711cfae6a0309ab85cf`. PIATVR read back `c0000000` after the survey, and the new driver and old-card states were unchanged.

The bounded RAM-call experiment is accepted: two exact 80-byte payloads executed and returned normally with full-page restoration, plus paired pre-call and one post-call full-flash audits. It does **not** provide arbitrary upload or long-lived allocation. Existing DAC960PG RTEMS images range from about 40 KiB for a minimal bounded build to 315,108 bytes for the archived IPv6 build; the Doom arena is 8 MiB. A new-board RTEMS port needs these gates in order:

1. Decode stock allocation and cache layout, then obtain an owned arena through a firmware allocator or an explicit exclusive handoff that stops/drains stock RAID work and DMA. Snapshotting zero pages is not sufficient.
2. Add a bounded chunk upload/validation protocol and normally returning call into that arena. Keep full flash, DMA-guard, image, ownership and RAM before/after audits.
3. Port the new board's timer, interrupt context, DMA/PCI transport and STOP semantics. Run a minimal RTEMS task/clock/STOP image before networking.
4. Adapt the host-backed IPv4/IPv6 relay and web service, preserving the old card's network oracles but using new board-specific transport.
5. Only then port Doom's WAD service and framebuffer path, with an independently proven 8 MiB arena and browser frame audits.

Do not infer that an address is free from its contents or reuse old DAC960PG IRQ, DMA, firmware-loader or fixed RAM addresses.

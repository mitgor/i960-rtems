# New-card timer-1/vector-18 card acceptance — 2026-10-17

On AcceleRAID 160 `0000:37:09.1`, the existing operation-13 firmware admitted
a new three-page RAM image. The old DAC960PG `0000:37:04.1` remained unbound.
No flash command was issued. The unchanged 1 MiB firmware image has SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.

| Batch | Fixed-tick path | STOP path | Host-observed STOP call |
| --- | ---: | ---: | ---: |
| `timer-active-0` | 8 IRQs | stale token ignored, ACK after 13 IRQs | 26.143 ms |
| `timer-active-1` | 8 IRQs | stale token ignored, ACK after 201 IRQs | 176.560 ms |

The longer run sampled ticks 5→201 over host monotonic time, giving **1,253.04
interrupts/s**. This is a host-observed estimate, not a calibrated oscillator
measurement. It is consistent with a 100 MHz card clock divided by eight and
reload 10,000, approximately 1,250/s. Each call returned status/residual
`0/0`; the active image reported successful timer/vector restoration. ISR SP
was `c0711100` in its owned page, entry SP `c0712fc0` in a different owned
page, and firmware SP was `c0002100` before and after. The ISR page changed
68 bytes and its bottom 64 guard bytes remained `0xa5`.

The `timer-preflight-0`, `timer-postflight-0` and `timer-postflight-1`
read-only inventories independently show the same cached vector 18
`0xaaaaaaaa`, occupied F2 vector `0xe0000ff0`, timer-1 mode/count/reload
`0/0/0`, pending clear, IMSK `0x10c7`, IMAP2 `0x00080000`, and unchanged
IMAP0/1. Timer-0 count legitimately moved. All loader-page bytes, staging
source and 512 allocator count/owner records restored; no one-shot module
remained loaded. Four same-boot guarded full flash reads (`before-full` and
each inventory's `postcall-flash`) match the exact firmware, with status,
residual and DMA guard changes all zero.

The exact [source, build, harness and replay](../../../rtems/accele160/timer/README.md)
are tracked. Accepted image SHA-256 is
`09064cdb91661727a6c10ab93a5f149998fb9d9ca6b4e95e071f905be1cc8038`;
the independent rebuild matched it byte-for-byte. Offline replay verifies
the raw command reports, page and allocator boundaries, stack evidence,
pre/post vector observations and full flash data. Altered flash, cached
vector, STOP ACK and owner captures were rejected.

This proves a bounded timer interrupt and reversible vector borrowing while
stock firmware is parked in one command callback. It does not yet clock
RTEMS, preserve stock timer-0 time across longer pauses, support nested
preemption, or guarantee recovery from an ISR/task that stops cooperating.

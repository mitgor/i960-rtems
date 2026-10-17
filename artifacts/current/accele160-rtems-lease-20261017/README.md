# AcceleRAID 160 RTEMS task STOP acceptance — 2026-10-17

The new card at `0000:37:09.1` ran a RAM-only 16-page RTEMS 4.6.6 image
through the already accepted operation-13 firmware. The old DAC960PG at
`0000:37:04.1` stayed unbound. No firmware write occurred. The complete
1 MiB firmware reads before/after the test matched SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`;
the guarded read status, residual and DMA guard changes were all zero.

| RTEMS worker path | Host-observed call | Result | Worker polls |
| --- | ---: | --- | ---: |
| Valid STOP after stale token | 48.829 ms | READY, then exact ACK/nonce/epoch | 9,936 |
| No host STOP | 1,503.149 ms | TIME after fixed budget | 2,000,000 |

Both calls returned operation-13 status/residual `0/0`. The worker SP was
`c0717c20` inside RTEMS workspace. Entry SP was `c071ffc0` in the owned
stack page; its bottom 256 guard bytes remained `0xa5` and 63 bytes changed.
Firmware SP was `c0002100` before and after. The entire loader page and
staging page restored, as did the allocator's 512 count/owner records.
Reserve and release completed, and no one-shot command module remained
loaded. The post-call full flash read matched the pre-call image exactly.

`accept-3/` is the accepted capture, including both task paths, every upload
receipt, whole-card digest, loader/owner/stack snapshots, command statuses,
and the final guarded full flash read. `accept-1/` and `accept-2/` each
contain a same-boot pre-read used by the final run. `accept-0/` through
`accept-2/` also preserve the three bounded failed/decoder attempts and
their guarded recovery results. The first two RTEMS attempts used Init's
default task argument as the worker nonce and therefore rejected STOP at
the task assertion. The third executed STOP successfully, but the host
validator decoded telemetry one word off; its saved card page shows status
`0`, correct ACK and restored firmware SP. All three retained grants were
inspected, released, and followed by a matching full flash read.

The exact [source, build script, image, harness and offline verifier](../../../rtems/accele160/lease/README.md)
are tracked in the RTEMS subproject. The pinned image SHA-256 is
`0eb6e4591739dbf8c46363b74f0c645dd990b5cc139461ac6eb2635ad329263f`;
the accepted build reproduced it byte-for-byte. Offline replay:

```sh
python3 rtems/accele160/lease/verify_live.py artifacts/current/accele160-rtems-lease-20261017
python3 rtems/accele160/lease/test_verify_live.py artifacts/current/accele160-rtems-lease-20261017
```

Replay validates the three same-boot guarded full reads, exact binary and
page digests, STOP/timeout reports, firmware/task/entry stacks, allocator
records and loader restoration. Four modified flash, ACK, SP and owner
captures were rejected. This proves cooperative RTEMS task STOP and clean
normal return. It does not prove timer interrupts, preemption, recovery from
a non-cooperating task, or a resident RTEMS service.

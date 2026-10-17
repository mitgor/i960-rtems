# Exact AcceleRAID 160 host DMA target

`dma_pin.c` is a Linux 6.8 companion for new card `0000:37:09.1` under
`myrsread`. It allocates three coherent pages on that PCI device: a leading
4 KiB guard, a 4 KiB payload window, and a trailing 4 KiB guard. It accepts
only a 32-bit bus address for the payload and never submits a firmware
command. `status` exposes that DMA address; `data.bin` exposes the payload.
The module self-pins until explicit `release`. After `arm`, release requires
`verify`, which checks the exact 256-byte test pattern, untouched remainder
and both guards. The host runner must independently prove card-channel
inactivity and descriptor completion before writing `verify`. A failed or
uncertain transfer retains the allocation and module until recovery.

The passive allocation test on 2026-10-17 returned a 32-bit, 32-byte-aligned
bus address `fff91000`, initial guards zero-changed, and an unchanged
payload. Unarmed release and module unload passed. The first live transfer
used the **wrong card-side DMA register address** (`ff001400`), never fetched
its descriptor and left the runner holding the module and card grant; see
[the transfer record](../../../rtems/accele160/dma_transfer/README.md).
The host module itself did not initiate a transfer or alter the old card.

The corrected card image subsequently completed three 256-byte transfers
through this same exact module: initial HALT, reuse HALT and no-host lease
expiry. Each target passed its 4 KiB front/rear guards, untouched payload
tail and exact byte-pattern check before `verify` and `release`. The host
module never initiates the transaction; the 80303 channel 0 does. The
[exact captures](../../../artifacts/current/accele160-dma-transfer-attempt-20261017/README.md)
include bus addresses, payload bytes and release evidence. A genuinely
stalled DMA transaction has not been injected or drained, so retain the
module on that path.

Build on the test PC with its current kernel headers:

```sh
make -C /lib/modules/$(uname -r)/build M=$PWD modules
```

Do not load it against another BDF or driver. Do not unload it while armed
without a proven drain; a reboot/power cycle is the recovery boundary for
an uncertain transfer.

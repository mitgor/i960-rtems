# Allocator and segmented-loader core — 2026-10-12

Three actual-card cooperative BIO rehearsals passed, with full paired staging
readback/restoration and clean module unload. No flash change or reboot.
The existing cooperative IPv6 HTTP service was stopped for testing, then restored;
`http-check.json` records HTTP 200 and RTEMS content after restoration.

- First: copied RX function returned `b791f3dd` from scalar input.
- Second: copied RX function loaded the separate RW segment's `DATA` word and
  returned `e4f1e4e1`. BSS was zero, prepare took four bounded steps, and the
  arena was 3,728 bytes. Release while execution was pinned failed; confirmed
  completion reclaimed the image and the old handle was rejected.
- Native ASan/UBSan: contiguous 6 MiB allocation, 128-slot exhaustion,
  fragmentation, 10,000 allocation/release operations, stale/generation-exhausted
  handles, pinned cancellation, malformed manifests, CRC corruption, BSS and
  cache-hook failure retention. `make -C loader test` also passed existing tests.

`captures.tar.xz` contains all three exact target binaries/ELFs/disassemblies/maps,
source hash manifests, generated host module/source, full live captures, boot ID
and the final prototype source snapshot. `archive-members.json` hashes every
regular member. `replay.json` records independent local capture verification;
the final target build's source hashes were checked against the working tree.
`initial-sources.tar.xz` preserves the exact first-build input sources as well.
`middle-sources.tar.xz` preserves the second build before the address-overflow
check; the third test repeated the separate-data execution with that check.
Replay with `python3 loader/segmented/verify_card.py captures.tar.xz --output /tmp/replay`
from the repository root, using the archive path in this directory.
The initial link attempt exposed compiler-generated memcpy for structure copying;
explicit byte copying removed that undeclared runtime dependency before any card
execution. No failed hardware run occurred.

Remote workspace: `/home/mit/i960-segmented-20261012`.
Build with `project/loader/segmented/build_card.py --out target`, generate the
module with `project/host/loadrun/build.py --out module`, then `make -C module`.
With production stopped and the card driverless, the final run (with an added arena-address overflow check) was:

```sh
sudo -n python3 project/host/loadrun/loadrun.py target/test.bin \
  --module module/dac960loadrun.ko --output live-final --buffer-io --expect 0
```

These are **core tests, not large-heap resident acceptance**. RTEMS's production
allocator, ownership grants and resident transport were not changed. Large RAM
admission/high-tail protection, bootstrap code placement, libc/task ownership
adapters, host streaming and larger execution tests remain in the
[integration plan](../../loader/segmented/README.md#next-integration-gates).
No new resident networking endurance or IRQ-latency claim is made here.

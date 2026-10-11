# General application heap in validated RAM

The opt-in `--general-heap` resident build uses the actual RTEMS 4.6.6
`_Heap_Initialize`, `_Heap_Allocate` and `_Heap_Free` for a separate application
heap. It requires `--extra-ram --fault-owner --secondary-reset`. The kernel
workspace and task stacks remain in the original upload allocation. RTEMS's
historical `_Heap_Extend` requires a contiguous higher extension, so it cannot
attach this lower, discontiguous range to the existing workspace.

## Layout and contract

| Range | Use |
| --- | --- |
| `c0200000..c0200040` | Lower region guard |
| `c0200040..c022ee40` | 128 × 1,500-byte packet queue |
| `c022ee40..c022ee80` | Queue-end / heap-start guard |
| `c022ee80..c023ffc0` | 69,952-byte application heap |
| `c023ffc0..c0240000` | Upper region guard |

No address outside the previously validated 256 KiB range is newly granted.
Admission still requires the matching board, stopped engines, owned exception
paths, four full RAM patterns, and protected firmware/code/neighbor checks.
Initialization exhausts the heap, frees alternating blocks, verifies coalescing,
and fills/checks a 69,696-byte allocation before workers start.

`resident_malloc`, `resident_calloc`, `resident_realloc`, and `resident_free`
provide general variable-sized allocation; target libc names route to them.
There are at most 64 live allocations, 16-byte user alignment, and 16-byte
redzones on both sides of every allocation. Allocator metadata and alignment
consume additional space. Allocation failure returns null; failed realloc keeps
the original block. Zero-size allocation returns null; realloc to zero frees.
Foreign, interior and duplicate frees are rejected before reaching the legacy
allocator. ISR allocation is refused. Do not use this allocator before admission.

Single-core serialization saves/restores interrupt priority and raises it to 31.
Before allocator entry, bounded walks validate physical blocks (at most 129),
free-list pointers (at most 65), and every live allocation's redzones. Each used
block must match the registry; its saved alignment offset is checked before
`_Heap_Free` can use it to recover a block header. The
registry resides in the original owned BSS. Outer-guard, metadata or allocation
guard failure enters the owned terminal handler without freeing live memory.
The host can inspect the stable record and acknowledge STOP; it cannot resume
stock firmware or unload retained resources. Reboot is required.

This is corruption detection and containment, not memory protection: a task can
write outside its allocation before the next check. NMI/fault paths do not
allocate. Interrupt masking includes calloc/realloc memory work; worst-case
latency still needs measurement. There is no automatic cancellation reclaim:
workers retain allocations across preemption and explicitly verify/free them
at shutdown. Shared allocation ownership still needs an application policy.

## Reproduction

On the Linux build host, with the existing pinned toolchain and RTEMS tree:

```sh
python3 project/rtems/build.py --work scsi-drain --profile residentnet \
  --secondary-reset --fault-owner --extra-ram --general-heap
python3 project/rtems/residentnet/test_general_heap.py \
  --rtems scsi-drain/rtems-4.6.6 --out general-heap-native
```

For a fresh, unowned card session after reboot, build the matching module and
run the resident acceptance harness (this retains resources until another reboot):

```sh
python3 project/rtems/residentnet/build_transport.py \
  --out residentnet-module-heap --payload scsi-drain/residentnet/kernel.bin
make -C residentnet-module-heap
sudo python3 project/rtems/residentnet/live.py \
  --payload scsi-drain/residentnet/kernel.bin \
  --module residentnet-module-heap/dac960auto.ko --output heap-network-new \
  --secondary-reset --fault-owner --extra-ram --general-heap \
  --ticks 36000 --rounds 10 --round-interval 30 --parallel --burst --deadline --drop-data
```

The native harness compiles unmodified RTEMS allocator sources into a
freestanding 32-bit Linux executable; it supplies lock/abort/address shims and
small memory primitives. It checks exhaustion/coalescing, 2,000 simulated worker
iterations, ISR refusal, 32 redzone corruptions, 32 saved-offset mutations and 32 free-list pointer
corruptions. These tests complement, rather than substitute for, the card runs.

`--heap-test 1`, `2`, `3`, and `4` inject outer-guard, allocation suffix, physical
block extent, and saved-alignment-offset corruption respectively after 100
resident ticks. Use
`live_fault.py --kind 4` and `verify_fault.py` for these terminal builds. Keep
them out of production. Terminal record words 48–63 carry HEP1, heap location,
ready/error, allocation/free/live/peak/rejection counters, startup result,
validity, both worker counts, outer-guard mask and injection selector.

Normal heap networking uses RNT6; snapshot words 48–51 carry base, byte count,
allocations and frees. Ownership bit 16 joins the previous four bits, giving
31. Completed workers must leave allocations equal to frees. The 128-slot queue
and raw packet evidence remain independently checked.

The final hardened image passed 36,000 ticks and ten 30-second-spaced concurrent
IPv4/IPv6 UDP/TCP/HTTP rounds, intentional TCP data loss, and a 160-request burst
(129 replies, 31 drops, queue peak 128). All 36,100 allocations were freed at the
autonomous deadline; both task IRQ contexts drained and ownership remained 31.
An earlier image independently passed the same duration before offset hardening.
Four terminal card tests cover the outer guard, allocation suffix, physical
extent and saved offset; their exact per-build evidence is retained.

See [the batch artifacts](../../artifacts/rtems-general-heap-20261011/README.md)
for exact images, physical results and the thirty-step ledger. Default and
cooperative profiles remain available; exclusive images retain resources until
reboot and do not promise RAID/SCSI service or graceful disk flush.

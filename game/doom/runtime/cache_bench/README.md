# Bounded cache/scaling diagnostic

Opt-in `platform/build.py --cache-bench` adds eight fixed-work cases to the
private engine, one per frame, repeated every eight frames. Both boards receive
exactly the same admitted template and relocation list. No renderer option or
cache-enable bit is changed. This is **not a gameplay FPS benchmark**: diagnostic
work is deliberately inserted after renderer profiling and before publication.

Each case executes 1,048,576 iterations/accesses. Cases are register xorshift,
1/4/64 KiB reads, 320-byte-stride reads within 64 KiB, 64 KiB word copy repeated
64 times, word clear repeated 64 times, and 1 KiB reads with 4,096 explicit
whole-D-cache invalidations. The 1 KiB warm and invalidated cases use matching
loop shapes. The last case includes invalidation call overhead and is not an
isolated instruction-latency measurement. Read kernels include indexing
and branches; their rates are not raw SDRAM bandwidth.

Temporary 128 KiB storage comes from the existing owned allocator and is freed
before publication. Source contents, destination contents and both outer guards
are checked outside the timed section. Ownership/STOP is checked on both sides;
interrupts remain enabled throughout the finite workload. Existing frame pins,
DMA guards, full system audits, firmware audits and cleanup remain mandatory.
The 10 ms card clock limits precision; report all repetitions and medians.

The 512-byte trailer at offset 65024 is reserved exclusively for these records;
wall, input and FixedDiv trailers cannot be combined with this mode. Words are
magic `CCB1`, version, generation, case, iterations, elapsed milliseconds,
result, D-cache status before/after, source address, working allocation words,
checks-passed, then DLMCON/LMADR0/LMMR0/LMADR1/LMMR1; the remainder is zero (record version 2). `verify.py` computes an independent Python
result oracle. `test.py` runs the C kernels with sanitizers and negative trailer
tests. The complete frame transport hash protects the trailer like other bytes.

`dcctl 4` reports global enable in bit 0, but enabled alone does not prove a
particular address is cacheable. Cache geometry occupies the upper status
fields. See Intel's [assembler manual, Data Cache Status Word Bits](https://datasheets.chipdb.org/Intel/80960/manuals/48527607.pdf)
and [Jx manual, section 4.5](https://mark-ogden.uk/files/intel/publications/272483-001%20i960%20Jx%20Microprocessor%20Users%20Manual-Sep94.pdf).
Neither actual CPU frequency nor SDRAM timings can be deduced from the enable
bit alone. No clock or memory-controller registers are modified by this probe.

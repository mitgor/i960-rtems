# i960 CPU-to-SDRAM throughput from physical card captures

This is a **CPU workload measurement**, separate from PCI DMA. The accepted
old-card N1 and new-card stock/cached N1–N2 captures ran the same admitted
diagnostic engine on each i960. A timer inside the RTEMS Doom task bracketed
volatile memory loops; initialization, complete source/destination/guard
checks and frame publication occurred outside the timed region. `measure.py`
checks both exact archive hashes, identical engine template/relocations/
manifest, all 120 old and 32+32 new frame records, native result words,
unchanging logical cache maps and effective cacheability. The [raw samples and
rates](results.json) are derived from four repetitions per case in frames
1–32. Full system/frame/WAD/owner/DMA/STOP and paired stock-flash audits were
replayed again from the original archives. No new card command or flash write
was needed: these are **previously captured physical measurements**, analyzed
for the CPU-to-memory question.

Each measured workload transfers 4 MiB of *useful* data: 1,048,576 volatile
32-bit loads for the reads, 64 passes over 64 KiB for copy or clear. The copy
does 4 MiB of source loads **and** 4 MiB of destination stores; its useful
copy rate below counts 4 MiB and its logical aggregate traffic is twice that.
All rates are `4 MiB ÷ median elapsed seconds` and use MiB = 1,048,576 bytes.

| Timed CPU loop | Old PG, cached | New 160, stock map | New 160, private cache map |
| --- | ---: | ---: | ---: |
| Sequential 64 KiB reads | 2.04 MiB/s | 7.02 MiB/s | **7.08 MiB/s** |
| 320-byte stride in 64 KiB | 1.95 MiB/s | 6.78 MiB/s | **6.78 MiB/s** |
| Sequential 64 KiB word copy, useful bytes | 4.04 MiB/s | 7.02 MiB/s | **7.02 MiB/s** |
| Sequential 64 KiB word clear | 6.90 MiB/s | 38.10 MiB/s | **36.36 MiB/s** |

The new-card cached-map medians are **565 ms** read, **590 ms** strided read,
**570 ms** copy and **110 ms** clear. The copy's logical read-plus-write
traffic rate is **14.04 MiB/s**. The old-card medians are 1965, 2050, 990
and 580 ms respectively. The new card's stock/cached 64 KiB rates are within
one 10 ms timer tick of each other. This 64 KiB working set is much larger
than either i960 data cache (old 2 KiB; new 4 KiB), so repeatedly traversing
it does not obtain the warm-read benefit seen with 1 KiB. The new private map
*does* reduce a warm 1 KiB read from 360 to 130 ms and the same Doom
rendering segment from 91.5 to 48 ms; locality therefore matters even though
bulk sweeps remain roughly unchanged.

These rates include CPU instructions for indexing, summing/looping, loads and
stores, RTEMS scheduling and interrupts. They are useful **application-loop
rates**, not isolated SDRAM bus bandwidth, SDRAM timing-register values, or
cycle counts. Write-through stores and cache-missing large reads exercise
the CPU-to-SDRAM path, but logical bytes do not determine exact external bus
transactions. A repeated-page DMA-chain test elsewhere suggested about
95 MB/s of PCI writes, but used a different direction, destination and clock
window; comparing that number directly with these CPU loops would be invalid.
The current Doom frame-DMA captures do not isolate pure DMA transfer time.

The measured asymmetry directs the next performance work: profile BSP/wall,
plane and sprite access patterns under the now-default cache map, then improve
their reuse of small hot sets and avoid repeated broad source sweeps. Pure DMA
bandwidth work alone cannot explain a 48 ms renderer segment. A dedicated
hardware bus probe or cycle counter would be needed to claim peak SDRAM
bandwidth or distinguish CPU instruction throughput from memory wait states.

Reproduce the quantitative report from the accepted archives:

```sh
python3 artifacts/current/cpu-sdram-20261018/measure.py > /tmp/cpu-sdram-results.json
python3 artifacts/current/cache-scaling-20261017/replay.py
python3 artifacts/current/accele160-doom-dma-20261017/verify.py \
  --archive artifacts/current/cache-map-20261018/cache-bench.tar.xz
python3 game/doom/runtime/cache_bench/test.py
```

The replay checks passed, including the original full card audits and 88
native malformed-trailer rejections. The old card remains untouched; the new
card remains bound to read-only `myrsread` on the remote PC.

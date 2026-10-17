# N1 cached-card baseline

The exclusive AcceleRAID 160 Doom build now defaults to the **physically
accepted** private cache map (`DOOM_PRIVATE_CACHE_MAP=1`). Set
`DOOM_PRIVATE_CACHE_MAP=0` explicitly to reproduce the stock-map control.
This default applies to this reboot-owned Doom build, not stock-firmware
coexistence, other cards, or RTEMS generally. The runtime still checks the
incoming and target logical registers, limits LMT1 to the claimed upper 8 MiB,
preserves WAD/control invalidations and ownership checks, and restores the
incoming map after Doom and DMA drain. No flash change is involved.

The [N1 old-card archive](../cache-scaling-20261017/README.md) and [N2
new-card archive](../cache-map-20261018/README.md) contain the exact same
admitted diagnostic engine: SHA-256 `96647128c8f01397c97b141a5f888217a210e7d3e1a52a1d365cd4e4a4483cef`
for its template, with matching relocations and manifest. `compare.py`
independently rechecks all 120 old-card and 32 new-card whole-frame benchmark
records, native workload results, unchanging register maps, and cacheability
of each allocation. Its [JSON](comparison.json) has all four samples per
workload from the matched first 32 generations.

| Diagnostic workload | Old PG, cached | New 160, cached | New speedup |
| --- | ---: | ---: | ---: |
| Integer xorshift | 695 ms | 125 ms | 5.56× |
| Warm 1 KiB read | 700 ms | 130 ms | 5.38× |
| 4 KiB read | 1680 ms | 255 ms | 6.59× |
| 64 KiB read | 1965 ms | 565 ms | 3.48× |
| 320-byte stride | 2050 ms | 590 ms | 3.47× |
| 64 KiB word copy | 990 ms | 570 ms | 1.74× |
| 64 KiB word clear | 580 ms | 110 ms | 5.27× |
| Warm 1 KiB read plus 4096 invalidations | 935 ms | 365 ms | 2.56× |

The old card reports D-cache `0x7221` (2 KiB, global enable) on every one of
its 120 frames. Its enabled LMT0 `c0000002/ff000001` covers the benchmark
allocation `c0a1db20` and the full 16 MiB card RAM region. LMT1 is disabled.
Its 1 KiB loop rises from 700 to 935 ms with forced invalidations, consistent
with effective caching. The new card reports `0x8221` (4 KiB, global enable)
on all 32 cached frames; enabled LMT1 `c0800002/ff800001` covers allocation
`c0f7b850` in the exclusively owned upper bank. Both allocations are thus
cacheable, though the new card has twice the nominal D-cache size. The 4 KiB
workload can benefit from that difference; the benchmark does not isolate CPU
clock frequency or bus bandwidth. Timings include RTEMS scheduling and have
10 ms granularity.

The new-card **gameplay** baseline is the accepted 32-frame low-detail,
card-FNV-off, no-diagnostic run: frames 12–31 reached **16.964 card FPS** and
**17.178 HTTP-observer FPS**. Its same-engine stock-map control reached
9.694 / 9.643 FPS. The +75% card improvement is a short steady window; it
does not establish sustained interactive FPS. Full frame/PIO/HTTP, WAD oracle,
guard/owner/system, stalled-host, STOP and paired post-reset stock-flash
audits passed in the source archives. The old-card diagnostic timings are
**not** an old-card gameplay FPS comparison.

To regenerate the matched comparison, extract the N1 `accepted.tar.xz` to an
old directory and N2 `cache-bench.tar.xz` to a new directory, then run:

```sh
python3 artifacts/current/cache-baseline-20261018/compare.py OLD_DIR NEW_DIR/case
```

Replay the complete original captures with the archived N1 `replay.py` and
the AcceleRAID `verify.py` referenced in their READMEs. This baseline adds no
card command; it rechecks the accepted evidence. The default-build binary
identity check and its exact SHA-256 are recorded in `build-identity.txt`.

# N1: matched cache-state and CPU-memory experiment

On 2026-10-17 the old DAC960PG (`0000:37:04.1`) and new AcceleRAID 160
(`0000:37:09.1`) ran the **same admitted Doom engine bytes**, relocations and
bounded diagnostic workloads. The benchmark is opt-in (`--cache-bench`); it
adds one workload to each of the first 32 frames, so its FPS is not gameplay
FPS. Each case executes 1,048,576 operations/accesses and has four samples.
`comparison.json` holds every duration, result word, register value and
cache-map decode.

| Workload | Old median | New median | New speedup |
| --- | ---: | ---: | ---: |
| Integer xorshift | 695 ms | 130 ms | 5.35× |
| Warm 1 KiB reads | 700 ms | 360 ms | 1.94× |
| 4 KiB reads | 1680 ms | 490 ms | 3.43× |
| 64 KiB reads | 1965 ms | 570 ms | 3.45× |
| 320-byte stride in 64 KiB | 2050 ms | 590 ms | 3.47× |
| Repeated 64 KiB word copy | 990 ms | 570 ms | 1.74× |
| Repeated 64 KiB word clear | 580 ms | 105 ms | 5.52× |
| Warm 1 KiB reads + 4096 invalidations | 935 ms | 365 ms | 2.56× |

Read-only capture shows the new card's D-cache is globally enabled, yet its
logical templates cache only `c0000000–c05fffff`; the Doom allocation
`c0f7b850` is uncached. The old card's enabled template covers its Doom
allocation `c0a1db20`. This explains the weak warm-read/copy scaling despite
strong integer and clear scaling. The new card's 5 ms invalidation difference
is within the 10 ms clock granularity. These are wall times with scheduler and
interrupt effects, not isolated CPU cycles, RAM bandwidth or a measured FPS
gain from changing the cache map. [Register and invalidation audit](AUDIT.md).

The new card completed 32 guarded direct-DMA frames, four full PIO pairs,
independent 32-frame HTTP delivery, exact native WAD startup prefix, held-host
test, full owner/system audits and STOP. The old card completed 120 guarded
frames and clean STOP; system, frame, WAD, profile and drain replayers passed.
Both builds passed native benchmark oracle, malformed-trailer and Doom tests.
Neither run wrote logical cache registers or flash. Both cards were selected
by exact BDF and the other card stayed free. Both new-card guarded pre-reset and post-reset pairs matched the accepted 1 MiB firmware SHA-256 `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`. All four reads returned status/residual/guard changes zero. The post-reset boot ID is `29dd7853-2614-40e9-8666-2b49b6764324`. The old card is unbound; the new card has only the read-only `myrsread` driver bound.

`accepted.tar.xz` is the final compact evidence archive, containing
the exact sources, build manifests and admitted binaries, new/old captures,
full audit records and paired flash reads. Replay with
`python3 artifacts/current/cache-scaling-20261017/replay.py` from the repository
root. The script checks the full new-card oracle, old-card system/frame/WAD/
profile/drain oracles and all matched workload records. Its JSON output is
written beside this README. `build-engine.sh`, `build-cards.sh`, `run-new.sh`
and `run-old.sh` document exact remote build/run commands; the archive records
the accepted bytes, rather than relying on future rebuilds.
The final archive SHA-256 is
`974df5742118518e9e3cab288413ef056cba708a4edd570ffd8ddc810bea7b34`;
replay of that archive passed after packaging.

Next, test a bounded cacheable mapping **only** for the reboot-owned upper
bank, preserving uncached host-written control/WAD pages and all DMA
coherency/ownership checks. Compare the identical engine with cacheable and
uncached private data before predicting gameplay FPS. Do not change SDRAM
timing or ordinary play defaults based on this diagnostic run.

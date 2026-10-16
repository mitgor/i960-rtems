> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Word-copy/clear hardware results — 2026-10-11

**Accepted on the card:** aligned word `memcpy` and `memset` are now the default
for the isolated raycaster build. Five sessions passed **2,105 native-matching
replies**, 65 periodic full-allocation audits, five initial prefix snapshots and
five full RAM restorations/unloads. No flash writes or reboot in this batch.
The production IPv6 page returned HTTP 200 after testing.

[Implementation and bounds](../../rtems/memory/README.md) ·
[Raycaster contract](../../game/raycaster/README.md)

## What changed

The new ordinary-RAM helpers align with byte prefixes, use 32-bit `ld`/`st`
(copy) or `st` (clear), and finish with byte tails. Copy falls back to bytes when
source/destination alignments differ. The alias-qualified word type allows
arbitrary object representations; size-zero and short cases access no extra
bytes. `memmove`, `memcmp`, `strlen`, the renderer, RTEMS core and transport
policies are unchanged. The existing forward `memmove` path calls the new copy;
the measured backward-overlap path remains byte-based.

Only `game/raycaster/build_target.py` selects the new helpers. Other OS profiles
and production autonet are not modified. Word selection is explicit in build
metadata and can be reverted with `--memory byte`. The measured optimized image
adds **160 text bytes**, with unchanged data/BSS and flat extent:

| Build | Text | Data | BSS | Flat bytes |
|---|---:|---:|---:|---:|
| byte | 23,792 | 468 | 71,040 | 202,596 |
| word | 23,952 | 468 | 71,040 | 202,596 |
| correctness checks | 24,832 | 468 | 83,520 | 215,076 |

The byte binary exactly reproduces the previous raycaster SHA256
`47046f511b683911df78a329985efba067836e982c0f42ec1a5d863e8d8242a5`.
Word SHA256: `8a19e5a357d3443721ee835d5fbdfd52ffd61710b339b8be9d74554d947da5e3`.
Check SHA256: `6b04762baea9d4bffcf6e33413ba77517e1a92f12b230939a04c68d75c8376cf`.

## Correctness

ASan/UBSan tests passed on macOS and Linux. Independent byte references check
2,112 copies, 2,112 overlapping/equal moves and 1,056 clears, using all source and
destination offsets 0–7, 33 lengths through 4,097, four fill values, return values,
source preservation and surrounding sentinels. Native-only inaccessible guard
pages check 513 lengths with equal and different alignments at both boundaries.
The six raycaster Python tests and C sanitizer suite also passed on both hosts;
`make -C game/raycaster test` now includes the memory suite.

The separate check image executes those same 5,280 reference/sentinel cases in
264 returning batches, one before each of the first 264 application requests.
A mismatch calls `bounded_fatal` before a successful reply. All 421 replies from
that session match the independent native raycaster. The saved checking source
and injection are verified alongside its binary identity; no checking code is
present in the two timing builds. Check-session maximum recorded transaction:
328.84 ms. Per-buffer guard pages are not available on the card.

During native harness development, forcing the Linux system string header into
the renamed legacy wrapper bound its copy declaration back to system `memcpy`.
ASan correctly rejected its forward-overlap call. Replacing that forced header
with a plain prototype fixed the harness before any hardware run. The target
implementation did not fail any live test. The old compiler emitted real word
instructions without attribute warnings; exact disassembly is preserved.

## Controlled timing comparison

After correctness acceptance, four independent sessions ran in **byte, word,
word, byte** order using the exact same profiling module and 421-request workload.
Each contains 160 full renders, forty 10-column batches, twenty header-only and
twenty framebuffer snapshots, and five repeats at 1/16/64/128 operations for each
benchmark. All four sessions passed native replay and restoration. The checking
session is excluded from all performance figures.

Figures below are medians of the two session medians (or fitted slopes), not
claims of statistical significance for tiny changes. Raw individual results
remain in the JSON reports. Host command timing includes dispatch, polling and
validation; no cycle counter, CPU clock assumption or profiling timer was used.

| Operation | Byte µs | Word µs | Speedup |
|---|---:|---:|---:|
| memcpy 4,096, aligned | 1,357.683 | 411.084 | **3.30×** |
| memcpy 4,096, both offsets +1 | 1,357.457 | 412.332 | **3.29×** |
| memset 4,096 | 861.170 | 185.951 | **4.63×** |
| memmove 4,096, destination +1 overlap | 2,006.896 | 2,006.984 | 1.00× |
| memcmp 4,096, equal buffers | 1,769.711 | 1,769.849 | 1.00× |
| strlen 4,095 | 895.943 | 896.078 | 1.00× |
| RTEMS semaphore roundtrip | 102.061 | 101.515 | approximately unchanged |
| RTEMS software clock tick | 4.895 | 5.173 | small/noisy difference |

Aligned copy rises from approximately 2.88 to **9.50 MiB/s**; clear from 4.54 to
**21.01 MiB/s**, as differential estimates on repeatedly reused buffers. The +1
copy has matching alignments and enters the word loop after three bytes; this
is not a speed claim for mismatched alignments. All fit R² values exceed 0.996.
Tick/sem differences are too small here to attribute to an OS improvement or
regression; those routines were not changed. Different code placement and host
polling remain possible contributors. These are not cold-cache or loaded-ISR
measurements.

| Raycaster measurement | Byte ms | Word ms | Reduction |
|---|---:|---:|---:|
| Full-frame execute interval | 14.191 | 11.969 | **15.65%** |
| Full-frame kernel transaction | 60.309 | 57.952 | **3.91%** |
| Full-frame complete Board.step | 64.997 | 62.573 | **3.73%** |
| Render/publication increment over full snapshot | 7.547 | 6.437 | **14.70%** |
| Full framebuffer snapshot execute | 6.644 | 5.532 | 16.74% |
| Header-only snapshot execute | 5.041 | 5.039 | approximately unchanged |

Full-frame kernel medians were 60.336/60.281 ms for byte and 57.823/58.081 ms for
word, so the effect appeared in both runs. The 2.22 ms execute saving agrees with
two 4,800-byte copies becoming faster: back-to-front publication and front-to-host
reply. Snapshot saves one such copy. The render/publication increment retains
DDA, pixel fill, frame hashing and one copy; it is not isolated ray-math time.
Clear is much faster in its benchmark but is not the main per-frame operation.

Upload plus arming remains about **32.8 ms**; paired staging audit remains about
12.5 ms on full renders. Ordinary reads still total 942,272 bytes, and every
32nd request reads 1,048,576 bytes. No check, audit, memory ownership gate or
framebuffer byte was removed. The smaller improvement in total transaction time
is therefore expected. This batch measures card frame transactions, not a new
browser/compositor FPS result.

## Service and concurrency

Remote workspace: `/home/mit/i960-word-20261011-MeZXbs`.
Boot ID throughout these runs: `3c5b99fb-e6a3-4bab-8df2-fdd16e43b1d9`.
We waited for the parallel monitor tests and HTTP verification, then normally
stopped `http-after-handoff` and verified its full restoration before taking the
exclusive loader lock. That close is preserved in `production-close/`.

After all five sessions, production restarted into `http-after-word-memory`.
The parallel monitor task subsequently performed its final validation and
restarted it into `http-after-handoff-final`. Our first HTTP attempt overlapped
that restart and failed to connect; a subsequent request returned **HTTP 200**.
`service-state.txt` records the final active service and our intermediate
143-step service's clean restoration. No production helper change was deployed,
and no visitor log is included.

## Evidence and reproduction

- `byte/`, `word/`, `check/`: exact binary/ELF/map/symbols/disassembly, build
  metadata and target sources. `hardware_tested: false` is the retained build-time
  flag; the later captures establish acceptance.
- `build-verification.json`: identities, layout, unchanged non-libc sources,
  exact helper substitution and self-test injection verified.
- `dac960rtems.ko`: unchanged module from the original raycaster milestone;
  its source and timestamp-only diff are in `../raycaster-20261011/`.
- `live.tar.gz`: all five full capture directories, original request/reply traces,
  phase timings, audits, preflight/open and close records. Each run has 13 periodic
  full audits and one initial prefix snapshot. Each close checks the full allocation.
- `*-verified.json`, `*-profile.json`, `comparison.json`: replay and reproducible
  timing analyses. `archive-replay.json` records re-extraction and replay of all
  captures; floating analysis results allow 1e-12 relative/absolute tolerance
  for host Python rounding (raw replies remain byte-exact). `live-*.log`, `*-build.log`, `native-*.txt`: execution/build/tests.
- `http-restored.*`, `service-state.txt`: final HTTP and service evidence.

```sh
make -C game/raycaster test
python3 rtems/memory/verify_build.py artifacts/word-memory-20261011
python3 rtems/memory/verify_archive.py artifacts/word-memory-20261011
# Extract live.tar.gz into a fresh directory. For each live-VARIANT run:
python3 game/raycaster/verify_card.py CAPTURE --payload BUILD/kernel.bin \
  --module artifacts/word-memory-20261011/dac960rtems.ko
python3 game/raycaster/profile.py CAPTURE/phases.json
python3 game/raycaster/compare.py \
  --byte artifacts/word-memory-20261011/byte1-profile.json artifacts/word-memory-20261011/byte2-profile.json \
  --word artifacts/word-memory-20261011/word1-profile.json artifacts/word-memory-20261011/word2-profile.json
```

For further work, profile the constituent upload/arming firmware commands first.
Keep any future transfer batching tied to explicit buffer ownership, completion,
backpressure and teardown. Wider/unrolled memory loops can be compared later,
but the measured transport costs now dominate. Adoption by other RTEMS profiles
requires their own regression tests; this acceptance is bounded-session specific.

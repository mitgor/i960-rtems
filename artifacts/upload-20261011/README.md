# The 32 ms upload wait: blocking UART output

## Result

The stock RAM upload method unconditionally prints `\nOff%X Siz%X` through a
blocking UART routine **before DMA**. A narrowly scoped, reversible change of
that format string's first byte to NUL removes most of the measured wait.
No flash change, DMA bypass, command batching or reduced audit is involved.

Fresh baseline → quiet → quiet → baseline runs, each with 421 requests and the
same unchanged target, produced these medians of the two session medians:

| Full-frame metric | Baseline | Quiet upload | Reduction |
|---|---:|---:|---:|
| Three upload completion waits, summed per frame | 32.129 ms | 0.368 ms | 98.85% |
| Request upload phase, including added paired format check | 10.697 ms | 0.575 ms | 94.62% |
| Arming phase | 21.962 ms | 0.577 ms | 97.37% |
| Execute/callback | 11.928 ms | 11.924 ms | 0.03% |
| Table/result verification | 0.614 ms | 0.599 ms | 2.50% |
| Readback/audit | 10.684 ms | 10.493 ms | 1.79% |
| Full kernel transaction | **55.840 ms** | **24.141 ms** | **56.77%** |
| Complete host Board.step | 60.444 ms | 28.924 ms | 52.15% |

The final coarse build, without detailed per-command timing, passed another 421
requests at **23.876 ms** median full-frame kernel time (27.112 ms Board.step).
That single run confirms release behavior; it is not a separately repeated
comparison. No browser FPS or raw PCI bandwidth claim is made. Small differences
in execute/audit phases are not evidence of target CPU or OS acceleration.
The first request retains its original upload/cache handshake cost; render
measurements exclude that reset request. Host scheduling is not controlled.

The final matrix passed **2,105 native-matching replies, 65 periodic full audits,
five initial prefix snapshots and five full restorations/unloads**. Four detailed
sessions reconcile **45,612 commands**. Ten earlier corrected-build smoke sessions
passed another 40 replies and ten restorations. Two exploratory sessions passed
842 replies; a third rejected startup safely. Across all 18 sessions, 2,987 replies
matched and every session restored/unloaded. The rejected request never entered
user code, and is not counted as a successful reply.

## Root-cause evidence

`firmware-uart-trace.txt` byte-checks the saved disassembly against matching vendor
binaries. Bootstrap installs the read/write methods at controller offsets e0/e4
as `c004ce90` and `c004ced0`. The latter references the unique format at `c004cec0`
and calls `c000a2a0` before the transfer helper `c004c010`. The read method has
no corresponding print. Bootstrap copies the formatter/UART region from
`fefc9000` to `c000a000`; the UART routine waits for transmitter readiness for each
character. No guessed baud rate or hardcoded 10 ms firmware sleep is asserted.

The live gate independently verifies paired reads of the controller pointer,
method words, formatter (256 bytes), UART routine (104 bytes), and the format plus
adjacent upload handler (80 bytes). This establishes which method is actually
installed, rather than inferring it solely from a static bootstrap branch.

Removing only this serial output changes the three command waits from about
32 ms to 0.37 ms; restoring the original byte returns the baseline to about
32 ms. Callback and audit costs remain roughly unchanged. This is strong causal
evidence for the dominant UART cost, not merely a correlation with less logging
on the Linux host. Host command logging and the completion poll are unchanged.

## Scope and preservation

[Implementation contract](../../game/raycaster/upload/README.md).
`upload/build.py --quiet` derives the previous optimized validation transport.
It uploads four bytes at exactly `c004cec0`, changing only `0a` to `00` and keeping
`4f 66 66`. No arbitrary write interface is added. Both preimages are hash-pinned
at build time, and all relevant live bytes must match before the write.

Suppression happens after the existing first-STEP cache handshake, with that
maintenance callback still installed. A second invocation invalidates caches
without an intervening PING/table roundtrip. The normal sentinel, runner arm,
user callback and self-disarm then run. User callbacks are never retried.
Subsequent STEPs add two exact 80-byte reads before request submission.

All three ordinary uploads remain, as do the existing 22 reads (24 with the new
format checks), paired payload snapshots, full code/guard comparisons, exact DMA
byte counts, status/tag gates, sequence consumption, timeout and resource-retention
rules. Ordinary paired staging volume is still **942,272 bytes**; every 32nd reply
still reads **1,048,576 bytes**. The new format checks add 160 bytes per ordinary
request. No sampled/checksum-only substitute for any comparison is used.

Before restoration, paired format reads must match either exact original or exact
suppressed bytes, including the neighboring handler. CLOSE writes the original
word, runs the cache/PING checks and compares the original 80 bytes twice before
normal full RAM restoration. `quiet_dirty` participates in both pinning and
removal gates. Unexpected bytes, pending DMA or uncertain user execution cannot
be silently cleaned up and freed. Other firmware diagnostics remain enabled.

## Failure found, retained evidence and correction

The initial candidate suppressed the string in OPEN and added a cache/PING
roundtrip. It passed 421 replies once. On the next session's first STEP, paired
RAM reads showed the cache-callback table word, but four harmless dispatches
returned PING `017e` instead of cache status `017d`. ENODATA was returned before
user execution. The format, full staging image, runner, result and table restored;
normal unload succeeded. No reboot was required.

This establishes stale dispatch visibility, not a complete microarchitectural
explanation. The missing UART traffic had exposed a dependency on the old timing
and cache behavior. Increasing retries or ignoring the wrong status would have
weakened validation. Instead the final implementation preserves the original
startup handshake and suppresses output immediately afterward, with no intervening
PING that could cache the old dispatch again.

`module-quiet-v1/` and `exploratory-*` in the archive preserve the accepted first
run and the rejected second run. The rejection's raw command/status/readbacks and
successful cleanup are in `exploratory-fast-rejected/failure-000001/result.txt`.
Its empty trace proves no successful application reply was recorded. The final
source is qualified by ten repeated open/run/close smoke sessions before the
fresh five-session measurement matrix. Exploratory timings are excluded from
`comparison.json` and `upload-waits.json`.

## Native tests and independent replay

ASan/UBSan passed on macOS and Linux for both detailed and coarse variants:
406 command-boundary failures/timeouts per variant, stale/malformed requests,
six output corruptions, 520 format/handler/formatter/UART byte mutations,
fixed read/write gates, and pending/uncertain cleanup refusal. Mutated format
regions are refused before any restoration write. The simulator also models the
observed cached-PING hazard, explicitly rejects a stale PING despite a matching
RAM table word, and exercises the corrected ordering. This models the observed behavior, not the whole i960.
The inherited exact-count/range tests and native raycaster/memory tests passed.
Fault injection is native; the live rejection above happened naturally.

```sh
python3 game/raycaster/upload/test.py
python3 game/raycaster/upload/verify.py artifacts/upload-20261011
```

Replay verifies payload/module hashes, every successful reply, required captured
full audits, quiet preimages and restoration, exact per-frame command order and
volume, the rejected startup's restoration, and all derived profiles. It
regenerates all three accepted module sources byte for byte; generated `.mod.c`
compiler stubs are archived but excluded from source reproduction. Derived
floating values permit 1e-12 rounding differences; raw bytes compare exactly.

## Artifacts, host and service

- `kernel.bin`: unchanged word-memory payload, SHA256
  `8a19e5a357d3443721ee835d5fbdfd52ffd61710b339b8be9d74554d947da5e3`.
- `module-base/`, `module-quiet/`, `module-release/`: exact loaded modules,
  generated C/header/Makefile archives, mode metadata and Linux disassemblies.
- `module-quiet-v1/`: exact exploratory build, including the startup issue.
- `live.tar.gz`: complete five-run matrix, ten smoke sessions, three exploratory
  sessions and prior production close. Four final detailed runs retain every
  command log. Coarse retains phase rows and periodic/open/close logs.
- `*-verified.json`, `*-quiet.json`, `*-commands.json`, `*-profile.json`,
  `comparison.json`, `upload-waits.json`, `archive-replay.json`: replay/reconciliation.
- `native-*.txt`, `build-*.log`, `batch.log`, `smoke.log`, `live-*.log`: test/build evidence.
- `http-restored.*`, `service-state.txt`: actual public HTTP 200 and service state.
  Visitor logs are not collected.

Workspace: `/home/mit/i960-upload-20261011-FigihP`.
Boot throughout our batch: `8a7b0ba8-1ae4-4480-86e8-81c40e3b0c9a`.
The parallel resident-networking batch finished first. We stopped and verified
`http-after-residentnet`, then restored production autonet into
`http-after-upload`; the Mac received HTTP 200 over global IPv6. No flash write
or reboot was made by this batch.

For an ordinary bounded raycaster session use `upload/build.py --quiet --coarse`.
This remains opt-in and specific to the pinned firmware. Production autonet and
resident RTEMS are unchanged. The remaining frame costs are mainly the roughly
12 ms callback and 10.5 ms full readback/audit. Those need their own measured
optimizations; faster uploads grant no additional RAM or DMA ownership for Doom.

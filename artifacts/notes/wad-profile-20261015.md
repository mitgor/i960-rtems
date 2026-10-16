> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# WAD DMA and software-cost profiling — 2026-10-15

Status: both bounded physical runs and full replay passed. Final cache attribution
is accepted; the first completed run has an explicitly invalid cache trailer.
Public IPv6 HTTP is restored and verified from the Mac (200 / 2,891 bytes).

## Measurement contract

This is an explicit `--wad-profile` build on top of the accepted two-slot WAD
ring. It retains finite descriptors, exact destination loans, complete guard
scans before and after **every** transfer, full descriptor/state/cleanup checks,
the three-second requested paired system/RAM audits, frame comparisons and STOP.
It does not change the PCI mapping, flash, transfer size, cache policy or default.

The exclusive shared heap already owns timer 0. Profiling only reads its TCR0
register at `0xff000304`; it neither reprograms the timer nor reads the
terminal-count-clearing mode register. Unsigned downcounter deltas accumulate
with explicit low/high carry. Nominal frequency is 4,166,700 Hz (the established
bus/8 calibration), not a new oscillator measurement. These are **elapsed-time
brackets including interrupts and preemption**, not isolated task CPU cycles.
An empty bracket gives an instrumentation reference; it is not subtracted.

Nineteen cumulative categories cover WAD calls, frame-DMA barrier, allocation
and loans, staging initialization, release and loan returns, full guards, DMA
start-to-completion, whole transfer, response wait, service/yield, staging copy,
benchmark transfer/hardware/guards, empty bracket, benchmark payload comparison,
response transfer, allocation alone and free alone. Categories overlap: response waits include response DMA;
whole transfers include guards and hardware. Do not sum every column as if they
were independent. Read-only reports are refused while the owner is running,
while staging exists or loans remain. Existing upload command 21 indexes 8–72
read the final 65-word version-2 report after owned STOP.

## Bounded resident-source DMA benchmark

On the first complete 32 KiB WAD payload, the existing host slot stays immutable
until its normal completion. The task repeats **64 host-to-card reads / 2 MiB**
from that same slot into its existing borrowed staging destination. Every read
uses the complete ordinary transfer path and checks all 32 KiB against the
initial copied payload. STOP is checked between repetitions; the existing
finite hardware deadline and quarantine behavior are retained. The benchmark
never writes outside already registered windows and does not use a circular
hardware descriptor chain. Hardware timing excludes guards, allocation, payload
comparison and host refill; checked-transfer timing includes the regular guards
and setup/cleanup but excludes the separate payload comparison. Neither figure
is an end-to-end WAD loading rate or a RAID disk throughput measurement.

The cache exports cumulative runtime-read, cache-fill, miss-copy and hit-copy
elapsed times in a versioned trailer at byte 64960 of the existing frame. These
use the existing **10 ms clock**, so individual tiny copies are quantized;
aggregate figures are attribution estimates. Their counters/bytes and all
unused padding are validated. Pixels and palette remain byte-comparable with
the independent native oracle. A trailer is allowed only for the explicit
profile build; ordinary frames still require zero padding there.

Host timing separately counts successful/pending ioctl durations, elapsed work
inside `serve_locked()` (including serialization and journals), and waiting to
acquire the audit gate. These overlap and exclude time outside service calls;
they must not be added blindly to card timings.

## Build, native validation and initial correction

`build.sh` is the full candidate build; `rebuild.sh` reuses the existing compiled
Doom engine when only the platform/runtime changes; `build-kernel.sh` rebuilds
the kernel/module. The bounded launch script is `run.sh`. Remote workspace:
`/home/mit/i960-wad-profile-20261015`.

Before any game frame, the first physical attempt was stopped because the new
cache trailer had not yet been admitted by the existing presentation validator.
Its pre-engine capture is preserved in `aborted-before-engine.tar.gz`. This is
an aborted attempt, not a passed full run. SHA-256 was checked locally before
normal reboot released the retained module. The corrected validator checks the
explicit schema, counters, clock scale and gap/tail padding; native tests reject
nine malformed/unadvertised trailers. No payload check was weakened.

Native tests exercise the real profiled target with modeled DMA and ASan/UBSan,
including 64 repeats, exact payload comparison, STOP during the benchmark,
corrupted benchmark payload quarantine, counter carry, refused live telemetry,
all guard bytes and descriptor bits, existing timeout behavior and normal reads.
Cache tests cover all three block modes with profiling both off and on. Native
Doom tests preserve repeat pixels, input/STOP and heap drain.


First completed candidate: 146 protected pages, 28,448 bytes of upload helper code,
22,016 bytes of protected engine helper code and 80 bytes of unused mutable
reserve. No protected boundary was widened. Exact candidate identities:

- Kernel `b440fd84cb543c1b6a50118ecfb357cc6cb5abb4c529e7790895c91168bbec94`
- Module `a4a1a928762e2143766f5ffe3d54511f867f447b302f08844377e388d14bc2de`
- Doom image `71fc400d3174e5ff796166dc4a6158f3291ae80ae3aab3f41553b7ec08ec504e`


The first completed capture (`live-profile2`, `card-v1.tar.gz`) passes 100
frames, 89 full paired audits, full WAD replay, native pixel comparison and STOP.
It measures the runtime and resident-source benchmark correctly, but its cache
trailer is **invalid for WAD attribution**: it exposes the unused stdio cache,
and the actual engine cache was compiled without the instrumentation flag.
The zero cache costs in `local-v1-profile.json` must not be interpreted as no
copying. The original decoder/verifier is preserved with that candidate.

The second candidate explicitly profiles the actual engine backend and exports
`doom_wad_backend_stats()`. The platform builder refuses a mismatched engine.
Before physical execution, two complete native 52-frame runs prove deterministic
pixels and nonzero actual WAD counters in every frame. The final verifier also
cross-checks cache calls/bytes against target call counts and every ring request.
This is an instrumentation correction, not a change to the transfer algorithm.
The first archive remains preserved rather than silently replacing its evidence.


Final candidate (version-2 runtime report): 146 protected pages, 28,448 bytes of
upload helper, 22,080 bytes of protected engine helper, 64-byte mutable reserve.

- Kernel `0741a0fc5c71a5b7bc6e64830934dd86615d07ace740b6d0c8c0bc2207356dfa`
- Module `9f3074128d410b348d18911192580e0d0ce9954fc8162c525d4adea4310bfc8e`
- Doom image `a2eb8f504dab0d7cae3bbcf1475b3a01f12e681e94450a064dc6117a821f64e7`

`build2.sh` rebuilds the actual engine with `--wad-profile` and the corresponding
platform, kernel and module. `native-frames2.py` explicitly checks real backend
counters before physical use. `run2.sh` runs the final candidate as
`live-profile3`. `build-kernel2.sh` rebuilds just the runtime/module if needed.

## Reproduce from a fresh checkout

On the qualified Linux host, with the cross compiler installed:

```sh
python3 game/doom/play/build.py --work /home/mit/doom-wad-profile-new \
  --pipeline --pingpong --wad-ring --wad-profile \
  --frame-profile --cpu-profile --no-fnv --direct-frame --low-detail
```

After inspecting actual hardware ownership and normally stopping its current
owner, use the bounded runner:

```sh
sudo python3 game/doom/play/run.py --work /home/mit/doom-wad-profile-new \
  --output /home/mit/doom-wad-profile-capture-new --port 8087 \
  --pipeline --pipeline-test --pingpong --wad-dma --wad-ring \
  --wad-load-test --debug-audits
```

The browser at `http://192.168.2.75:8087/` displays the bounded test. Keyboard
input is disabled, the level restart is automatic, and the server closes after
100 frames and STOP. This is a measurement session, not an interactive play
launch. Run `replay.sh` on the archived evidence, then normally reboot to release
retained mappings and restore/check the public relay. Never force-unload it.


## Final measured findings

The corrected `live-profile3` run delivers its first frame **192.075 seconds**
after engine preparation (engine upload separately **80.113 s**). Warm restart,
frames 66–68, takes **4.506 s**; the fixed-scene sample delivers **3.803 FPS**.
This is a profiling build with an extra DMA experiment, not an optimization or
a controlled FPS improvement claim. The earlier uninstrumented ring measured
186.566 s, 4.242 s and 3.948 FPS; these sequential runs do not isolate profiling
perturbation from scheduling/run-to-run variation.

### Resident-source transfer, 64 × 32 KiB

| Bracket | Total | Derived decimal MB/s |
| --- | ---: | ---: |
| DMA start to observed completion | 0.101777 s | **20.605** |
| Complete ordinary transfer, including guards/setup/cleanup | 0.308731 s | **6.793** |
| Full guard scans within those transfers | 0.193614 s | — |
| Additional exact payload comparisons, outside transfer bracket | 0.600209 s | — |
| 64 empty timing brackets | 0.0000826 s | — |

The first completed candidate observed **17.322 MB/s** for hardware completion
and **7.037 MB/s** for the guarded routine. Both are short 2 MiB samples with
interrupts/preemption enabled, not calibrated PCI bus traces or maximum RAID
throughput. The 6.793 MB/s rate does **not** include the separate full-payload
comparison. No check was switched off to obtain the hardware bracket.

### Costs across startup, 100 frames and warm restart

| Work | Elapsed time |
| --- | ---: |
| Copy fetched windows into WAD cache, byte loops | **77.960 s** |
| Copy cache/bounce data into Doom on misses | **6.920 s** |
| Copy cached data into Doom on hits | **8.760 s** |
| Complete target WAD read calls (contains the rows below) | **79.234 s** |
| Full target guard scans, ordinary traffic | **35.802 s** |
| Target staging → borrowed output copy | **13.597 s** |
| Staging clear and guard initialization | **8.767 s** |
| Allocation and obtaining ownership loans | **6.389 s** |
| Of that: allocation alone | **3.138 s** |
| Release and returning loans | **5.667 s** |
| Of that: freeing alone | **2.581 s** |
| All ordinary DMA start/completion intervals | **2.843 s** |
| Response wait including response DMA and its checks | **14.451 s** |
| Response DMA and checks within that wait | **10.466 s** |
| Residual response wait | **3.985 s** |
| Frame-DMA barrier | **0.0034 s** |

**The cache copy loops are the largest measured cost.** Before the first frame
alone, cache filling consumes 75.820 s and copies into Doom another 15.540 s.
Those copies sit outside the runtime read bracket. Cache measurements use the
10 ms clock; the runtime's high-resolution total is 79.234 s versus 78.540 s
accumulated at the coarser cache call boundaries. Do not force them to agree or
present either as precise task CPU time.

There are 903 cache fills, 1,805 WAD payload transfers, **59,138,244 useful source
bytes / 59,146,240 DMA payload bytes**, and 14,753,444 bytes delivered to Doom.
Normal traffic executes **13,251 DMA operations**: seven per payload plus 616
extra response polls. Their 26,502 complete guard checks examine 217,104,384
bytes, separate from the benchmark's 128 scans. The benchmark adds 2 MiB DMA
traffic but does not create fake WAD requests or advance their generations.

Host service accumulates **21.997 s** of work (including Python preparation and
journal writes). Separately, successful and pending ioctl calls total **3.973 s**;
the latter also includes registration/finalization outside the service bracket.
Waiting for the full-audit gate adds **23.009 s** across service calls. Those
host totals overlap card execution and cannot be added to the critical path.
The approximately 18 s non-ioctl residual has not been split into Python
serialization, filesystem writes and other work. The small residual card wait
shows that host service is often overlapped with useful card work.

### What to change next

1. Replace the actual WAD cache's byte-copy loops with tested aligned word
   copies, retaining exact bounds and tail handling. The existing staging word
   copy processes useful bytes at about 4.35 MB/s versus 0.76 MB/s for cache
   filling; this is motivation for a benchmark, not a promised speedup.
2. Retain one owned staging allocation for the engine session to amortize
   allocation, free, initialization and loan bookkeeping. Qualify cancellation
   and final drain before changing its lifetime.
3. Investigate DMA into guarded, owned cache storage to remove intermediate
   copies. Preserve descriptor bounds, pinning, completion and full audits.
4. Adapt read-ahead to actual demand. The single-window policy moves about four
   source bytes for each byte delivered to Doom in this capture, including
   repeated windows. Warm restart remains a regression versus 4 KiB loading.

Reducing guard/ownership checking is **not** part of this change. Descriptor
queueing and original RAID-driver practices remain useful future work, but the
measured cache copies should be addressed before tuning PCI burst parameters.

## Physical acceptance and evidence

Both completed runs pass **200 frames / 178 full paired audits** in total.
The final run has 89 pairs, four complete DMA/mailbox frame comparisons, a
three-second two-slot hold/resume, held frames 99/100 across owned STOP and
complete global heap drain. All first 52 controlled pixels/palettes match across
the two card runs and retain exactly the four known native pixel differences at
29260, 29261, 29580 and 29581; all palettes match. The captures do not claim to
fix those differences. The earlier aborted attempt is excluded from these totals.

Final captures reject **24 frame/ownership mutations, three WAD mutations and
six profile-evidence mutations**. Complete system/frame/WAD/profile replay passes
on Linux and the Mac. `comparison.json`, `local-v2-profile.json`, the three
`*-tamper-v2.json` files and `http-verification.json` hold exact results. Every
observed HTTP payload matches its captured frame; observer receipt is not browser
paint time. Native STOP within the benchmark and corruption/quarantine tests
passed; the physical benchmark completed all 64 reads normally. Physical
mid-benchmark STOP/timeout fault injection and long interactive qualification
remain future work.

`candidate.tar.gz` / `card-v1.tar.gz` preserve the first completed candidate;
`candidate-v2.tar.gz` / `card-v2.tar.gz` preserve the final one. SHA-256 files sit
beside them. Exact final runtime/build sources match the archive, recorded in
`accepted-source-check-v2.json`. All archives were copied, hash-verified and
replayed locally before the final normal reboot. Public restoration is recorded
separately when verified. The bounded Doom server closes at STOP.


## Restored public service

Final boot: `94855ff1-240c-45ce-a28f-bfd47d4195f1`. Supervisor **3570** and relay
**3572** own `dac960auto` on `0000:37:09.1`. The unchanged public relay is serving
`http://[2a02:8106:40:9000:f662:19ee:dbad:1f1e]:8080/`; the Mac verified HTTP 200,
2,891 bytes and RTEMS content. See `restoration.json` and `restore-relay.log`.
The bounded Doom server is closed. Inspect actual owner before future work;
stop the public relay normally and never force-unload retained exclusive DMA
mappings. No public visitor log is included in these test artifacts.

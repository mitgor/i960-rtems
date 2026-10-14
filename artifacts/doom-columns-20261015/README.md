# Doom ordinary-column C/assembly comparison — 2026-10-15

**Bounded physical acceptance passed: baseline 3.478 FPS, C 3.857 FPS (+10.89%), assembly 3.821 FPS (+9.86%).**
Independent system/frame/WAD replay passed on Linux and Mac; all 35 tamper
cases rejected. Public service restoration is tracked in `restoration.json`.

Workspace `/home/mit/i960-column-20261015`, boot
`1917f487-902d-4579-bbea-5b5b859db300`. Parallel RTEMS chat was idle. The public
relay closed normally through its SIGTERM handler, restored RAM, unloaded its
module and left the PCI function unbound. No reboot was needed to begin.

## Design and reproducibility

See `game/doom/columns/README.md`. The bounded 52-frame low-detail run uses
original / specialized C / i960 assembly / original column loops. CRC and FNV
are off throughout; direct presentation, scheduler and all audits stay fixed.
The same pinned Doom source, private Newlib, Freedoom 0.13.0 WAD and 6 MiB Doom
zone are retained. Only ordinary high/low columns change; fuzz/translated
columns and plane drawing remain untouched.

`build.sh` rebuilds engine, private runtime, admission, RTEMS and module in an
isolated copy of the accepted dependency workspace. `oracle.sh` links the
unchanged accepted native engine against the same low-detail platform, then
compares all 52 pixels/palettes to the new engine. `run.sh` requires the card to
be unbound; `close.sh` performs replay/tampering and archives evidence. Sources,
exact binaries and native oracles are collected in the build archive; card
captures and measured results are separate. `replay.py --wad /path/freedoom1.wad`
will independently replay system/frame/WAD evidence and HTTP delivery locally.

## Pre-card verification

- 96 Python oracle cases check C and assembly entry points on native builds;
  native assembly is a C substitute and does not prove target assembly.
- 10,000 randomized ASan/UBSan comparisons against original indexing pass,
  including every untouched buffer byte and independent doubled destinations.
- Actual input/STOP/native heap drain passes; two deterministic 52-frame runs
  match the unchanged native engine pixel-for-pixel and palette-for-palette.
- i960 disassembly confirms both new inner loops contain no helper calls.
  C still reloads the constant mask and loop sentinel inside its wall loop;
  assembly keeps the mask in a local register and uses a decrement-to-zero loop.
- Target self-test uses 64,032 temporary owned heap bytes and frees them before
  Doom initialization. It checks ownership/STOP between cases. CPU1 records
  actual implementation and all 96 passed cases. Admission stays below 900,000
  bytes; no larger arena or firmware changes. Kernel mutable tail remains 400.
- Mac cannot run the 32-bit Linux sanitizer executable; those tests ran on the
  Linux host. Python metadata tests pass locally and remotely.

Measurements will retain all within-block delivery intervals, including
outliers. CPU attribution uses the existing 10 ms samples and is not cycle-exact.
Only bounded no-input low-detail performance is tested, not long interactive
play, all levels, or a fixed optimized production build.

## Physical results

| Implementation | Frames | Delivered FPS | Renderer wall | Sampled renderer CPU |
|---|---:|---:|---:|---:|
| Original before | 5–16 | 3.455029 | 210.0 ms | 105.5 ms |
| Specialized C | 17–28 | 3.856557 | 180.0 ms | 90.0 ms |
| i960 assembly | 29–40 | 3.820688 | 180.0 ms | 90.0 ms |
| Original after | 41–52 | 3.500689 | 212.7 ms | 106.4 ms |

Pooled original baseline is **3.477709 FPS** from 22 intervals. Each candidate
uses eleven within-block intervals; first-frame setup is excluded from phase
averages too. No slow interval is removed. C gains **10.89%**, assembly **9.86%**.
Renderer wall falls **211.36 → 180 ms (14.84%)**; sampled CPU falls
**105.91 → 90 ms (15.02%)**. Both candidates are identical at the sampler's
resolution. Their ~0.9% FPS difference does not demonstrate that one is faster.
Prefer the smaller maintenance burden of C; assembly provides no demonstrated
extra benefit here. The compiler emits a good call-free loop once C exposes
invariants explicitly. This narrow change does not establish the earlier
20–40% estimate for a broader renderer optimization program, or 10 FPS.

Do not use the prior batch's pooled 3.178 FPS as this experiment's baseline:
that batch included a long delivery stall. Compare the surrounding baseline
blocks here. All modes use the same low detail, no-input scene, scheduler,
profile queries, direct presentation and full audits. HTTP endpoint delivery is
measured; browser painting and input latency are not.

- All 52 captured frames report the correct implementation and 96 successful
  target self-tests, including real assembly with high/low destination cases.
- All 24 optimized C/assembly frames match the prior accepted low-detail card
  pixels and palettes exactly. The remaining four native/card differences are
  exactly at (140,91), (141,91), (140,92), (141,92) in every frame, with matching
  palettes. They remain unresolved, not attributed to the new kernels.
- 52 complete guarded DMA captures (3,833,856 bytes), first four exact full
  DMA/mailbox pairs, 14 full paired system/RAM audits, owned STOP and global
  allocation drain pass. CRC/FNV removal does not remove these checks.
- Admission **872,376 bytes**, engine memory span **818,352 bytes**. Temporary
  self-test memory is released before Doom starts. Kernel tail remains 400 bytes.
- Host first-frame engine time **323.58 seconds** is dominated by existing WAD
  startup; this experiment changes rendering, not level loading.

## Identities

- Kernel: `810b34d6da187cb9d332f91b695593d3d7f64f0bee8086cc88a92ae75279e9e7`
- Module: `a591fea2c62071a9be9fdae49e7db1962429bbb2f7feca2c6ec651edd135f5f5`
- Engine template: `6443efbcfff0ea85faaf01dd2ce5d9461de16d2c49972c0d678132bdb7bb2ecd`

Default/interactive builds remain unchanged. `--column-test` is a bounded
experiment, not a permanent C/assembly play selector. Next: make a fixed C
candidate and validate longer interactive play, then target plane/span drawing
or compare a carefully bounded scheduling policy. Retain the assembly as a
reference and correctness test, not as a presumed performance improvement.

## Archived evidence and delivery

- Build archive SHA-256: `9c4218a8b0ed53f83325557bbcf0e3a6400f926bc5a2135cfe5ca45d80ccb6b3`
- Card archive SHA-256: `b46b006bc58d0f04f326902801834754861a82e0b011335c86bf5e12030b966d`
- Linux and Mac system/frame/WAD replay pass; all 35 mutated journal/capture
  cases are rejected. `profile-tests.log` additionally checks wrong column
  implementation IDs, self-test counts, trailer padding and bounded admission.
- All 52 HTTP binary payload hashes match their captured frames; mean fetch time
  is 50.96 ms. This observer ran on the Mac, with no synthetic browser FPS claim.
- `card-baseline.png`, `card-c.png`, `card-assembly.png` export actual pixels and
  palettes. Only profile bytes are zeroed for PNG conversion; raw evidence is
  unchanged. The optimized card payloads equal the prior card payloads.
- Normal reboot was requested only after exact archives were saved locally and
  replayed, to release the exclusive test module. No forced unload was used.

Public IPv6 HTTP was restored after normal reboot, without a requested power
cycle. Mac verification returned HTTP 200 with RTEMS content (2,891 bytes).
Boot `03e2a874-bffb-4c2e-b4f6-ec6d90e7a3db`; relay supervisor 1427 / Python
1432 now owns `dac960auto`. See `restoration.json` and `restore-relay.log`.
Stop this owner normally before further hardware work.

# Cached Doom wall clip-copy experiment

The accepted cached-map run was reprofiled from its exact 32 whole-frame
captures. Frames 12–31 spend **48.0 ms** in the renderer: **27.5 ms** in
BSP/walls, **14.5 ms** in planes, **6.0 ms** in masked drawing. The same
admitted engine under the stock map spent 91.5/52/25/14.5 ms respectively.
The [phase replay](phase.py) checks both archive identities, exact admitted
engine bytes, all 20 selected profile trailers and identical pixels/palette;
the [raw phase values](phase.json) retain every 10 ms-clock sample. These
regions are inclusive task wall times, not cycle counts or a direct measure
of the two clipping copies.

`R_StoreWallRange` copies short ceiling and floor clip runs into `lastopening`
through two general `memcpy` calls. `game/doom/build.py --fast-clip-copy`
replaces **only those two calls** with `doom_clip_copy()`, a bounded unrolled
halfword loop. The source and destination remain independent and short-aligned;
the helper never reads or writes past the exact count, including differing
word alignments. The option is off by default. Target-object inspection shows
the general `_memcpy` reference disappears from `r_segs.o`. A native
ASan/UBSan test exercises every count 0–320 and all four short-aligned source/
destination offsets. The full 40-frame native Doom test passes deterministic
replay, input, STOP and heap drain; its WAD request stream matches the
reference.

The isolated new-card candidate admitted 873,356 bytes and then completed
**32 direct-DMA Doom frames** on the default private cache map. The first
four have complete PIO comparisons, all 32 have coherent-buffer guards,
immutable completion markers, native whole-frame hashes and independent
binary HTTP captures. The real native WAD startup oracle, full ownership,
bank/allocator/system checks, three-second stalled-host test, quiescent STOP
and pre-reset full replay passed. Every frame's 64,768 pixel/palette bytes
matches the accepted cached build exactly. Two fresh same-boot guarded stock
firmware reads before the run matched SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`,
with zero status/residual/guard changes.

| Frames 12–31 | Accepted cached build | Clip-copy candidate |
| --- | ---: | ---: |
| Card FPS | **16.964** | **16.964** |
| Renderer mean | 48.0 ms | 48.5 ms |
| BSP/walls mean | 27.5 ms | 27.5 ms |
| Planes mean | 14.5 ms | 15.0 ms |
| Masked mean | 6.0 ms | 6.0 ms |

[Exact comparison](compare.json) checks all 32 frame pixel/palette blocks,
phase trailers and card ticks. The 20-frame result shows **no FPS improvement**;
the 0.5 ms changes are below the 10 ms per-sample clock resolution and cannot
be attributed to this helper. Keep it opt-in. This experiment narrows the
performance problem: shortening these two clip-copy loops alone is not enough
to move the measured BSP/wall phase. Next profile texture/column access or
eliminate the separately measured 6.5 ms presentation copy, with the same
pixel, ownership and audit gates.

The [complete replay archive](candidate.tar.xz) is SHA-256
`4c9de0e6eb15528ad4c63ef351e5b4916c83f22af137fe49e29fbebf5647c3bd`.
It contains the exact admitted engine and kernel, build metadata, 32 guarded
DMA captures, 32 binary HTTP packets, native request oracle, system/owner
receipts, pre- and post-reset full-flash pairs, and source hashes. The
[independent replay](replay.json) passes 18 deliberate transport tamper cases,
all 32 native pixel references and full post-reset audits. The candidate's
steady HTTP observer saw 16.855 FPS and mean observed-to-HTTP availability
of 2.137 ms; this is a short bounded run with a deliberate three-second
stalled-host test, not sustained interactive play.

After reboot, both complete guarded 1 MiB stock reads on boot
`09a4c489-e2ad-46ba-b345-c9ab0c1825f1` matched the stock SHA-256 above.
Both reported `done=1 status=0 residual=0 released=0 guard_changes=0`, then
released their reader modules. The pre-run pair was on boot
`866fa8b0-1ff2-4f1e-ba87-6b183320db96`. No flash write was issued. The
old card stayed unbound and untouched.

Run the offline checks from the repository root:

```sh
clang -std=gnu99 -O2 -fsanitize=address,undefined \
  game/doom/clip_copy/test.c -o /tmp/i960-clip-copy-test
/tmp/i960-clip-copy-test
python3 artifacts/current/clip-copy-20261018/phase.py
python3 artifacts/current/clip-copy-20261018/compare.py \
  artifacts/current/clip-copy-20261018/candidate.tar.xz
python3 artifacts/current/accele160-doom-dma-20261017/verify.py \
  --archive artifacts/current/clip-copy-20261018/candidate.tar.xz
```

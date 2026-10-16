# Doom host determinism — 2026-10-12

The three inconsistent frames came from out-of-post sprite reads, not the game
clock. The same bounded sampling fix is applied to the host and i960 engine.
No Doom code was loaded onto the card for this investigation.

## Reproduction and cause

The old milestone's 2,100-draw Phase 1 DEMO1 was reproduced in two fresh Linux
processes. All 134,400,000 indexed framebuffer bytes were captured in each run.
Only seven pixels differed:

| Zero-based draw | Game tic | Differing pixel positions (x,y) |
| ---: | ---: | --- |
| 497 | 459 | (170,112), (171,112) |
| 1426 | 1388 | (192,117) |
| 1817 | 1779 | (204,154) through (207,154) |

Debugger stops at `R_DrawMaskedColumn` proved that the first sample fractions
were **−15, −11 and −28**, respectively (16 fractional bits). Each becomes
integer index −1. The ordinary column drawer's `&127` wall wrapping turns that
into **127**, beyond the corresponding **18-, 3- and 13-byte** sprite posts.
The result depends on unrelated bytes after the post. A hardware watchpoint also
traced the first differing pixel from wall drawing to the final sprite write.
The full debugger scripts/logs and both original captures are preserved.

`bounded_column.h` clamps masked samples to `[0, post_length-1]`. The masked
column dispatcher sets the length only around its draw call and clears it after
return; zero-length posts are skipped. Normal and low-detail columns, including
translated-color variants, use the bound. Wall columns retain their original
128-pixel wrap. Fuzz drawing does not read the sprite source. No frame or pixel
is omitted from comparison, and no heap-wide zeroing masks the defect.

This intentionally corrects deterministic invalid reads too. Against the first
old run, the fixed Phase 1 DEMO1 differs in **148 pixels across 35 frames**;
repeatability alone would not have detected most of those reads. This is not a
promise of pixel identity with the unmodified historical renderer.

## Validation contract

**Passed: 24 runs, 50,400 draws; zero repeated pixel, palette or tic-trace
differences.** Each six-demo case matches across all four heap fills.

`run_determinism.py` runs DEMO1–3 for both pinned Freedoom 0.13.0 IWADs, four
fresh processes each, with glibc `MALLOC_PERTURB_` values 17, 85, 170 and 255.
Every run uses the 32-bit host binary, a 6 MiB zone, no sound/input, a synthetic
29 ms outer clock step, and a cap of 2,100 draws. Its primary comparison reads
all indexed framebuffer bytes and all explicitly serialized RGB palette bytes;
it separately compares draw ordinals, game tics and the existing FNV trace.
Per-frame SHA-256 covers little-endian ordinal/tic, 64,000 pixels and 768 palette
bytes. Capture open/write/close errors fail the run.

The renderer unit test links the actual patched `r_draw.c`, checking all post
lengths 1–255, both out-of-range edges, normal/low/translated drawers, and
unchanged wall wrapping under AddressSanitizer and UndefinedBehaviorSanitizer.
The allocation-accounting unit test also passes. These sanitizers cover the
focused drawing test, not a claim that the entire legacy engine is UB-free.

The i960 compile still succeeds for all 80 engine units. Text is **306,960 bytes**,
data **69,888**, BSS **250,248**: **627,096 bytes total**, an increase of 240.
The unresolved symbol inventory is unchanged at 58. Host capture instrumentation
is excluded from that object. It remains relocatable, not a loadable Doom image.

## RAM and next gate

The parallel RTEMS work has now [accepted an 8 MiB guarded arena and a live
contiguous 6 MiB allocation](../../rtems/residentnet/UPLOAD.md), with resident
segmented uploads. That is hardware evidence, superseding the earlier RAM-only
proposal. Libc still uses the small old heap; arbitrary application task launch,
runtime/import integration and host-backed WAD reads remain necessary.

Keep the prior 20-workload allocation peak of 6,456,649 bytes as the broader
planning input. With the new engine static size, their sum is **7,083,745 bytes**,
before missing runtime, stacks, transport and allocator metadata. The old budget
with the 240-byte increment is **8,029,720 bytes**, leaving **358,888 bytes** of
an 8 MiB arena; its allowances remain estimates, not a final linker manifest.

The finite host corpus is a reference for these exact inputs and configuration.
It does not prove all levels/mods, interactive play, complete demos, target stack
bounds, i960 output equality or card FPS. First complete the real runtime link
and task/WAD integration, then compare headless i960 output against this corpus
with the accepted memory/ownership audits intact.

## Reproduce

Use the pinned source and WAD archives from
[the original milestone](../../artifacts/doom-m1-20261011/README.md).
On a Linux multilib host, with `game/doom` copied as `tools`:

```sh
python3 tools/build.py --work after --archive doomgeneric-source.tar.gz --target host32
python3 tools/build.py --work target --archive doomgeneric-source.tar.gz --target i960
python3 tools/run_determinism.py --root runs --binary after/host32/doom-profile --wad-dir freedoom-0.13.0
```

The isolated test directory was `/home/mit/i960-doom-determinism-20261012`.
[Exact captures, sources and binaries](../../artifacts/notes/doom-determinism-20261012.md)
include an independent replay command and corruption rejection tests. The old
milestone archive and its verifier remain unchanged: they still describe the
historical failed repeatability test.

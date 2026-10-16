# Exact span and selective renderer optimization

`game/doom/play/build.py --fast-render` selects this candidate. It preserves the
pinned Doom renderer and image dimensions. The engine builder compiles only
`r_bsp.c`, `r_plane.c` and `r_draw.c` with `-O2` instead of `-Os`. The separately
compiled `R_PointOnSide` stays at `-O0` because of the known i960 compiler bug.
Neither traversal order nor clipping/visibility decisions are redesigned.

`span.h` evaluates two successive packed texture positions per iteration. In
low detail it looks up each color once and duplicates it. A four-byte aligned
destination gets one 32-bit packed store; other addresses use byte stores. The
last odd pixel is written separately. Source/map bounds, packed-coordinate wrap,
original inclusive endpoints and the original low-detail `ds_x1/ds_x2` side
effects remain. This is for the little-endian i960/host32 private engine built
with `-fno-strict-aliasing`; it is not a portable big-endian store routine.

The build report and admission manifest record `fast_render`. No new persistent
state or allocation is required. DMA buffers, ownership, full paired audits,
publication/release priority and STOP remain unchanged.

Host primitive test (Linux):

```sh
gcc -m32 -O2 -fno-strict-aliasing -fsanitize=address,undefined \
  game/doom/render/test_span.c -o /tmp/doom-span-test
/tmp/doom-span-test
```

It checks 123,264 spans against the scalar equation, including all destination
alignments, zero/odd/even counts, wrap and surrounding sentinels. Integration
requires deterministic native images plus matched card captures; a primitive
host test alone does not qualify the old i960 compiler.

Evidence and measured acceptance: `artifacts/notes/render-20261015.md`.

Reproduce the tested profile from a fresh build directory on the Linux host:

```sh
python3 game/doom/play/build.py --work /home/mit/doom-render-new \
  --pipeline --pingpong --wad-ring --wad-profile --peer-yield \
  --frame-profile --cpu-profile --low-detail --no-fnv --direct-frame --fast-render
```

Omit `--fast-render` for the original renderer. After the existing card owner has
cleanly released hardware, the bounded acceptance launch is:

```sh
sudo python3 game/doom/play/run.py --work /home/mit/doom-render-new \
  --output /home/mit/doom-render-new-capture --pipeline --pipeline-test \
  --wad-dma --wad-ring --pingpong --debug-audits --wad-load-test \
  --frames 520 --release-schedule priority --port 8087
```

This uses the existing scripted acceptance input and stops after 520 frames;
it is not an unlimited interactive play session. The renderer flag remains
opt-in. Card results qualify the tested low-detail scene/input sequence, not
all WADs, levels or high-detail rendering.

## Optional four-sample kernel

`--span-four --fast-render` selects a four-sample prefix in the same packed
coordinate kernel. The existing two-sample and single-sample tails remain.
Aligned low-detail output uses two 32-bit stores for eight duplicated pixels;
aligned high-detail output uses one 32-bit store for four pixels. Unaligned
output uses byte stores. Unsigned coordinate additions wrap exactly as before.
This is for little-endian i960/host32, ordinary owned framebuffer RAM and the
existing `-fno-strict-aliasing` builds; never use it on MMIO.

Without `--span-four`, the accepted two-sample kernel is unchanged. The option
is recorded in engine, platform, admission and playable-build manifests. It does
not change render quality, buffer ownership, DMA, audits or task scheduling.
Physical acceptance and measurements: [four-sample experiment](../../../artifacts/notes/span-four-20261016.md).

Run the existing primitive oracle both normally and with `-DDOOM_SPAN_FOUR`;
each covers 123,264 high/low spans, destination alignments, tails, wrap and sentinel
bytes under ASan/UBSan. The on-card matched experiment uses fixed low detail;
these primitive tests alone do not qualify high-detail gameplay.

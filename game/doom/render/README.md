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

It checks 82,176 spans against the scalar equation, including all destination
alignments, zero/odd/even counts, wrap and surrounding sentinels. Integration
requires deterministic native images plus matched card captures; a primitive
host test alone does not qualify the old i960 compiler.

Evidence and measured acceptance: `artifacts/render-20261015/README.md`.

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

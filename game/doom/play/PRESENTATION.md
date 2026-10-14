# FNV, direct presentation and frame profiling

These are build-time options for the admitted Doom engine, not firmware changes.
They require the two-slot `--pipeline` build. Ownership, bounds, guards, image
admission, complete guarded DMA captures and full periodic system audits remain.

## Build a candidate

```sh
python3 game/doom/play/build.py --work /home/mit/doom-direct-build \
  --pipeline --no-fnv --direct-frame --frame-profile
```

- `--no-fnv`: omit per-frame pixel and palette FNV. This is separate from the
  framebuffer DMA CRC, selected at run time with `--no-crc`.
- `--direct-frame`: present from Doom's persistent screen directly into a free
  delivery slot. Remove the second copy into that slot. Doom's persistent screen
  remains because partial redraws/cached render pointers depend on it.
- `--frame-profile`: include a versioned timing trailer and frozen DMA timing
  reads. Omit for an uninstrumented build; no measurements are then fabricated.

Run the resulting build only after the previous exclusive owner has closed,
its evidence is saved and a normal reboot has released the retained mappings:

```sh
sudo python3 game/doom/play/run.py --work /home/mit/doom-direct-build \
  --output /home/mit/doom-direct-capture --pipeline --no-crc --wad-dma --port 8087
```

Default builds retain FNV and the copy. The browser wire size remains 65,536
payload bytes; only explicit profiling uses part of the formerly zero trailer.

## Bounded comparison

Build with `--pipeline --presentation-test`, then run with
`--pipeline --pipeline-test --wad-dma`. The manifest fixes the test profile;
interactive launch of the mixed-mode test engine is refused. It compares:

1. Frames 5–16: FNV and copy.
2. Frames 17–28: no FNV, copy.
3. Frames 29–40: no FNV, direct presentation.
4. Frames 41–52: FNV and copy again.

Frames 1–4 have complete byte-identical DMA/mailbox comparisons, and all frame
DMA CRCs are off for this test. No input or level-change confounds are introduced.
Run `rtems/residentnet/verify.py`, `verify_play_pipeline.py` and
`rtems/dma/verify_wad.py`; none substitutes for the others. Native/card comparison
checks every pixel and palette byte separately from the explicit timing fields.
Existing native/card pixel differences are not silently forgiven or changed.

The `PFR1` trailer at offset 64,768 contains sixteen little-endian words:
magic, version, generation, mode (bit 0 FNV / bit 1 direct), renderer ms,
BSP/setup ms, planes ms, sprites ms, persistent-screen copy ms, adapter ms,
previous publication wait ms, display ms, pixel FNV, palette FNV, clock resolution,
reserved zero. All following bytes remain zero. Frozen DMA timing is returned
only for the current complete frame before its exact ACK.

The owned clock advances in 10 ms ticks. Zeros mean below that resolution.
Timings include preemption/service waits; display overlaps rendering, and DMA may
execute within other task intervals. Do not sum overlapping fields or call host
completion wait pure PCI transfer time. Host timing separately records submit,
completion wait, guarded readback, and profile decode/query overhead.

[Physical evidence and results](../../../artifacts/doom-present-20261014/README.md)
track acceptance, hashes, native tests and failed/preliminary attempts.
[Browser controls](PLAY.md) are unchanged.

## Low detail and task CPU samples

`--low-detail` selects Doom's native wide-column renderer while keeping the
320×200 output and existing browser controls. Combine it with
`--pipeline --no-fnv --direct-frame`; add `--frame-profile --cpu-profile` for
phase wall times and timer-sampled Doom-task CPU attribution. Sample counts use
the unchanged 10 ms timer; they are not higher-resolution hardware timestamps.
They exclude samples attributed to peer tasks, with periodic sampling error and
interrupt attribution. Do not interpret `wall - sampled CPU` as exact wait time.

`--detail-test` implies profiling, no FNV and direct presentation. Run only with
`--pipeline --pipeline-test --wad-dma`: frames 1–16 and 41–52 are high detail,
17–40 low detail, all CRCs off. Full audits and ownership remain. Renderer mode
is checked from actual `detailshift`, not just the requested setting. First-frame
setup costs are excluded from each block's FPS intervals and phase averages.
The extra `CPU1` trailer follows PFR1; replay checks its mode, sums, sample bounds
and reserved padding. A mixed benchmark engine cannot be launched interactively.

[Low-detail evidence and acceptance status](../../../artifacts/doom-detail-20261014/README.md).

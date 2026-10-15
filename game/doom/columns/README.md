# Bounded Doom column experiment

The current Doom engine is already native i960 code. This experiment replaces
ordinary column **inner loops**, rather than translating an interpreted renderer.
It follows the register reuse / specialized-loop idea of retro Doom renderers;
it does not copy x86 self-modifying code or disable interrupts.

`column.c` dispatches wall wrapping versus finite-post clamping, and single versus
doubled output, once per column. Source, colormap, fraction and stride stay local.
`column.S` implements the same four cases using i960 local registers. The original
range checks, destination lookup, count and fixed-point setup remain in `r_draw.c`.
Fuzz/translated columns, planes, BSP traversal and fixed-point math are unchanged.
Unsigned fraction accumulation preserves the target's 32-bit wrapping semantics.
The second destination is independent; it is not assumed to be adjacent.

## Build and test

```sh
python3 game/doom/play/build.py --work /home/mit/doom-column-build \
  --pipeline --column-test
sudo python3 game/doom/play/run.py --work /home/mit/doom-column-build \
  --output /home/mit/doom-column-capture --pipeline --pipeline-test --wad-dma
```

Use only an idle, qualified card. Preserve earlier evidence and release the
previous owner normally; never force-unload retained exclusive mappings.

The option implies low detail, direct presentation, no FNV, and CPU/frame
profiling. All frame CRCs are off, as in the prior presentation experiment.
Full periodic system/RAM audits, guarded captures, first four paired DMA/mailbox
comparisons, ownership, exact ACK, STOP and drain remain unchanged. Mixed-engine
interactive launches are refused; default builds still use the original code.

| Frames | Column implementation |
|---|---|
| 1–16 | Original baseline |
| 17–28 | Specialized C |
| 29–40 | i960 assembly |
| 41–52 | Original baseline again |

A bounded table selects modes at display setup. CPU1's last two words contain
actual mode (0/1/2) and completed self-test count (96), only when `column_test`
is admitted. Older profiles still require zero in both fields. Host decoding and
independent replay validate these values for every frame.

Before Doom initializes, an owned 64,032-byte temporary allocation is tested and
freed. The Python-generated oracle covers signed fractions, fraction overflow,
zero/full-height counts, wall wrapping, post lengths 1 through 255, independent
double destinations, and every untouched byte/guard. Both C and real assembly
must pass on the card. Ownership/STOP is checked between cases. There are no new
persistent large buffers or changes to arena admission limits.

On Linux with 32-bit GCC and sanitizers:

```sh
python3 game/doom/columns/test.py
python3 rtems/residentnet/test_column_profile.py
```

Native builds use C in place of assembly; they cannot establish assembly
correctness. The physical self-test and full card frames supply that evidence.
See [the acceptance record](../../../artifacts/doom-columns-20261015/README.md)
for measured performance, exact binaries, captures and remaining limitations.


## Fixed C selection on the span baseline (2026-10-15)

`--fast-columns --fast-render` uses the specialized C helper for all ordinary
columns, without the mixed-test dispatch or assembly. A/B/B/A 520-frame runs
measure 5.330→6.204 FPS (+16.4%), rendering 168.70→ 141.81 ms. BSP/walls improve
106.75→ 84.14 ms and sprites 21.73→ 17.44 ms; planes stay 40.24 ms. All full system,
frame and WAD audits/replays, stalled-host and STOP/drain tests pass.

Both candidate runs match all 520 reference images. The last unchanged baseline
has one menu-transition mismatch at frame 64, equal to the reference's earlier
main-menu image. The strict all-run image oracle records failure; every other
image and all measured-window images match. This timing limitation is retained
in [the report](../../../artifacts/columns-20261015/README.md), not waived silently.
The option remains explicit for wider-scene/high-detail qualification. It does
not reduce quality; runtime quality settings are independent.

# Optional flat-color floors and ceilings

Build the playable engine with `game/doom/play/build.py --runtime-flat` alongside
its normal pipeline options. The engine starts **textured**. F6 or the browser's
**Toggle flat planes** button changes quality at an input/event boundary without
reloading the level or reallocating render/DMA buffers. F6 is reserved for this
control in that build (it does not open Doom's quick-save prompt). Repeated keydown
events toggle once until keyup. Builds without the option retain their renderer
and do not expose the button or accept the new control through the HTTP relay.

Flat mode fills each existing non-sky visplane span with its texture's first
palette index, mapped through the sector's nearest light table (or fixed colormap
for power-up effects). It removes texture detail and distance shading, retains
sector lighting and animated texture selection, and leaves sky, clipping, walls,
sprites and HUD on their original paths. Normal mode returns to the original
textured path on the next rendered frame. It is independent of high/low detail.

The fill handles unaligned heads and tails with bytes and aligned bodies with
32-bit stores. All writes remain in the persistent renderer buffer; DMA slot
ownership, publication, release, heap guards and audits are unchanged. The span
bounds are checked before filling. No memory mapping, firmware or IRQ policy
changes are involved.

Mode telemetry is versioned at bytes 64880–64895 of each 65536-byte frame:
`FLT1`, version 1, mode 0/1, toggle count. The host validates the mode, parity,
trailer padding and normal full frame/ownership checks. Play builds enable CPU
and frame profiling for this feature so the displayed button reports confirmed
card state rather than predicting a successful toggle.

## Tests

- `python3 game/doom/flat_planes/test.py`: 41,088 guarded span cases, actual
  generated key debounce, unchanged textured/sky code, malformed telemetry and
  admission refusal tests.
- On Linux, `game/doom/play/test_native.py --runtime-flat-test` with the built
  private platform: 40 frames, real F6 events, normal/flat/normal, keyboard,
  deterministic repeat, STOP and heap drain under host sanitizers.
- `native_oracle.py` checks repeated native frames against the card's observed
  quality sequence. The known four native-reference differences remain explicit.
- Full physical acceptance uses the unchanged full system/frame/WAD replays and
  mutation tests. See [current experiment](../../../artifacts/current/flat-planes-20261016/README.md).

Bounded ping-pong acceptance disables external keyboard input and injects F6 at
frames 20, 32, 220 and 420. The short transition checks cover turning the feature
on/off; the longer intervals permit a same-build textured/flat/flat/textured
comparison after level reload. Its comparison uses frames 141–218, 241–318,
341–418 and 441–518, excluding transitions and held-slot STOP. Generic transport
FPS comparisons are marked invalid for these mixed-quality runs. Interactive
pipeline sessions expose the normal button and keyboard controls instead.

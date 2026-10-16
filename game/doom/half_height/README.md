# Optional half-height shading

Build with `--runtime-half-height`. Full height is the initial mode. **F7**, or
the browser's height button, toggles alternate-row rendering while playing.
`--runtime-flat`/F6 and `--runtime-detail`/F5 are independent capabilities.
No separate binary is needed to return to full height. This remains an experimental
quality option: the measured half-only gain is just 0.67%, and half + flat is
7.92% slower than flat alone. Keep full height as the default.

The renderer keeps its original view dimensions, projection, visibility,
clipping and texture-coordinate equations. Ordinary and translated columns
shade only even viewport rows with twice the texture step. Plane spans skip
odd rows before textured or flat shading. After masked sprites and weapons,
word copies duplicate each rendered row into the following row, before the HUD
and menus are drawn. This preserves field of view and screen size; thin vertical
features can disappear and edges become coarser. Sky columns are sampled too.
Fuzz retains its existing guarded rendering path, then participates in the same
row expansion. BSP traversal and visplane construction are not halved.

The persistent renderer buffer stays separate from the two owned DMA slots.
The wire format remains 320×200 indexed pixels plus palette and metadata;
this change reduces shading work, not framebuffer transfer size. No allocation,
DMA lease, audit interval, guard scan, STOP or acknowledgement rule changes.
Expansion time is included in the sprite/presentation end of renderer timing.

The `HLF1` version-1 record at bytes 64896–64911 contains mode and switch count.
Decoding validates both, rejects nonzero padding and requires CPU/frame profiling
and the two-slot pipeline. Flat metadata remains at 64880. Debounced F7 events
are consumed before Doom's usual end-game responder. Unsupported deployments
hide the control and reject the key. The bounded ping-pong acceptance intentionally
blocks browser keyboard input and injects the same input FIFO events itself.

Local checks: `python3 game/doom/half_height/test.py` runs guarded column/expansion
comparisons, actual toggle debounce, both metadata combinations and invalid-record
rejection. Linux multilib native tests exercise the real engine with both switches,
movement, deterministic repeat and STOP/drain. `native_oracle.py` reproduces the
first 52 observed card modes for exact comparisons.

[Physical acceptance and measurements](../../../artifacts/current/half-height-20261016/README.md).

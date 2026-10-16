# Bounded input-consumption trace

Use `game/doom/play/build.py --input-trace` with a pipeline build to record
input consumption without changing its scheduling. It enables frame telemetry
and requires admitted double buffers. It is diagnostic and off by default.
It cannot be combined with `--fixed-div-profile`, which uses the same trailer.
The exact divide is independently enabled by default in playable builds;
`--no-fast-fixed-div` retains the original arithmetic for comparisons.

At frame offset 65024, ITR1 has eight 32-bit words: magic (`0x31525449`),
version 1, display generation, row count, cumulative sequence, cumulative
lost-row count, current gametic and current maketic. Up to 16 rows follow,
each containing sequence, phase, next display generation, gametic, maketic,
packed key/down and menu-active state. The remaining words must be zero.

Phases are 1: successful owned input dequeue in `DG_GetKey`; 2: immediately
before `M_Responder`; 3: immediately after `M_Responder`. Non-menu events
then follow the original `G_Responder` path. These records establish the
frame/tic where Doom processed a key; they do not timestamp browser paint.
A read-only accessor exposes the private main-loop `maketic` to this diagnostic.
No heap allocation, interrupt masking, extra card command or ownership change
is introduced by recording. Per-frame count resets only when published;
overflow remains sticky and is rejected by decoding/replay.

The host logs each input submission, ioctl result, before/after monotonic times
and observed frame in `input-submit.jsonl`. `verify.py CAPTURE` reconciles the
bounded eight-key script with all three phases, validates every frame and
rejects mutations. The general decoder also validates arbitrary traced frames;
`verify.py` intentionally targets the 520-frame acceptance script.

Run `python3 game/doom/input_trace/test.py` for default-option, decoder and
actual C recorder bounds tests. Physical evidence is recorded under
`artifacts/input-trace-20261016/`. Old captures lacking ITR1 cannot prove which
tic consumed an input; do not retroactively label the historical menu mismatch
as resolved solely because a new run passes.

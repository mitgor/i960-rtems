# Cached Doom presentation-copy experiment

The accepted new-card cache map leaves a separate 64,000-byte indexed-screen
copy in Doom's `I_FinishUpdate`. `I_VideoBuffer` is persistent because Doom
retains incremental HUD/menu pixels and cached row pointers; the DMA delivery
slots rotate and cannot safely replace it without changing redraw semantics and
pin ownership. This experiment retains that separation and changes only the
fixed 320×200, scale-one, CMAP256 copy. The opt-in
`game/doom/build.py --wide-screen-copy` selects `screen_copy/wide.h`: four
8-byte pairs per iteration when **both** pointers are 8-byte aligned, the
accepted 4-byte path otherwise, and byte copies for other alignments. The
source and destination are distinct owned buffers. All paths copy exactly
64,000 pixel bytes and leave the palette/trailer writers untouched.

The pinned i960 compiler emits four `ldl`/`stl` pairs in the wide branch of
`i_video.o`; the runtime alignment decision was not separately instrumented.
The host ASan/UBSan test covers both headers, all 64 source/destination byte
alignment combinations and exact edges. The matching 40-frame host32 Doom
test passes deterministic replay, input, STOP and heap drain.

The first isolated physical run admitted an 873,236-byte candidate on the
default private cache map. It completed 32 card DMA frames and 32 independent
binary HTTP captures. The first four frames had full PIO pairs; every frame
had complete guards, marker/source/epoch checks, native WAD request oracle,
pixel reference and system/owner audits. The generation-8 three-second held
host buffer and quiescent STOP passed. [Full first replay](replay-first.json)
passes all checks, including 18 deliberate tamper rejections. The
two guarded pre-run whole-flash reads on boot
`09a4c489-e2ad-46ba-b345-c9ab0c1825f1` matched the stock SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`
with zero status, residual and guard changes. The old DAC960PG was unbound.

| Frames 12–31 | Accepted cached build | Wide run 1 | Wide run 2 |
| --- | ---: | ---: | ---: |
| Card FPS | 16.964 | 17.593 | 17.593 |
| Internal presentation copy | 6.5 ms | 3.0 ms | 3.0 ms |
| Renderer wall | 48.0 ms | 49.0 ms | 49.0 ms |
| HTTP observer FPS | 17.178 | 17.738 | 17.752 |

[First comparison](compare-first.json) and [repeated comparison](compare-repeat.json)
verify all 32 pixel/palette blocks and profile trailers in each run. The
second run used the **same admitted engine, kernel and source hashes** on a
fresh boot; its [full replay](replay-repeat.json) again passed all 32 frames,
full audits, 18 tamper rejections, stalled-host handling and STOP. Timing
samples have **10 ms resolution** and
include scheduling; the apparent 1 ms renderer difference cannot be assigned
to this copy change. Both are short bounded runs with a deliberate stall,
not sustained interactive FPS. The gain is repeatable in this fixed window,
but the candidate remains opt-in pending longer interactive acceptance. No
flash write was issued.

The [first complete archive](first.tar.xz) is SHA-256
`36eac7523a7a5556b99681d9bc28f4199ce2965cc44d75152cee575252f3fe62`.
It includes two complete post-reset guarded stock-flash reads on boot
`ef98c3da-b09c-430e-9040-9685ee8d0fc4`, both
matching the stock SHA with zero status/residual/guard changes. The repeated
run's pre-run pair on that boot also matched. The
[repeated complete archive](repeat.tar.xz) is SHA-256
`34cd1aec585f1ec3ffcc446b20f9c9ce33f1c59bbc84616d371b44b4dd6ae1f4`.
Its two complete post-reset stock reads on boot
`18fc4051-18cb-47fa-9bef-a71b04f404e7` also matched, with zero
status/residual/guard changes. Neither run changed flash, and both readers
released their resources.

Replay from the repository root:

```sh
python3 game/doom/screen_copy/test.py
python3 artifacts/current/accele160-doom-dma-20261017/verify.py \
  --archive artifacts/current/wide-screen-copy-20261018/first.tar.xz
python3 artifacts/current/accele160-doom-dma-20261017/verify.py \
  --archive artifacts/current/wide-screen-copy-20261018/repeat.tar.xz
python3 artifacts/current/clip-copy-20261018/compare.py \
  artifacts/current/wide-screen-copy-20261018/first.tar.xz
python3 artifacts/current/clip-copy-20261018/compare.py \
  artifacts/current/wide-screen-copy-20261018/repeat.tar.xz
```

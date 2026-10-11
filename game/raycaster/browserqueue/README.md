# Audited browser queue bridge

`server.py --backend card-queue` connects the browser to the accepted combined
ACK+PUBLISH queue. Reuse the slot-optimized `--queue-slots words` release image and
unchanged queue-v2 module recorded in `artifacts/slotopt-20261011/`.

One HTTP request is in flight. The first frame uses PUBLISH; subsequent frames
acknowledge and replace that same occupied slot with the next generation. The
host must accept the paired descriptor, paired slot, complete paired 512-KiB
allocation, exact command order, guards, metadata and independent native frame
before the next replacement. Every full allocation is archived, without sampling.
This is bounded cooperative rendering, not an asynchronous producer or DMA fence.
Full snapshots use lossless gzip level 1: every decompressed byte remains available
for replay. The accepted browser run reduces archive cost from 21.61 to 5.94 ms;
with animation-frame pacing, measured delivery reaches 13.10 FPS. Seven physical
sessions pass 663 full audits and restoration. Read the artifact report for the
measurement conditions; these timings are not a physical scanout guarantee.

Reset drains an occupied slot with an audited ACK, then initializes a strictly
newer epoch with another full audit. Its immediate reset image is the original
native renderer's deterministic reset reply; the following rendered frame comes
from the card's paired slot bytes and must match the native oracle. All actual
rendered images come from validated card data. Frame and epoch counters never
wrap. This adapter uses one of the two available slots.

Any request/audit failure latches the session faulted; input is never retried.
Raw failure debug files are copied before CLOSE. A broken response socket also
unwinds the server and closes/restores the session, even if the last render
completed successfully. A browser disappearing without a failed socket write
leaves no outstanding producer: the server closes after the idle timeout.
SIGINT/SIGTERM request shutdown after the current bounded transaction. The frame
limit and idle timeout default to 512 updates and 30 seconds, capped at 4,096 and
300 respectively. The application remains loopback-only, with same-origin JSON
controls; use an SSH tunnel. Binding occurs before hardware acquisition.

The page uses one request per animation cycle and records actual canvas draw
intervals in `window.rayDelivery` (bounded to 4,096 samples). This measures browser
delivery, not physical monitor scanout or a reciprocal of kernel callback time.
Closing the page stops requests; keyup, blur and visibility changes clear controls.
No framebuffer is displayed until its complete JSON body has arrived.

## Running

Wait for other card work and the hardware lock to be released. Stop production
HTTP cleanly, verify its close capture, and use a fresh output directory:

```sh
sudo python3 game/raycaster/server.py --backend card-queue \
  --payload /path/to/accepted/target-words/session/kernel.bin \
  --module /path/to/accepted/module/dac960rtems.ko \
  --output /fresh/browser-capture --port 18099
ssh -N -L 18099:127.0.0.1:18099 mit@192.168.2.75
```

Open `http://127.0.0.1:18099/`. On exit, require the normal verified restoration,
unload and unbound-device summary before restoring production HTTP.

```sh
make -C game/raycaster test test-browserqueue
python3 game/raycaster/browserqueue/verify.py /fresh/browser-capture \
  --payload /path/to/kernel.bin --module /path/to/dac960rtems.ko
python3 game/raycaster/upload/verify_quiet.py /fresh/browser-capture
python3 game/raycaster/browserqueue/tamper_test.py /fresh/browser-capture \
  --payload /path/to/kernel.bin --module /path/to/dac960rtems.ko
```

The variable-request replay invokes the unchanged accepted queue verifier,
replacing only its fixed request suite. Full allocation/immutable-region checks,
original ROM, source payload/module hashes, all command ordering and exact CLOSE
checks remain intact. Older archive verification scripts stay unchanged.

`browser_test.cjs URL OUTPUT` uses Playwright/Chromium for real canvas, movement,
turn, reset, blur, alpha and single-flight checks. Set `NODE_PATH` to your
Playwright installation. It compares the former 16-ms-after-draw scheduling with
animation-frame delivery using the same queue backend, 80 draws per run in an ABBA order. This is a
pacing comparison; control scheduling may differ by a few frames, so it is not a
cycle-identical renderer benchmark. See the dated artifact README for measured
acceptance and remaining gaps.

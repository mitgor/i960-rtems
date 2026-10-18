# Persistent keyboard input and pushed browser frames

From the Mac repository, run `./doom`, then open
[http://192.168.2.75:8088/](http://192.168.2.75:8088/).
Textured rendering is the initial mode; F6 toggles flat floors/ceilings.
The installed flat launcher starts both the original owning daemon and this
gateway. Stop parks only Doom. Start new game reuses RTEMS after fresh image/WAD
loading. `./doom shutdown` stops the gateway and terminally shuts down RTEMS.

The original polling page remains at port 8087 for comparisons and fallback.
Close other keyboard tabs before testing: the gateway allows one controller
and up to four viewers. It does not take over a controller already connected.

## Boundaries

- The gateway has **no PCI or DMA access**. It pins the existing control file's
  PID, boot ID and token for its lifetime; replacement or loss ends the gateway.
  It never adopts a dead daemon's retained hardware resources.
- Separate WebSockets carry ordered input and video. Keys no longer wait for
  browser HTTP replies, and frame output cannot block that input connection.
  Messages retain run IDs, strict connection sequences, authentication and
  same-origin checks. Client input has a 32-message bound, server WebSocket
  input a 16-message receive high-water mark, and owner input retains its
  96-event limit and fail-closed overflow behavior.
- Disconnect releases accepted held keys. Three seconds without a control
  message closes the input connection; the owner's independent key deadline
  still covers gateway death. Heartbeats are forwarded only from a real client.
  Owner host-loss, DMA and frame-slot timeouts are unchanged.
- Video allows two unacknowledged frames and stores only the latest upstream
  frame. A slow viewer skips obsolete display generations; it cannot slow card
  frame audits or hold DMA ownership. Missing display ACK for five seconds or
  wrong ACK identity/order closes that viewer. Transport compression is off.
- Only the owner's already-audited `/frame.bin` data is eligible. Header,
  epoch/generation, run and matching status snapshot are checked before push.
  Browser validates binary geometry/identity before palette conversion and
  ACK after canvas submission. Every forwarded image SHA-256 is journaled.
  This is not a camera/input-to-photon measurement.
- The live owner is unchanged: one-event/ACK card input mailbox, task-owned
  ping-pong DMA, every-frame guards/hash/ownership and full system/idle audits
  remain. This gateway polls **loopback HTTP every 10 ms** and pushes to the
  browser; it does not yet subscribe directly to `BrowserSession.publish()`.

Do not confuse browser display ACKs with the owner's card/DMA ACKs. The gateway
cannot issue or delay a hardware ACK. Full audits run even for display frames
that no viewer receives.

## Reproduce installation

Linux Python 3.10+ is sufficient. The only added dependency is the archived
pure-Python `websockets==15.0.1` wheel, SHA-256 pinned in `requirements.txt`.
The installer verifies and extracts it into a private `vendor/`, without pip,
system package changes or modification of the owner's accepted bundle.

From the Mac, with the accepted flat launcher already installed:

```sh
ssh mit@192.168.2.75 'mkdir -p /home/mit/i960-doom-stream-20261018/source'
scp game/doom/play/accele160/stream/*.py \
  game/doom/play/accele160/stream/index.html \
  game/doom/play/accele160/stream/requirements.txt \
  artifacts/current/doom-stream-20261018/dependencies/*.whl \
  mit@192.168.2.75:/home/mit/i960-doom-stream-20261018/source/
ssh mit@192.168.2.75 'python3 /home/mit/i960-doom-stream-20261018/source/install.py --root /home/mit/i960-doom-stream-20261018 --wrapper /home/mit/.local/bin/i960-doom-flat --wheel /home/mit/i960-doom-stream-20261018/source/websockets-15.0.1-py3-none-any.whl'
./doom
```

The original wrapper is preserved as
`/home/mit/i960-doom-stream-20261018/owner-launcher`. Every invocation checks the
gateway source/dependency manifest before calling it. Reinstall explicitly after
source changes, and restart **only** `i960-doom-stream.service` to load new
gateway code. This leaves the card owner alone; disconnected keys are released.

`./doom --stream-port 8089` changes the gateway port for a new gateway service.
`--port` still selects the owner's HTTP port; the two must differ. To change an
already running gateway's port, stop only `i960-doom-stream.service` first.
The textured-only reusable and legacy wrapper selections remain unchanged.

Logs and rollback:

```sh
ssh mit@192.168.2.75 'sudo journalctl -fu i960-doom-stream'
ssh mit@192.168.2.75 'sudo systemctl stop i960-doom-stream.service'
ssh mit@192.168.2.75 'cp /home/mit/i960-doom-stream-20261018/owner-launcher /home/mit/.local/bin/i960-doom-flat'
```

Stopping the gateway alone does not park the game. Use `./doom stop` or the
original port 8087 page for that; never unload retained hardware modules.

## Verification and results

`test_gateway.py` uses the actual production gateway and original HTTP
`BrowserSession`, with no card. It covers authentication/origin, ordered input,
stale runs, disconnect releases, two-credit backpressure, fresh reconnects,
malformed ACKs, STOP/rearm and frame mutations. `test_launcher.py` verifies
repeatable install, preservation/routing of the original launcher and source
tamper rejection. Run them in an environment containing the pinned dependency.

`benchmark.py` runs HTTP / stream / stream / HTTP F6 comparisons, eight pulses
per run. It validates delivered binary frame telemetry and records every image
hash. Run on the host with its private `vendor/` in `PYTHONPATH`, or on the Mac
with `--host 192.168.2.75`. `lifecycle.py` exercises the live card's stalled-viewer,
stale-input, disconnect-release, sequence-gap and STOP gates; it ends in live
idle. These scripts inject input and require no human keyboard controller.

Matched Mac result: **142.13 → 106.18 ms median F6-to-received-frame (-25.3%)**,
and **16.63 → 20.40 received FPS (+22.7%)**. Renderer and DMA were unchanged.
See [complete measurements and acceptance](../../../../../artifacts/current/doom-stream-20261018/README.md).
WebSocket implementation follows the library's
[pinned server API](https://websockets.readthedocs.io/en/15.0.1/reference/asyncio/server.html).

# Persistent keyboard and pushed-frame acceptance — 2026-10-18

The installed default `./doom` now starts the flat-enabled reusable owner **and**
the separate host gateway. Open **http://192.168.2.75:8088/**. Textured is the
initial mode; F6 toggles flat planes. The original port 8087 page remains for
fallback/comparison. Close other keyboard tabs before attaching: one gateway
controller is allowed. The game is currently parked and RTEMS remains owned;
click Start new game or run `./doom` to reload it without rebooting.

## Matched measurements

Same admitted engine, RTEMS instance, DMA mappings, host, card, map and full audit
policy. HTTP / stream / stream / HTTP, eight F6 press/release pulses in every
run, sixteen observations per transport and client location. All delivered
binary images are checked for header, mode/switch telemetry and source hash.

| Client | HTTP F6 median | Stream F6 median | Reduction | HTTP received FPS | Stream received FPS |
| --- | ---: | ---: | ---: | ---: | ---: |
| Linux loopback | 144.27 ms | 96.37 ms | 33.2% | 18.86 | 20.53 |
| Mac, same LAN | **142.13 ms** | **106.18 ms** | **25.3%** | **16.63** | **20.40** |

Mac maximum: 269.46 ms HTTP, 165.15 ms stream. Received FPS improves **22.7%**
on the Mac; individual HTTP runs delivered 18.18 and 15.07 FPS, stream 20.58
and 20.22. Loopback received FPS improves 8.8%. Latency figures pool the sixteen
pulses per mode; FPS is the mean of each transport's two complete observation
windows, including quality transitions. Raw windows and every received frame
hash are retained in `*-abba-final.json`, and `comparison.json` is replayed.

The probe starts before sending F6, and stops when that client's frame receiver
gets the changed, validated binary payload. It does not measure browser OS key
scheduling, canvas paint or input-to-photon latency. F6 is a reproducible
presentation change, not proof of equal latency for movement/shooting. Native
browser tests separately exercised real F6 and a Shift+W chord. The renderer and
card transfer path are unchanged: this is a **delivery improvement**, not a
card-FPS speedup. Both plane modes are visited equally by even F6 pulse counts.

The earlier investigation's approximately 970 ms Mac confirmation median was
recorded during much worse LAN jitter. It is **not** used as this change's
baseline. Network conditions vary; compare the matched ABBA runs here.

## Physical ownership, safety and lifecycle

Boot `cdc21494-3d7c-4fea-b59b-c3e1900fc6aa`, owner PID **33118** throughout,
AcceleRAID 160 `0000:37:09.1`, old card absent. All **190** accepted bundle file
hashes still verify. No firmware, RTEMS, Doom engine, card ABI, source-slot/DMA
ACK policy or kernel module was replaced. No reboot or force-unload occurred.

The gateway talks only to the live owner's authenticated loopback browser API.
Separate input/video sockets avoid frame-output head-of-line blocking of keys.
Video has two exact-generation display credits, one latest snapshot and a five
second missing-ACK bound. Obsolete display generations may be skipped; **every
card frame still passes the original complete audits** before owner publication.
Browser display ACKs have no access to card ACKs or ownership. Compression is off.

- **Game 3: 6,494 frames**, benchmarks/negative gates, STOP to verified live idle.
- **Game 4: 2,012 frames**, real browser Start new game, F6 on/off and browser STOP.
- **Game 5: 1,725 frames**, another browser restart, immediate reload feedback,
  fresh textured image, combined movement keys and browser STOP to verified idle.
- Total: **10,231 full-audit frames**, **12 full paired PIO comparisons**;
  every sent key acknowledged (global sequence **296/296** at final STOP).
- A viewer withheld both display ACKs: the card continued producing frames;
  independent F6-to-confirmed-card-frame took **96.91 ms**, and the stalled
  video connection closed with 1008 after its bounded wait.
- Wrong run ID was rejected without delivering a key. A sequence gap closed
  the control connection. Disconnect after an accepted held F6 released it;
  a new connection's press toggled again. STOP stayed independent of video.
- Original owner/heap/lower-bank/IRQ/cache/guard/DMA-drain/retired-entry/stale
  rearm checks all remained enabled and completed for every parked game.

`verify.py` matches **4,316 gateway payload records** and **796 benchmark-client
payloads** to the original owner receipts, with every SHA-256 equal, and verifies
the two-credit bound, all per-game cleanup/key/PIO/guard results and exact
deployment/dependency hashes. Deliberately wrong payload hash and generation
are rejected. Source-level tests additionally cover cross-origin/authentication,
single-controller admission, malformed ACKs/frames, fresh reconnect snapshots,
stale runs, ordered keys, disconnect releases, STOP/rearm and installer tampering.

The first Mac probe exposed a cached first frame after a viewer-free interval.
That could give the benchmark an obsolete switch-count baseline. The fix clears
the snapshot when the last viewer leaves and waits for a fresh upstream frame
on reconnect. A regression test covers it. The failed probe is excluded from
the matched measurements; no card/ownership fault or audit bypass occurred.

## Saved artifacts and remaining work

- `card-evidence-final.tar.xz`: complete frame receipt journals, game/final-frame
  results, idle/STOP pages, latest DMA guard reports, preflight and both guarded
  boot firmware-read request/status/results. Full ROM bytes already have a
  canonical saved identity and are not duplicated here.
- `deployment.tar.xz`: exact installed gateway sources, original preserved
  owner wrapper, gateway manifest, lifecycle capture and full transport journal.
  `dependencies/` holds the exact pinned pure-Python wheel, including its license.
  Existing engine/kernel binaries are reused from the accepted flat bundle.
- `gateway-manifest.json`, `installed-flat-launcher.sh`, `owner-identity.json`:
  deployment/owner identities. No control tokens or token-bearing HTML are saved.
- `browser.png`: real in-app-browser screenshot of game 5, textured, before final
  movement/STOP. It is not a native oracle image or a paint-latency measurement.
- `verify.py`, `replay.json`, raw ABBA captures and `comparison.json`: independent
  metadata/payload-identity and measurement replay; no evidence code is executed.

The gateway still polls local HTTP at 10 ms; direct owner publication could
remove that extra hop later. The one-key/ACK card mailbox, 29 ms outer engine
sleep and renderer/tic scheduling remain separate latency candidates. A bounded
card input FIFO needs its own engine/kernel acceptance. Do not overwrite queued
key transitions or relax ownership checks to chase a lower number. Extended
play, idle host death and a real browser event-to-paint measurement remain open.

[Source, installation, commands and rollback](../../../game/doom/play/accele160/stream/README.md).

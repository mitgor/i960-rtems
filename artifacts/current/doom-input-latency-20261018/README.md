# Keyboard latency investigation — 2026-10-18

The main observed problem is the Mac-to-LAN path, with additional input and
display round trips in our implementation. Card FPS is not input-to-paint latency.
No firmware, kernel, engine, ownership policy or audit was changed.

| Measurement | Result |
| --- | --- |
| Linux-local F6 POST to mode confirmed in validated card frame, 8 trials | median **74.40 ms**, range 72.34–108.03 ms |
| Mac F6 POST / release / observed status, 4 trials | median **970.31 ms**, range 374.62–1,576.24 ms |
| Mac key-down HTTP request alone in those trials | 9.60–1,047.16 ms |
| Mac → PC ping, 12 samples | mean 208.25 ms; max 546.50 ms |
| Mac → router ping, 8 samples | mean 228.10 ms; max 579.27 ms |
| Linux host → same router, 8 samples | mean 0.87 ms; max 1.07 ms |
| Linux-local status/frame HTTP, 20 samples each | median about 1.1 ms each |
| Mac 65,568-byte frame HTTP, 30 samples | median 1,085.81 ms; max 2,432.71 ms |

The separate short Mac frame sample ranged 178–393 ms, illustrating substantial
variation. These samples establish a problem on the Mac-side network path;
they do **not** prove a specific Wi-Fi, power-saving, congestion or NIC cause.
Pings eventually received every reply, including ones initially reported late.
No network settings were changed. First retest over a wired connection or another
client on the same LAN, comparing both PC and router ping before changing Doom.

The F6 probes use the real browser HTTP input endpoint, existing owner, real
engine and mode reported only after complete frame validation. Local observation
polls every 10 ms. The Mac probe serially waits for down, up and status responses;
its result includes those network waits and is not exact first-visible-pixel
latency. Neither probe measures browser key-event scheduling, canvas paint,
movement response or camera/input-to-photon latency. All twelve toggles passed;
an even number restored textured mode.

## Pipeline findings and priorities

1. **Fix or bypass the high-jitter client network first.** Its measured delays
   exceed the local card-to-validated-frame response many times over. The user's
   approximately 20 FPS may describe card production; it does not establish that
   the browser paints 20 fresh frames per second on this measured path.
2. **Replace chained per-event HTTP with a bounded ordered input stream.** In
   `index.html`, every key, release, heartbeat and STOP joins one promise chain.
   A slow request therefore delays subsequent releases and combinations. Use a
   persistent socket or bounded batch transport with epoch/run ID, sequence,
   authentication, release-on-blur and overflow/timeout STOP preserved. Isolate
   heartbeat/STOP latency without reordering key edges or losing release events.
3. **Batch host-to-card keyboard delivery.** `run_bridge.py` sends one key via
   `live[10:13]` and waits for its ACK before sending the next. The engine ACKs
   in `DG_GetKey()` through checkpoint 101, not an independent input consumer.
   Multiple presses/releases serialize across input-poll/render opportunities.
   Introduce a bounded task-owned FIFO with sequence/epoch checks, not blind
   overwrites of the existing one-entry mailbox. Current ACK means consumed by
   the platform callback, not proof of an immediately simulated/painted action.
4. **Remove browser status-before-frame polling.** The page uses a 50 ms
   refresh interval, then sequential status and frame fetches; the `busy` guard
   suppresses overlapping refreshes. This caps fetch opportunities at 20 Hz and
   adds two network operations. Push latest validated frames, dropping obsolete
   display frames while preserving every ownership check and host audit.
5. **Instrument before changing engine pacing.** The startup entry sleeps 29 ms
   before each `doomgeneric_Tick()`, and Doom input follows the 35 Hz game-tic
   machinery. The input responder also breaks after processing a release.
   Measure browser event/send/receive/paint, host enqueue/mailbox/ACK, engine
   tic and frame generation under a common correlation ID before removing sleeps
   or changing tick semantics. The present test does not assign exact costs to
   these individual stages or promise sub-30 ms interaction at 20 FPS.

## Card session and evidence

Boot `cdc21494-3d7c-4fea-b59b-c3e1900fc6aa`, new card `0000:37:09.1`,
flat reusable bundle `/home/mit/i960-flat-accele160-20261018/bundle`.
The old card is absent. Two guarded full firmware reads passed before startup.
Original interactive game 1 parked after **9,906 frames**, all 44 sent keys ACKed.
Its receipts show median card interval 50 ms, host interval 54.47 ms and
observation-to-publication 1.88 ms (p95 1.95 ms). These combine different scenes
and plane modes and are not a matched renderer benchmark.

The existing live owner successfully accepted a CLI restart into game 2 with
the same RTEMS/pins, loaded a fresh image and WAD, and completed **1,428 frames**.
Eight local and four Mac F6 pulses produced exactly twelve confirmed transitions.
CLI STOP then parked game 2; the HTTP state is `idle`, textured, and the service
remains active. Full per-frame audits, four paired PIO frames per game and the
existing post-game idle audit stayed enabled. Positive CLI idle restart is now
exercised; browser restart and long/negative lifecycle qualification remain open.
No global shutdown or reboot was issued for this investigation.

- `local-f6.json`, `client-f6.json`: complete probe observations, no control tokens.
- `measure_local.py`: reproduce as root on Linux against an already running game.
- `measure_client.py`: reproduce from the Mac against an already running game.
- `network.json`: measured network/HTTP summary with sample sizes and limits.
- `card-evidence.tar.xz`: original game results, all frame receipts, both idle
  audit pages, DMA guard status, preflight and firmware-read results. Full source,
  binaries and frame format are the unchanged accepted flat bundle documented in
  [the flat acceptance archive](../accele160-flat-20261018/README.md).

Do not run input probes concurrently with a person playing. They inject F6.
The game is intentionally left stopped, as requested before this investigation.

# Doom setup: optimized default and historical archive

## Current playable profile

`./doom` selects `/home/mit/.local/bin/i960-doom-flat` on the HP Z400. The
installed wrapper delegates to the pinned `i960-shutdown-safe-20261018/default-bundle`
and starts the pushed-frame gateway. A read-only check on 2026-11-24 confirmed
that bundle has the accepted keyboard FIFO kernel (`8f3b61c3…e7f185`), a
reusable engine, and flat-plane support. The root launcher defaults to this
optimized profile; `I960_DOOM_LAUNCHER` can explicitly select another one.

The optimized build uses low detail, optimized columns, the wide screen copy,
private cache mapping, owned two-buffer DMA, host frame hashing, the sixteen
entry keyboard FIFO, and a WebSocket video/input gateway. It starts with
textured planes; **F6** toggles flat floors and ceilings. The gateway is on
port **8088**; the owner’s older polling page is on port 8087.

On a card running **Firmware injection v1** with the corresponding stock
mailbox and guarded READIMAGE service, use:

```sh
./doom                 # start, or start another game from live idle
./doom status
./doom stop            # park Doom; keep the reusable RTEMS owner
./doom shutdown        # terminal shutdown; power cycle before another owner
```

Open <http://192.168.2.80:8088/> after startup. Startup includes card and
image checks, RAM upload, and WAD loading. Browser controls, restart behavior,
the build and provisioning path are in the [AcceleRAID play guide](game/doom/play/accele160/README.md).
The [stream guide](game/doom/play/accele160/stream/README.md) documents the
gateway and its installation. No launch command programs flash.

**Present hardware boundary (2026-11-24):** the sole installed card
`10112500320` now boots the native RTEMS diagnostic/updater image. It does not
implement the stock mailbox/READIMAGE protocol required by the optimized
Doom launcher. The two Doom services are inactive. Do not run `./doom` on this
card until the optimized engine is ported to the native runtime, or a
Firmware injection v1 card is installed. The default still names the
optimized build so the historical launcher cannot become the normal path.

## Measured optimized results

| Measurement | Result | Evidence |
| --- | ---: | --- |
| Persistent textured, matched steady frames 12–31 | 17.59 card FPS | [Physical persistent run](artifacts/current/doom-persistent-20261018/README.md) |
| Same run, last 64 frames after input | 19.33 card FPS | [Physical persistent run](artifacts/current/doom-persistent-20261018/README.md) |
| Flat-plane comparison, same accepted engine | 17.98 textured / 22.13 flat card FPS | [Flat-plane gate](artifacts/current/accele160-flat-20261018/README.md) |
| Mac received frames, pushed stream | 20.40 FPS mean | [Matched transport comparison](artifacts/current/doom-stream-20261018/README.md) |
| Mac received frames, older HTTP in same comparison | 16.63 FPS mean; one run 15.07 | [Matched transport comparison](artifacts/current/doom-stream-20261018/README.md) |

Card FPS and received FPS measure different stages. The last 64 frames include
scene changes, so they are not a matched optimization comparison. None of
these numbers is a browser paint-rate measurement.

## Historical setup and experiments

The [October 23 command guide](docs/games/archive/doom-commands-20261023.md)
is preserved as a dated snapshot. The [early AcceleRAID run](artifacts/current/accele160-doom-live-20261017/README.md)
measured 2.33 card FPS before the later renderer/cache/DMA work. The
[original DAC960PG browser runner](game/doom/play/README.md) and the
[milestone-1 report](game/doom/README.md#historical-development-record)
remain available for reproduction. Their commands and FPS values do not
describe the optimized AcceleRAID default.

Older installed launchers (`i960-doom`, `i960-doom-reusable`, and
`i960-doom-private-wq`) are retained for explicit historical comparisons.
They are never selected by `./doom` unless `I960_DOOM_LAUNCHER` names one.
The [installed-script snapshot](host/deployments/accele160-20261023/README.md)
records their paths and the default wrapper chain.

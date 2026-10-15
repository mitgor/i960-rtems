# Playing Doom on the Mylex card

For the opt-in bounded **WAD/DMA cost profiler**, including the resident-source
DMA benchmark and exact reproduction commands, see
[the measured profiling report](../../../artifacts/wad-profile-20261015/README.md).
It keeps full audits, disables keyboard input, stops after 100 frames and does
not change ordinary play defaults. Cache copies are the largest measured cost;
the profiler itself is not a performance optimization.


## Optional WAD ring experiment (2026-10-15)

The shared request/completion ring is implemented and has passed bounded card
runs with full audits. It improves first-frame loading after word optimization,
but the current fixed 64 KiB read-ahead policy regresses warm level restart.
Keep the older transport as the default. Results and exact archived builds:
[WAD ring evidence](../../../artifacts/wad-ring-20261015/README.md).

On the qualified Linux host, build in a **new** directory:

```sh
python3 game/doom/play/build.py --work /home/mit/doom-wad-ring \
  --pipeline --pingpong --wad-ring --frame-profile --cpu-profile \
  --no-fnv --direct-frame --low-detail
```

After checking that no other task/service owns the card, run the bounded test:

```sh
sudo python3 game/doom/play/run.py --work /home/mit/doom-wad-ring \
  --output /home/mit/doom-wad-ring-test --port 8087 \
  --pipeline --pipeline-test --pingpong --wad-dma --wad-ring \
  --wad-load-test --debug-audits
```

Open `http://192.168.2.75:8087/`. This is a **100-frame benchmark**, with keyboard
input disabled, an automatic level restart, a deliberate framebuffer stall and
owned STOP. It closes its HTTP server at the end. It is not a persistent play
session. The Stop Doom button requests owned shutdown; do not kill or force-unload
the driver. Archive and verify the captures before normal reboot releases retained
DMA mappings. Restore the prior public service afterward.

For a matched 4 KiB baseline, use the same binaries and omit only `--wad-ring`,
in a fresh hardware session after normal reboot. Keep every other option and all
full audits. Report WAD startup separately from engine upload, and warm restart
separately from startup. See [protocol and tests](../../../rtems/dma/wad_ring/README.md)
for all required replayers and the current limitations.


Doom runs on the card under RTEMS. The Linux host supplies the WAD and sends
frames to your browser. This uses Freedoom; no commercial WAD is needed.

## Open the game

When a play session is running, open **http://192.168.2.75:8087/**.
Wait for the first level, then click the picture to give it keyboard focus.
Refreshing the browser reconnects to the current game; it does not reload the WAD.
The current build allows 30 minutes of play after the first frame appears.
Initial loading has a separate 30-minute limit; the accepted bulk run loads the
first level in about 5m 18s, plus about 79s for engine upload. Board startup adds more time.
Allow roughly 7–8 minutes from a fresh launch; reconnecting is immediate.

If your computer can reach the Linux PC only over SSH, run:

```sh
ssh -N -L 8087:127.0.0.1:8087 mit@192.168.2.75
```

Keep that terminal open and visit **http://localhost:8087/**.

## Controls

| Key | Action |
| --- | --- |
| W or Up | Forward |
| S or Down | Backward |
| A / D or Left / Right | Turn |
| Ctrl or Space | Fire |
| E | Use / open doors |
| Shift | Run |
| 1–7 | Select weapon |
| Tab | Map |
| Escape | Game menu |
| Enter | Confirm menu selection |

To restart the first level: Escape → New Game → episode → difficulty.
Arrow keys select menu items. Losing focus releases held keys. Sound and
persistent savegames are not implemented.
The **Stop Doom** button ends the whole card game session; use Escape for menus.

## Start a session from SSH

Use a fresh, qualified card session with no other card owner. A completed
exclusive experiment retains its module until reboot. Do not force-unload it or
launch a second owner. Save experiment captures before rebooting.

The accepted build is already on this host. After the previous session is saved
and the PC has rebooted, this command reuses it (no rebuild):

```sh
ssh -t mit@192.168.2.75 'sudo python3 /home/mit/i960-wad-dma-20261014/project/game/doom/play/run.py --work /home/mit/i960-wad-dma-20261014/build --output /home/mit/doom-play-$(date +%Y%m%d-%H%M%S) --pipeline --no-crc --wad-dma --port 8087'
```

For a new build on the Linux card host, from the repository:

```sh
python3 game/doom/play/build.py --work /home/mit/doom-play-build --pipeline
sudo python3 game/doom/play/run.py \
  --work /home/mit/doom-play-build \
  --output /home/mit/doom-play-capture \
  --pipeline --no-crc --wad-dma --port 8087
```

Choose new build/output paths. Keep the SSH terminal open while playing.
`--wad-dma` selects bulk host-to-card WAD delivery without payload CRC.
`--no-crc` separately disables framebuffer payload CRC. Image admission,
request identity, bounds, ownership, guards, DMA completion and full system
audits remain enabled. The old CRC-checked mailbox WAD path is available by
omitting `--wad-dma`.

For the bounded acceptance test, replace `--no-crc` with
`--pipeline-test --wad-load-test`. It changes menus automatically and stops
after 52 frames; it is not an interactive session.

The card is shared with the public RTEMS web server. Only one of these exclusive
profiles can own it at a time. After STOP, retain the capture directory and use a
normal reboot before another exclusive launch.


## Bounded ping-pong DMA acceptance

Build with `--pipeline --pingpong --frame-profile --cpu-profile --no-fnv
--direct-frame --low-detail` using `game/doom/play/build.py`. Choose a new work
directory. Launch on the qualified, unbound card with `game/doom/play/run.py
--work WORK --output CAPTURE --pipeline --pipeline-test --pingpong --wad-dma
--wad-load-test --debug-audits --port 8087` (sudo required).

Open `http://192.168.2.75:8087/`. This is a bounded acceptance run: keyboard input
is disabled to preserve the FPS comparison. It measures host-triggered delivery
before switching to card-initiated ping-pong, holds both host destinations for
three seconds, resumes, automatically restarts the level after frame 60, then
stops with frames 99/100 held. The Stop Doom button remains available. Early STOP
safely ends the invocation but does not count as completion of the acceptance
protocol. For the original 52-frame experiment, omit `--wad-load-test`.

All full paired audits, capture guards and ownership checks remain mandatory.
Do not apply the synthetic producer FPS to Doom. Current results and exact
sources/binaries are in `artifacts/doom-pingpong-20261015/README.md`. This batch qualifies the bounded path; keep using the earlier pipeline for
ordinary play until a longer interactive ping-pong run is qualified. Retained
exclusive mappings are released by normal reboot, never forced unload.

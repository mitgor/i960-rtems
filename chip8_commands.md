# CHIP-8 commands

## Native simulation (available now)

From the repository root, prepare a Python environment once:

```sh
python3 -m venv .venv-chip8
.venv-chip8/bin/pip install --no-index \
  artifacts/current/doom-stream-20261018/dependencies/websockets-15.0.1-py3-none-any.whl
CHIP8_PYTHON="$PWD/.venv-chip8/bin/python" ./chip8 --native
```

Open <http://127.0.0.1:8096/>. This runs on the host, not the card.
`--rom /absolute/path/game.ch8 --cpu-hz 500` selects a supplied CHIP-8 ROM.
There are no automatic ROM downloads. Original CHIP-8 dialect only; no SCHIP/XO.
Ctrl-C ends the native server.

## AcceleRAID 160 (reusable play tested on the card)

The tested reusable build is staged at
`/home/mit/i960-chip8-upgrade-20261018/build-g8/bundle`.
Do not start while Doom's exclusive resources remain pinned. As inspected on
2026-10-23, the combined Doom/RTEMS owner occupies the card, even though its
game is parked. A PC reset and a fresh, verified CHIP-8 admission are required
to switch workloads; guest Stop/Start within one owning CHIP-8 RTEMS session
can then reuse that session.

From a fresh boot, or to reuse its existing owning session:

```sh
ssh -t mit@192.168.2.80 sudo -n python3 \
 /home/mit/i960-chip8-upgrade-20261018/build-g8/bundle/project/game/chip8/accele160/launch.py \
 --bundle /home/mit/i960-chip8-upgrade-20261018/build-g8/bundle start
```

The root `./chip8` command targets this tested build: it starts/restarts the owned game,
`./chip8 stop` parks the guest, and `./chip8 status` reports its owner.
`./chip8 shutdown` ends RTEMS globally and requires a PC reset before reuse.
Four games, three restarts, full FIFO batches, stalled video and a three-second
host pause passed on the card in the archived CHIP-8 acceptance session.

Open <http://192.168.2.80:8096/> for the card gateway. Port 8095 is the private
owner's diagnostic HTTP endpoint; normal play uses 8096.

## Controls

Click the page, then use the standard CHIP-8 keypad:

```text
Host:    1 2 3 4     Guest: 1 2 3 C
         Q W E R            4 5 6 D
         A S D F            7 8 9 E
         Z X C V            A 0 B F
```

Arrow keys also move the included original spaceship demo. Stop pauses by
ending the guest; Start new game resets it. Blur/hidden tabs release held keys.
Only one keyboard operator should control a game at a time. No sound output is
implemented.

If the gateway closes after a host pause/owner timeout, run `./chip8` and
refresh the page. This explicitly restarts only the gateway against the same
verified owner. A second keyboard client may be refused; close it and refresh.
Do not force-unload modules or adopt a daemon which has disappeared.

Measured: 47–48 FPS delivered over LAN WebSockets in the scripted tests and
about 52 displayed FPS in the in-app browser. Key submission to a frame showing
the changed key state had 30–39 ms median latency across the three scripted
games (not a measurement of visible game movement). The guest remains capped
at 500 instructions/s. Full details: [acceptance record](artifacts/current/chip8-stream-20261018/README.md).

Global `shutdown` remains a terminal transition; SIGTERM/global shutdown and
a deliberately expired card-side timeout were not exercised in this reusable
acceptance batch. They are separate from the tested guest Stop/Start controls.

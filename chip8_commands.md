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

## AcceleRAID 160 (pending physical acceptance)

The candidate is staged at
`/home/mit/i960-chip8-upgrade-20261018/build-g8/bundle`.
Do not start while Doom's exclusive resources remain pinned. A PC reset is
required when switching workloads, although guest Stop/Start within one owning
CHIP-8 RTEMS session is designed to reuse the session.

The explicit candidate launch, after a fresh boot, is:

```sh
ssh -t mit@192.168.2.75 sudo -n python3 \
 /home/mit/i960-chip8-upgrade-20261018/build-g8/bundle/project/game/chip8/accele160/launch.py \
 --bundle /home/mit/i960-chip8-upgrade-20261018/build-g8/bundle start
```

The root `./chip8` command targets this candidate: it starts/restarts the owned game,
`./chip8 stop` parks the guest, and `./chip8 status` reports its owner.
`./chip8 shutdown` ends RTEMS globally and requires a PC reset before reuse.
**Card execution is not yet qualified; use only for the acceptance batch.**

Open <http://192.168.2.75:8096/> for the card gateway. Port 8095 is the private
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

# T4 — play Tetris on the card over SSH (validated 2026-10-10)

The terminal client is implemented in `host/session/terminal.py`. Gameplay and
all 1,920 framebuffer cells are computed by the i960 payload. Linux forwards keys
and elapsed ticks, displays the returned ASCII cells and manages the T5 session.

## Play on the current machine

From the Mac:

```sh
ssh -t mit@192.168.2.75 /home/mit/i960-tetris-t4/play.sh
```

Use a terminal at least **80 columns × 24 rows**. Controls:

| Key | Action |
| --- | --- |
| `a` / Left | Move left |
| `d` / Right | Move right |
| `w` / Up | Rotate |
| `s` / Down / Space | Drop to the bottom; locks on the next gravity tick |
| `r` | Restart, including after GAME OVER |
| `q` / Ctrl-C | Quit and restore the card's borrowed RAM |

The default seed is 1; pass `--seed 123` to the command to select another seed.
Restart uses the same seed, so an identical input sequence is reproducible.
The wrapper uses this host's existing passwordless sudo configuration. It loads
the exact tested session module, opens an exclusive session, and unloads after
verified cleanup. It refuses an already owned/bound controller. Run it on the
Linux card host, not directly on the Mac.

Shrinking the terminal pauses gameplay until it fits again. Quit still works
while too small. The client uses an alternate screen, hides the cursor, disables
line wrapping while drawing, and restores terminal settings on normal exit,
exceptions and handled signals. An SSH hangup/EOF triggers the same RAM cleanup.
SIGKILL cannot run Python cleanup: the kernel still closes the session when the
last descriptor dies, but module unloading and userspace final captures then
require inspection; do not force-unload a failed or uncertain session.

Each run saves traces and captures below
`/home/mit/i960-tetris-t4/sessions/<timestamp>/`; override with
`--output /new/directory`. The output directory must not already exist.
The old one-shot loader is unchanged, and no further ROM programming is needed.

## Timing and display contract

The scheduler targets 20 Hz with 50 ms simulation ticks. Gravity follows elapsed
monotonic time, not the number of rendered frames. A call processes at most 20
ticks; longer stalls drop excess catch-up and record that count. Missed render
slots are skipped instead of building an unbounded burst of calls.

The input queue holds at most 32 actions. Excess actions are counted and dropped;
quit is urgent, and restart clears queued moves. Fragmented CSI and SS3 arrow
sequences work; unknown escapes and non-control text are ignored. Only one game
key is submitted per frame. All target cells must be printable ASCII before any
terminal output occurs. Fixed host-generated ANSI cursor controls redraw only
changed rows. The last two otherwise blank framebuffer rows hold controls and
latency/queue status; the saved raw card framebuffer remains unchanged.

Every call uses T5's paired code/payload verification, periodic full staging
audit, and self-disarming runner. CLOSE performs the complete restoration checks.
The frontend never retries a failed card execution. It saves diagnostic captures
and leaves a module loaded if it cannot prove safe restoration/unload.

## Validation

The real-card SSH endurance run lasted **1,800.236 seconds**, completing
**35,846 frames and 68 restarts**. Every request/response matched the native C
core on the Mac afterwards, including all 240 state bytes and 1,920 screen cells.
The recorded interval between the first and last call was 1,800.193 seconds.

| Measurement | Result |
| --- | --- |
| Effective update rate | 19.91 Hz |
| Card-call/client-validation latency, median | 42.33 ms |
| p95 / maximum call latency | 43.54 / 59.06 ms |
| Late frame completions | 2,971 |
| Maximum scheduling lateness | 380.43 ms |
| Skipped render slots | 159 |
| Dropped simulation ticks | 0 |
| Intentionally overflowing input actions dropped | 96 |

The scheduling delay includes host/SSH timing and is distinct from card-call
latency. This meets the intended approximately 20 Hz cadence, with occasional
stutter; it is not a hard real-time guarantee. No execution was retried. There
were 15,733 running-game responses, 20,112 game-over responses and one quit;
scripted controls deliberately restarted periodically rather than immediately.

Additional real `ssh -tt` runs passed:

- 244-frame smoke: letters, arrows, Space, input flooding and normal quit.
- 102-frame connection-loss test: killing the local SSH process caused remote
  EOF cleanup, full RAM restoration and module unload.
- 64-frame reconnect: a new connection worked and Ctrl-C exited cleanly.
- Installed-launcher resize: reducing the terminal to 40×12 paused gameplay;
  returning to 80×24 resumed it, and normal quit restored settings and RAM.

Normal/interrupt/resize SSH tests confirmed the exact remote `stty -g` setting
was unchanged afterwards. Five native tests also passed on both macOS and Linux,
covering incremental escape parsing, queue overflow/priority, elapsed-tick carry
and bounds, safe rendering/diffing, and terminal restoration on exception.
The macOS termios comparison excludes its kernel-managed PENDIN bit.

All hardware runs preserved the same boot ID
`a9429ca4-0144-452d-8a80-7189608ce99b`. Full image, table, helper/runner and result
RAM restoration captures were independently checked; modules unloaded and the
card was left driverless. No flash write or reboot was performed. The endurance
run used scripted controls through the actual SSH terminal client, not a human
player or a headless replacement for its input/render loop.

`host/session/ssh_terminal_test.py` drives the same client used by a human through
an actual SSH terminal. It preserves the ANSI transcript and timed key events.
`validate_terminal.py` checks each recorded request against the preceding card
state, executes the native C core, compares the entire response, and independently
checks the saved full RAM/table/code/result restoration captures.

Offline verification example:

```sh
cc -shared -fPIC -DTETRIS_CORE_ONLY -Igame game/tetris.c -o /tmp/tetris-native.so
python3 host/session/validate_terminal.py /extracted/endurance \
  --library /tmp/tetris-native.so
python3 -m unittest discover -s host/session -p test_terminal.py
```

The gzip frame trace has fixed `<QQQ256s2160s` records: call start relative to
loop start, call duration, lateness (all nanoseconds), request and card response.
`metadata.json` identifies the payload, module, seed and boot. `summary.json`
records latency, input/tick/render drops, restarts, exit reason and cleanup.
`progress.json` is updated roughly once per second during play. Open/close
captures remain available even after the module is unloaded.

Evidence is in `artifacts/tetris-t4-20261010/`. This is a cooperative firmware
callback client, not RTEMS or a firmware replacement. Firmware recovery remains
untested; networking/RTEMS work follows its separate plan.

# Browser Doom on the i960

This experimental profile keeps the actual DoomGeneric engine running under
RTEMS while Linux supplies its immutable Freedoom WAD, keyboard events and
browser framebuffer delivery. It is separate from the fully replayed two-frame
[acceptance baseline](../../../artifacts/doom-visible-20261013/README.md).

## Connect and play

For the current lab deployment, open **http://192.168.2.75:8087/** and click the
game to focus it. For a machine that reaches the host only through SSH:

```sh
ssh -N -L 8097:127.0.0.1:8087 mit@192.168.2.75
```

Then open **http://localhost:8097/**. The page reports engine upload, level
loading, frame number and framebuffer readback time. The host renders only PNG
encoding; Doom simulation and rendering execute on the card. There is no sound.

| Control | Action |
| --- | --- |
| W / Up | Forward |
| S / Down | Backward |
| A / Left, D / Right | Turn |
| Ctrl / Space | Fire |
| E | Use / open door |
| Shift | Run |
| Enter | Confirm |
| Escape | Menu |
| Tab | Map |
| Stop Doom button | Request owned engine cancellation |

Keys release when browser focus is lost; a short input heartbeat also releases held keys after a disconnected browser stops renewing them. Frame delivery currently uses bounded
PIO readback and blocks the renderer until the host acknowledges the complete
frame. It can be slow; this is a play-first prototype, not a frame-rate claim.
The first physical six-frame test delivered about **0.169 frames/s** after a
roughly 23-minute initial upload/load. No input reaches the card until a published frame is being collected. Hold
movement/fire until a new frame appears: a short press and release between
updates can be consumed in the same game tick. Queue exhaustion requests STOP
rather than discarding a release event. Use the page’s Stop button to quit;
in-game Y/N confirmation and weapon-number keys are not mapped in this prototype.

## Build and run

On Linux, after installing the preserved cross tools and 32-bit GCC/ASan
support, build from a full Git checkout (including tracked artifacts):

```sh
python3 game/doom/play/build.py --work /home/mit/i960-play-new
sudo python3 game/doom/play/run.py --work /home/mit/i960-play-new \
  --output /home/mit/i960-play-session-new
```

The builder checks pinned inputs, runs the native engine and channel tests,
then builds the RTEMS image and a module for the running Linux kernel. It does
not touch hardware. `run.py` is the hardware action; the card must already
have the accepted hook and be unowned. `--cross /path/to/i960-coff-` selects a
toolchain, `--debug-audits` enables frequent paired checks, and `--self-test`
runs a short movement/STOP session before reloading the user's session.
The convenience wrapper passed a separate fresh-workspace build with native
tests; the exact dated commands below establish the physical build's provenance.
Build-directory paths appear in Doom assertion strings, so a different workspace
produces its own engine/kernel/module hashes rather than reusing an old identity.

The dated [batch](../../../artifacts/doom-play-20261013/) preserves the exact
`build.sh` and `live.sh`, source/binary identities and physical findings.
The build needs the pinned DoomGeneric source, Newlib, RTEMS/lwIP, cross tools,
Linux kernel headers and accepted loader artifacts. See
[stock-to-applications](../../../docs/reproduce.md) before using another card.
The lab scripts use explicit `/home/mit/...` input paths; adapt these in a new
workspace, keeping the pinned hashes and accepted source directories intact.

The new opt-ins are:

- Engine and private platform: `--startup --checkpoints --point-side-o0 --visible --play` (the platform builder does not take `--point-side-o0`).
- Engine admission: `--play`; no fixed-frame oracle identity is claimed.
- Resident runner: `--play-port 8087`; `--play-accept-frames 6` first exercises a short input/STOP session, then loads a fresh engine for play.
- Normal paired snapshot/RAM checks: `--audit-interval 60`; use `3` for frequent diagnostic checks. No guard, ownership, epoch, transport-uncertainty or executable identity checks are removed.

The engine allows up to 30 minutes to load, then resets its 30-minute
play deadline when the first frame is rendered. Missing frame acknowledgement for 60 seconds returns through the
same owned cleanup. Resident hardware ownership still requires a reboot after
final STOP; do not force-unload `dac960auto`. The public autonomous web-server
profile cannot simultaneously own this exclusive card session.

## Implementation contract

`port.c` uses the existing private owned ABI. In this build, verbose checkpoint
calls are suppressed. Its `mark` extension is used for two reviewed operations:
100 publishes the exact admitted BSS framebuffer pointer/size/sequence, and
101 drains one key event. The target verifies the pointer against its trusted
image geometry. No host-selected address can be read or executed.

The renderer parks with its image still pinned. Mailbox op `0x6b` reports the
published sequence, acknowledges it or enqueues a key; `0x6c`–`0x6e` read bounded
1 KiB windows through existing ioctl op 9. New ioctl op 10 carries control.
The target queue has 31 usable entries, the host queue 128; neither silently
overflows. HTTP uses a per-session token and same-origin checks. HTTP threads
never issue card commands. The upload worker services WAD requests and frames.

The 64,000 indexed pixels, 768 palette bytes and zero padding occupy 65,536
bytes. Full-frame transfer plus a repeated first-window check precedes ACK.
The trusted executable and relocation hashes are still checked before entry
and on return. The engine runs until STOP, then private allocations retire,
owned context ends, executable identity is rechecked and the image is released.

Host verification: `test_native.py` runs the real sanitized 32-bit engine with
input, repeats it deterministically, compares a no-input run, then proves STOP
and heap drain. `rtems/residentnet/test_play_channel.py` tests the actual target
channel's immutability, bounds, stale ACK, queue capacity, STOP and timeout.

## Returning to the public web server

Stop Doom using the page button, then wait for the supervisor to complete its
normal global STOP. Preserve the completed journals, results and RAM checks,
copy and hash-check them locally, then reboot to release the retained resident
module. Do not force-unload it. After Linux returns, confirm the card has no
bound driver before starting the existing autonomous web profile from
`/home/mit/i960-rtems-web-20261011` with a **new output directory**. The historical
[restore recipe](../../../artifacts/doom-visible-20261013/restore.sh) records the
matching payload, system-info module and IPv6 relay options; adapt its dated
output paths rather than overwriting an old result. Verify HTTP and outbound
IPv6 again. No automatic reboot or web restoration is scheduled during play.

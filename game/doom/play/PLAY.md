# Playing Doom on the Mylex card

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

# Playing the audited raycaster

The journal acceptance report is in
[artifacts/journal-20261011](../../../artifacts/notes/journal-20261011.md).
This is the fixed-point raycaster, not Doom. The card computes each rendered frame;
the host validates it and sends it to the browser. Arrow keys or WASD move/turn;
Reset restarts the scene. Click the page before using keys. Blur clears controls.

The public Vader service and the raycaster share one card. Start a play session
only after other card work has finished. Use two terminals on the Mac.

In terminal 1, connect to Linux and inspect the current owner:

```sh
ssh mit@192.168.2.75
sudo fuser /run/lock/i960-loadrun.lock
systemctl status i960-http6 --no-pager
```

If the owner is the cooperative public HTTP service, stop it gracefully. Verify
its current output directory's `close` capture with `rtems/transport/run.py`'s
`verify_close` before starting the raycaster. Do not unload an exclusive resident
experiment or bypass the lock. The service command and current output directory
are visible with `systemctl show i960-http6 -p ExecStart`.

For the service restored by this acceptance batch, the concrete close check is
below. If `ExecStart` shows a different output, substitute that path.

```sh
sudo systemctl stop i960-http6
cd /home/mit/i960-journal-20261011-g5s8JT
python3 - <<'CHECK'
import sys
from pathlib import Path
sys.path.insert(0, "rtems/transport")
from run import verify_close
verify_close(Path("/home/mit/i960-rtems-web-20261011/http-after-journal/close"))
print("Production CLOSE verified")
CHECK
test ! -e /sys/bus/pci/devices/0000:37:09.1/driver
```

From the prepared, tested workspace:

```sh
cd /home/mit/i960-journal-20261011-g5s8JT
sudo python3 game/raycaster/server.py --backend card-queue \
  --queue-metadata journal --payload accepted/kernel.bin \
  --module accepted/dac960rtems.ko --output play-01 \
  --port 18099 --max-frames 4096 --idle-timeout 120
```

Use a fresh output name every time. Keep this terminal open. In terminal 2:

```sh
ssh -N -L 18099:127.0.0.1:18099 mit@192.168.2.75
```

Open <http://127.0.0.1:18099/>. The session ends at 4,096 updates, after 120 seconds
without requests, or when terminal 1 receives Ctrl-C. Every request retains full
audits; the browser remains single-flight. Closing the page ends input immediately
and the idle timer then closes the card session.

After the server exits, require successful replay and restoration:

```sh
python3 game/raycaster/browserqueue/verify.py play-01 \
  --payload accepted/kernel.bin --module accepted/dac960rtems.ko
python3 game/raycaster/upload/verify_quiet.py play-01
```

Restore the cooperative public service using the preserved launcher and a fresh
output directory (replace `http-after-play-01` for subsequent sessions):

```sh
sudo systemd-run --unit=i960-http6 --collect \
  /home/mit/i960-rtems-web-20261011/serve-autonomous.sh \
  --internet6 --publish-http6 2a02:8106:40:9000:f662:19ee:dbad:1f1e \
  --http-port 8080 \
  --output /home/mit/i960-rtems-web-20261011/http-after-play-01
```

Check HTTP 200 from the public URL. A session that fails restoration must be
investigated before another application takes the card; do not retry uncertain
card requests. Preserve its capture directory.

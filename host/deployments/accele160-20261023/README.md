# Linux deployment snapshot, 2026-10-23

These are exact, small **installed host scripts** copied read-only from
`mit@192.168.2.80` and checked against `SHA256SUMS`. They record what the
machine had installed; they are not a second source tree or a command to
replace an active owner. No session captures, credentials, sockets or visitor
records are included.

| Snapshot | Installed path | Purpose |
| --- | --- | --- |
| `i960-doom-flat.sh` | `~/.local/bin/i960-doom-flat` | Browser gateway wrapper; delegates to `owner-launcher.sh` |
| `owner-launcher.sh` | `~/i960-doom-stream-20261018/owner-launcher` | Current shutdown-safe default bundle selector |
| `i960-doom-shutdown-safe.sh` | `~/.local/bin/i960-doom-shutdown-safe` | Explicit shutdown-safe bundle |
| `i960-doom-key-fifo.sh`, `i960-doom-reusable.sh`, `i960-doom-private-wq.sh`, `i960-doom-legacy.sh` | `~/.local/bin/` | Older retained comparison launchers |
| `gateway.py` | `~/i960-doom-stream-20261018/source/gateway.py` | Exact running Doom stream source |
| `restore_gateway.py` | `~/i960-packet-dma-20261019/restore_gateway.py` | One-time manifest/owner-checked gateway restoration helper |
| `rtems-console.sh` | `~/rtems-console` | Connects to the combined root-only socket |

The active `i960-doom.service` on inspection was using
`~/i960-packet-dma-20261019/bundle`, while the installed flat wrapper's saved
owner launcher points to `~/i960-shutdown-safe-20261018/default-bundle` for a
fresh session. Do not infer the current running image from the wrapper name.
The newer repository [gateway source](../../../game/doom/play/accele160/stream/gateway.py)
has additional generic-page options and a **different hash** from this running
snapshot. Its installed manifest pins the older file, so copying the newer
source over it would break the identity check. The [versioned installer](../../../game/doom/play/accele160/stream/install.py)
is the controlled path for a new deployment.

The active `broker.py`, `relay.py`, `service.py`, `client.py`,
`start_packet_service.py`, `start_broker.py`, `public_ipv6.py` and `start_link.sh`
matched their [tracked RTEMS runtime sources](../../../rtems/accele160/runtime/)
byte-for-byte on this inspection. The live TUN was `accele0`; the card's `/128`
route and proxy-NDP state named `enp1s0`, while the current host IPv6 default
route used `wlx90de807d9b04`. The public route needs a fresh interface audit
before claiming external reachability or running the link installer again.
This inspection did not stop services or change firewall/routing state.

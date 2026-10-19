# Accele160 paused DMA-bank qualification — 2026-10-19

Successful isolated profile 19: session `20261019T134058Z`, boot
`2930b50e-ed7e-4ccb-b5e4-bc8b9d3916cc`, kernel
`027d84cb3b90e2ffe6afdc66d1d7b3cdde84a0ed3cec5863a231f99e9e022614`.
64 Doom frames, 5,045 WAD reads, 709 external prompt exchanges, zero errors.

`tested-live.tar.xz` contains the immutable bundle (source, binary, objects,
map/symbols, modules, exact engine identity, manifests), paired flash reads,
three owned snapshots, frame/WAD/console records and external console capture.
`tested-final.tar.xz` adds the fourth retained snapshot and final STOP evidence.
`tested-replay.json` and `stop-replay.json` replay the actual bytes.

CONF1 was `0074 → 0374 → 0074`, with confirmed pause before selection and
confirmed restoration before release. HCCR stayed `0020` through the bank
operation and returned to zero. Both reads gave command `{1,8,0}` and data
`{8,8,0}` for config/status/FIFO. The transaction is one-shot; later snapshots
retain its original payload. Native tests cover refusals, mismatches, bounded
pause/release timeouts, unconditional zero restoration, access ordering and
retry prevention. No physical timeout was deliberately injected.

`failed-engine-identity.tar.xz` and its log preserve the first run: the bank
transaction passed, then the Doom uploader safely rejected an older generated
engine identity. `failure-stop.json` inside confirms QUIE and a retained pending
callback. `first-bank-observation.json` decodes that earlier ready snapshot.
The matching generated header was restored before the successful rebuild.

`previous-final.tar.xz` captures the formerly running normal service's clean
STOP before this experiment. The subsequent fresh-boot RTEMS application port
and restored prompt are recorded in the sibling
[application batch](../accele160-runtime-port-20261019/README.md).

`driver-sources.tar.xz`/JSON preserve exact primary-source references inherited
from profile 18. `app.dis` is the corrected tested object disassembly;
`native-tests.txt`, `linux-tests.log`, and `build.log` record validation.
No flash programming, DMA clear/reset, SXP command or RAM reclamation occurred.
See [PROFILE19.md](../../../rtems/accele160/ownership/PROFILE19.md).

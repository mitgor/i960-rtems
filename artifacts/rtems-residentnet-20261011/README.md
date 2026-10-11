# Resident RTEMS networking evidence — 2026-10-11

Source/contract: [rtems/residentnet](../../rtems/residentnet/README.md).
Thirty-step ledger: [BATCH.md](../../rtems/residentnet/BATCH.md).

Seven bounded sessions restored RAM, restored engine controls and unloaded.
Three resident sessions ran without a pending firmware callback, with all PCI
bus-master permissions still disabled. They parked at 533 ticks (host STOP),
6,000 ticks (target deadline) and 846 ticks (final-build host STOP). Every task
IRQ entry had returned before parking. Resident close deliberately retained
memory and the module; exit required reboot.

All three passed IPv4/IPv6 UDP, TCP echo and HTTP 200. The latter two included
maximum-size 1,500-byte IP packets. The deadline run deliberately lost one
card-to-host TCP data packet per IP family and recovered. Offline replay checks
236 IP packets, transport checksums and matching 4,096-byte TCP echo streams;
57 corrupted snapshot variants are rejected. Bulk ioctl latency maxima were
226.1, 229.1 and 240.8 ms respectively. These are test latencies, not throughput
or sustained-service guarantees.

## What remains unproved

Cache-engine completion and broader RAM ownership are **not** established. The
byte-checked firmware sequence waits/acknowledges bit 0 at `40800008` after command
submission at `4080001c`, but live values remain address-like. Two priming patterns,
before/after reports from three bounded engine-phase sessions, and CPU D-cache
enabled/temporarily disabled all returned configuration `40800000`, status `0008`, mask `4080`. The uncached probes
recorded NMISR 0, ATUCR `26`, and original CPU D-cache status `7221`. These probes ran in the ARM and final
STATUS callbacks, outside the isolated interval. Resident snapshots made the
normal-cache observations during isolation. The probes restored CPU cache state
and normal loader cleanup passed. This does not prove a mapped,
idle or drained cache engine. No cache-engine command/mask/ACK write occurred.

All executable code, RTEMS task/IRQ stacks, lwIP pools and packet data remain in
the prior upload allocation. The final image leaves 98,144 bytes before its upper
mutable guard; no external DRAM was reclaimed or destructively tested.

## Archives

Extract **each archive into a separate directory**: build paths overlap.

- `residentnet-v1.tar.xz`: initial module, 100-tick bounded bring-up, build log,
  exact payload recovered from its hash-pinned prepared image. Only the known
  guard padding was normalized; the result matches the original request SHA256.
  The overwritten v1 ELF is not reconstructed. `v1-v2-payload-diff.json` records
  the sole binary difference: one address-literal byte, command read→config read.
  v1 never entered resident mode, so that resident-only command-register read did
  not execute. Later images read only the firmware-evidenced config/status/mask.
- `residentnet-v2.tar.xz`: first resident image, ELF/map/disassembly/symbols,
  module and source, one STOP run, and the actual pre-batch production close
  (`http-after-transfer/close`). Per-word waits; predates total packet deadline.
- `residentnet-v3.tar.xz`: packet transaction deadline, two-seed probes, three
  bounded phases, max-size UDP and deliberate-loss/deadline resident run.
- `residentnet-v4.tar.xz`: final CPU-cache-qualified probe, three more bounded
  phases, final build resident STOP run, full target/module build outputs/source.

All ordinary `preflight`, `open`, trace and audit files are original hardware
captures. `retained-close/result.txt` intentionally says retained DMA/module;
that retained close is required in one-way resident mode, not a completed RAM
restore. Firmware ARM sequence stays 1 during networking.

`cache-audit/` contains exact-ROM disassembly excerpts and the byte-match manifest.
`evidence/` contains native tests, independent replay, RAM-map audits and fresh-boot
observations. The preexisting exclusive profile was cross-built too: its entire
image is identical except for seven `CHECK(__LINE__)` diagnostic-number literals
shifted by the new guarded source lines. `exclusive-regression.json` records the
failed initial byte-identity assertion and the exact reconciled differences; it
is not presented as a new hardware run of that profile.

Visitor statistics are excluded. No flash was written and no disk-I/O operation
was tested.

## Replay

```sh
python3 rtems/residentnet/audit.py --out /tmp/cache-audit
python3 rtems/residentnet/verify_bounded.py --root /tmp/v1 /tmp/v1/residentnet-bounded
python3 rtems/residentnet/verify.py --root /tmp/v2 /tmp/v2/residentnet-live1
python3 rtems/residentnet/verify_bounded.py --root /tmp/v3 /tmp/v3/residentnet-probe-{0,1,2}
python3 rtems/residentnet/verify.py --root /tmp/v3 /tmp/v3/residentnet-live2
python3 rtems/residentnet/verify_bounded.py --root /tmp/v4 /tmp/v4/residentnet-uncached-{0,1,2}
python3 rtems/residentnet/verify.py --root /tmp/v4 /tmp/v4/residentnet-live3
python3 rtems/residentnet/ram_audit.py /tmp/v4/residentnet
make -C rtems test
```

## Recovery and production

Each resident image was captured locally before reboot. The first reboot caused
an SSH outage and a physical-recovery request; a later fresh boot was observed.
Physical intervention versus delayed automatic boot is not established by that
record. The second also returned with a new boot ID. These observations do not
justify an unattended-recovery guarantee. The final boot is
`8a7b0ba8-1ae4-4480-86e8-81c40e3b0c9a`. The original paired 512 KiB RAM image
matches SHA256 `a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0`.
`i960-http6` is active using the existing `autonet` image/module. The public IPv6
Darth Vader page returned HTTP 200 from the Mac. `residentnet-production.tar.xz`
contains that fresh production preflight/open and request identity, excluding
visitor logs. `verify_production.py` replays this recovery evidence.

The artifact inventory was generated with `--tracked-only --index-bytes` so it
hashes staged bytes while a parallel task has unfinished artifact edits. Ordinary
working-tree audit still detects those edits; no unrelated file was staged to
make the audit pass. `host/audit/test_index_inventory.py` verifies this behavior.

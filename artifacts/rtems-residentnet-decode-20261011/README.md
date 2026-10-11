# Cache dispatch and extended resident networking captures

Collected 2026-10-11 from `mit@192.168.2.75`, PCI `0000:37:09.1`.
See [findings and thirty-step ledger](../../rtems/residentnet/DECODE-BATCH.md).
No flash programming, disk operation or new-RAM reclamation was performed.
The loader used its established borrowed regions and save/restore protocol.

| Archive | Contents and outcome |
|---|---|
| `residentnet-decode-v1.tar.xz` | Exact i960 image/ELF/disassembly, pinned kernel module and sources; 100-tick bounded decode probe restored/unloaded. Longer resident run failed on RX-begin `EAGAIN`; traceback, packet/monitor captures and retained-close evidence preserved. Not a successful networking acceptance run. |
| `residentnet-decode-v2.tar.xz` | Second image and module; 100-tick bounded six-page probe restored/unloaded. Corrected inline pending-packet retry; three network rounds and exact 12,000-tick deadline passed. 143 RX / 104 TX blob transactions; 247 decoded IP packets; all checksums/echo streams verified. |
| `residentnet-decode-v3.tar.xz` | Final diagnostic image/module and nine-callback bounded capture (ARM, base STATUS, seven fixed pages); 100 ticks, RAM restoration and unload passed. Adds live board selector, primary operation, sizing/timer pointers and firmware size report. Its networking code is unchanged from v2; no separate resident acceptance run is claimed for v3. Final host retry helper is native-tested. |
| `residentnet-decode-production.tar.xz` | Original production session's close, restored autonet session's OPEN and request identity, production ELF/binary/module and launcher. |
| `residentnet-decode-handoff.tar.xz` | Restored autonet session's later clean close, initiated by a separate raycaster experiment. Both closes pass the existing restoration verifier. |

Archives retain exact builds before replacement, including target binaries,
generated module source, loaded `.ko`, original staged RAM pairs and audit/trace
captures. The source directories may contain historical Python bytecode; `.py`
files and pinned binaries are the reproducible inputs. No missing ELF was rebuilt
and presented as an original.

## Evidence

- `firmware-audit/`: exact unpacked byte audit and both sizing paths.
- `decoder/`: byte-checked bootstrap board selection, both dispatch installations,
  CPU XOR loop and final live decode report. `internal_cpu_path_qualified=true`
  does **not** grant arbitrary RAM or establish all-engine drain.
- `evidence/bounded-v{1,2,3}.json`: exact-image/module and restoration replay.
- `evidence/resident-v2.json`: independent packet/ABI/snapshot replay; 19 corrupted
  snapshots rejected; maximum recorded bulk ioctl latency 241.816 ms.
- `evidence/ram-v*.json`: linked ownership and queue extent checks.
- `evidence/*tests*.txt`: native packet, host, queue, backpressure and decode checks.
- `evidence/http-restored*`: Mac-side public IPv6 HTTP 200 and Darth Vader response.
- `evidence/production-verified.json`, `production-handoff.txt`: successful
  restoration followed by another task's deliberate clean shutdown and takeover.
  The server was verified online; **do not infer that it remained active** after
  the separate experiment started. This task did not interrupt that experiment.

Initial boot `8a7b0ba8-1ae4-4480-86e8-81c40e3b0c9a`; after the failed resident run,
`61aad7bd-307f-4892-9fc4-8a46d6875f02`; after the successful deadline run,
`b73cb338-eb5f-4cd0-8367-ea65e2f799a9`. Both reboot requests led to fresh boots
being observed. The first outage prompted a physical-recovery question; no reply
established whether intervention occurred. Unattended reboot reliability remains
unproven. Artifacts were copied locally before each reboot.

The successful extended test did not encounter RX-busy in-flight. Repeated busy
replies are tested natively; the original failure demonstrates that this condition
can occur on hardware. Queue saturation, ten-minute maximum duration, exact timer
accuracy, broader RAM reclamation and resident internet routing are still gaps.
The existing public IPv6 production path remains autonet.

## Replay

Extract each version into its own directory. From the repository:

```sh
python3 rtems/residentnet/verify_bounded.py --root V3 V3/residentnet-decode-bounded3
python3 rtems/residentnet/verify.py --root V2 V2/residentnet-decode-resident2
python3 rtems/residentnet/ram_audit.py V3/residentnet
python3 rtems/residentnet/decode_audit.py --out /tmp/decode-check --pages V3/residentnet-decode-bounded3/cache-pages.json
make -C rtems test
```

`artifacts/SHA256SUMS` and `artifacts/artifact-inventory.json` cover these captures.
Cooperative profiles and their prior evidence remain in Git.

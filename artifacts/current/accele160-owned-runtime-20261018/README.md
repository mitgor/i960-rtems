# Accele160 normal runtime with owned fault/NMI handlers and ISP

**Qualification complete; owned-runtime prompt restored and left live.**
Corrected two-game acceptance, global STOP and post-reset recovery passed.
Fresh boot `b0732f10-debf-4bb3-8adc-e7e0bdc0fa91` ran the same kernel for
another 64-frame game and 525 console exchanges, then returned to verified idle.
Linux `~/rtems-console` and Mac `./rtems-console` reach the live service. The
existing streaming gateway on port 8088 is restored. This live session has no
global STOP receipt; do not reset it merely to finish documentation. See [implementation](../../../rtems/accele160/fault/OWNED-RUNTIME.md).

## Evidence

- `previous-stream-final.tar.xz`: clean shutdown of the pre-existing streaming
  owner before this isolated test. Its existing corrected admission module was
  preserved; this work does not edit its independently qualified source.
- `prepared.tar.xz`: first mode-5 candidate, with controller-task snapshot poll.
- `failed-controller-poll.tar.xz`: exact first candidate and failed run. Startup
  ownership passed, but the frame-32 request timed out while Init was inside
  Doom's callback. Failure STOP reached QUIE and retained admission/pins.
- `failed-replay.json`: raw failure QUIE and retained-admission checks. This run
  is not acceptance evidence.
- `corrected-prepared.tar.xz`: worker-0 snapshot poll, sole runtime report writer;
  Init writes the final snapshot only after worker/ISR drain.
- `candidate-identities.json`: both build identities and links to the corrected
  candidate's subsequent acceptance/recovery evidence.
- `native-tests.txt`, `entry-audit.json`: actual C/host tests and a bounded
  disassembly check that normal code does not call the fault-injection routine.
- `acceptance.tar.xz`: exact corrected bundle and full session
  `sessions/20261018T211830Z`, with paired guarded firmware reads, 128 DMA frames,
  console raw wires/client results, six owned-state pages and final QUIE/ACK.
- `acceptance-replay.json`: independent replay via
  `python3 rtems/accele160/fault/verify_runtime.py ARCHIVE`.

- `restored-live.tar.xz`, `restored-replay.json`: exact same bundle and full
  restoration session `sessions/20261018T212545Z`, 64 guarded frames, 5,045 WAD
  reads, three fresh owned-state samples, 525 external exchanges (zero errors),
  and paired firmware reads. Replay with `verify_runtime.py --live ARCHIVE`.
- `recovery.json`: links that new boot/firmware pair to acceptance reset recovery.
- `restored-prompt.txt`, `restored-services.txt`: actual prompt answers and
  active owner/gateway status. The gateway launch does not replace the owner.

## Accepted scope

Boot `a076f35d-c5ef-48b5-90fa-947ab4f53f8d`; corrected kernel
`55dc845a43b53fe0e84aba8ed180f28e0331999b74857c96d5e8ff2bb2d5d002`.
Admission module `313af2acae9e740dfb90e10e053beeca47efe9cfd5d0bfa74c1cdd07abd28c15`
is the already accepted shutdown-safe module. Source/module/engine/kernel hashes
are pinned in the archived bundle. No flash was programmed.

Two 64-frame games, rearm, 64 independent paired PIO comparisons, 10,090 WAD
reads, 965 external console exchanges without connection errors, and global
STOP passed. All six owned captures validate the exact fault/NMI symbols, ISP
`c0779040`, all 32 local fault entries, both guard regions, no terminal entry,
no armed NMI test and no IRQ fault. Ticks/handoffs increased from 8/8 to
18,922/16,595. The final QUIE snapshot retains those owners and guards.

Console maximum reply latency was 4938.153 ms, near the existing five-second
deadline. This is not a tighter response-time guarantee. Native tests do not
prove physical behavior; the corrected card capture is the qualification.
SCSI/cache exclusion, active-DMA exception containment and long endurance remain
open. The prompt was restored only after fresh paired firmware reads; no prior
owner's retained command or buffers were adopted.

The unrelated existing artifact symlink in
`artifacts/current/accele160-flat-20261018/post-0/data.bin` is unchanged; checksum
verification here covers this batch, not a new whole-repository audit.

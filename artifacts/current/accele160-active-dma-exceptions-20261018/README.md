# Accele160 active-DMA fault/NMI containment

**Both real exception tests and post-reset recovery passed; normal prompt restored.**
The final live boot is `b92db15d-de4d-4a57-9997-f6236dafa06a`.
The original qualified profile-5 kernel remains running at verified idle after
64 frames, 5,045 WAD reads and 541 external console exchanges without errors.
Use `~/rtems-console` on Linux or `./rtems-console` from this repository on the
Mac. The streaming gateway on port 8088 is active again. Do not reset this live
session merely to finish artifact collection.

This batch adds isolated diagnostic profiles 6/7 to the owned-exception path.
Normal service remains profile 5. See [implementation and limits](../../../rtems/accele160/fault/ACTIVE-DMA.md).

## Evidence

- `restored-live.tar.xz`, `restored-replay.json`: exact qualified profile-5
  bundle and session `20261018T215108Z`, including both guarded firmware reads,
  all 64 frames, console wires/client results, and three owned-state captures.
  Kernel `55dc845a43b53fe0e84aba8ed180f28e0331999b74857c96d5e8ff2bb2d5d002`.
  Its 548 captured card replies had maximum latency 1056.193 ms; this is a
  sample, not a new deadline guarantee. Replay with `verify_runtime.py --live`.
- `recovery.json` links each terminal test to fresh paired firmware reads on
  the next boot. Individual terminal replays deliberately do not claim evidence
  from a later archive. Both recovery reboots returned without physical help.
- `restored-prompt.txt`, `restored-services.txt`: working prompt, idle game,
  returned workspace loan, live owner and streaming gateway.
- `accepted-identities.json`: accepted mode/kernel/boot/entry samples.

- `previous-final.tar.xz`: clean STOP of the prior qualified profile-5 session.
- `prepared-fault.tar.xz`: first hardware candidate and exact bundle.
- `failed-source-aperture.tar.xz`, `failed-replay.json`: first real fault entered
  with CSR=0x400 and its DMA payload/guards passed, but host source verification
  failed because consecutive 4 KiB reads duplicate the odd aperture page.
  The failure kept `done=0 released=0`; it is not the accepted test.
- `corrected-prepared-fault.tar.xz`: full post-drain card fingerprints plus
  independent comparisons of visible odd pages, with the complete host payload
  checked byte-for-byte. No unsupported PCI access to core DMA registers.
- `fault-tested.tar.xz`, `fault-replay.json`: accepted real `faulte` run,
  boot `37da0752-0cf1-4c91-a1bb-5c2697e777a4`, session
  `20261018T214447Z`. Kernel
  `d43dfde43574eb53cd5505312dd18716fdff5f99a3d16a0378a6e59100a1dc70`.
  Entry CSR=0x400, BCR=64304, NDAR=c0821020. Bounded observation took
  1,843,221 polls, then CSR/BCR/NDAR were zero and CDAR=c0829000.
  All guards, peer-register, pattern, marker, source/chain fingerprint,
  visible-page and owner-table checks passed. STOP did not complete the command;
  buffer-module removal was refused and all resources remained retained.
- `prepared-nmi.tar.xz`: independently built real-doorbell-NMI profile 7.
- `nmi-tested.tar.xz`, `nmi-replay.json`: accepted real NMI run on boot
  `dffc27c9-dadb-4905-8d5d-1062374361cd`, session `20261018T214743Z`.
  Kernel `85d89ad77217a5d01459abd2b9eb1bc1d7eb6e1fd6c97cd3f48d20119ce06a1e`.
  Vector 248, entry CSR=0x400, BCR=36864, NDAR=c0821260; 1,810,029
  observation polls to inactive DMA. The same complete retention/integrity
  checks passed. This boot's firmware pair also closes fault-test recovery.
- `entry-audit.json`: both exact cross-builds contain the early CSR/register
  capture before the C terminal record call.
- `native-tests.txt`, `native-tests-linux.txt`: policy, actual card C,
  owned-table corruption, host negative tests; Linux additionally executes the
  actual DMA diagnostic with simulated completion/error/10M-poll timeout paths.
  `native-dma.txt` records the initial focused simulated diagnostic test.

Replay accepted terminal captures with:

```
python3 rtems/accele160/fault/verify_dma.py ARCHIVE
```

The test submits a finite 1024-descriptor repeated-source workload (64 MiB)
plus a final marker, using one existing 64 KiB host target. The second target
stays unchanged. An actual entry-time Channel Active bit is required; CCR
being enabled alone is not accepted. The card observes bounded completion
without releasing the command, source, descriptors or either target.

Hardware timeout/abort containment, reclamation without reboot, broad SCSI/cache
exclusion and resuming a faulted task remain unqualified. The timeout policy
has native simulated evidence only. The existing unrelated artifact symlink
under `accele160-flat-20261018/post-0/data.bin` is not changed; verification is
scoped to this batch rather than a new whole-repository audit.

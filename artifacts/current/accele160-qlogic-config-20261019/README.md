# Accele160 QLogic configuration corroboration, 2026-10-19

Profile 15 reads the one firmware-identified secondary device through SOCCAR /
SOCCDR, restores the selector, and retains the existing profile-14 inventory.
The source contract and static queue/mailbox audit are in
[PROFILE15.md](../../../rtems/accele160/ownership/PROFILE15.md).

Evidence files:

- `previous-final.tar.xz` and its check preserve the previous normal owner's
  clean STOP before the test reboot.
- `build.txt`, `entry-object-check.txt`, `native-tests.txt` and
  `firmware-tests.txt` preserve build and native validation. The profile-15
  exception-entry object exactly matches the accepted normal profile-5 object.
- `tested-live.tar.xz` includes the complete immutable build bundle, firmware,
  kernel/image, modules, paired fresh-boot flash reads, frame captures, WAD
  service trace, three owned reports and external console acceptance.
- `tested-final.tar.xz` preserves STOP, the fourth inventory/config report,
  retained pending callback and DMA pins. Replay JSONs verify both archives.
- `restored-live.tar.xz` and its replay preserve fresh-boot recovery and the
  original normal profile-5 service. `recovery.json`, prompt and service captures
  identify the final running owner.
- `qlogic-dependencies.dis`, `qlogic-firmware-audit.json` and `provenance.json`
  preserve the pinned offline queue/mailbox analysis. Static queue addresses
  do not prove current queue contents, drain, or safe reclamation.

Replay from the repository root:

```sh
python3 rtems/accele160/ownership/verify_inventory.py artifacts/current/accele160-qlogic-config-20261019/tested-live.tar.xz
python3 rtems/accele160/ownership/verify_stop.py artifacts/current/accele160-qlogic-config-20261019/tested-live.tar.xz artifacts/current/accele160-qlogic-config-20261019/tested-final.tar.xz
python3 rtems/accele160/fault/verify_runtime.py --live artifacts/current/accele160-qlogic-config-20261019/restored-live.tar.xz
bash rtems/accele160/fault/test.sh
```

The test's count is bounded at five PCI data reads per successful sample; an
individual PCI transaction is not guaranteed to finish in bounded wall time.
No device configuration write, SCSI chip register access, engine disable or
additional RAM ownership is claimed. Failed restore/identity is rejected; an
exception requires reset with resources retained.

## Acceptance and final state

All four samples report configuration `10161077 / 02b00006 / 01000006 /
00000001 / fff00000` at offsets `00 / 04 / 08 / 10 / 14`; SOCCAR is `1000c`
before and after. Physical revision is 6; the earlier firmware metadata word
was zero. Bus mastering remains enabled. See `observations.json`.

Test session `20261019T092238Z` passed 64 frames, 5045 WAD reads and 697 external
console exchanges (zero errors); worst observed card reply was 1950.706 ms.
STOP passed with retained callback/pins. The normal profile-5 recovery session
`20261019T092824Z` on boot `96907303-fe0a-4c0f-a7bd-558d044f44c6` passed the same
frame/WAD checks and 681 external exchanges. Fresh paired firmware reads
match the accepted image. Prompt idle/zone return and gateway 8088 HTTP 200 pass.
The normal owner is left running; no physical recovery was needed.

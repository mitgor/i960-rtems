# Accele160 P3i: observational engine-ownership audit

No reset or new kernel was needed. The normal session `20261019T041732Z`
remains live, on boot `bbefd6d3-016a-4c9e-8388-36a164e78fd4`.

- `live.json`: three new fixed-device PCI configuration and existing-console
  observations. Raw 64-byte headers and bridge SACR are preserved.
- `audit.json`: decoded BCR=0x202, SACR=0x1554, bus 0x38, prompt preservation;
  secondary reset is deasserted and external arbitration slots remain enabled.
- `prior-core-samples.json`: explicitly historical extraction from the already
  committed profile-5 recovery archive, with archive/member hashes. These
  samples omit CSR/DAR/AAU and do not establish permanent engine exclusion.
- `tests.txt`: decoder evidence rejection and no-ownership-promotion tests.
- `provenance.json`: exact collector/decoder hashes and manual identity.
- `final-health.txt`: prompt and gateway health after the audit.

[Ownership matrix and implementation plan](../../../rtems/accele160/ownership/README.md).
Replay with `python3 rtems/accele160/ownership/audit.py` and `live.json` as its
argument. The collector is `rtems/accele160/ownership/collect.py`; it was copied
to `/home/mit/i960-engine-audit-20261019.py` and run with sudo over SSH.

No flash, core MMIO or PCI configuration was written. No stock descriptor or
memory was reclaimed. SCSI device identity, AAU state and permanent exclusion
remain open. The active runtime's binary is already preserved in
`../accele160-nmi-dma-refusal-20261019/restored-live.tar.xz`; this audit did not
build or deploy another kernel.

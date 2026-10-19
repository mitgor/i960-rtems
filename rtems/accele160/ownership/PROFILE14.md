# Profile 14: non-status engine and firmware dependency inventory

Profile 14 preserves profile 5's owned fault/NMI handlers and interrupt stack,
worker-0 snapshot owner, normal console and Doom lifecycle. It adds an opt-in
fixed whitelist of 48 reads: 24 DMA non-status words, IACR/SACR, six AAU
non-status words, 13 channel-0 metadata words and three AAU queue pointers.
There are no inventory MMIO writes, private PCI configuration transactions,
unknown-device scans, SCSI requests or engine-reset operations.

The original 240-word report is unchanged. Extension words 256–311 remain
within its existing 4 KiB allocation: magic ENG1, schema 1, nonce, sequence,
phase, count 48, two reserved zeros, then values in `inventory.h` order.
The runtime publishes the shared acknowledgement only after both reports are
complete. The owner thread validates and rereads the immutable page. Readers
must supply profile 14 explicitly; profile 5 remains the default. Injection
requests are rejected by both normal runtime profiles.

CSR/ASR are deliberately absent. Reads across engines are sequential rather
than atomic; zero control/count/queue words do not establish completion or
permanent exclusion. An ordinary load also cannot guarantee a wall-clock bound
if a bus stops responding. The whitelist does not dereference captured pointers.
Metadata is firmware RAM, not an independent PCI identity read.

## Firmware dependencies

`firmware_audit.py` accepts only the exact programmed firmware and expanded
runtime hash, then checks machine-code anchors. The associated disassembly
records the reasoning behind those anchors:

- DMA1 submissions at `c004f6d4..c004f6e8` use a descriptor pointer from
  `c0494a20`, write NDAR `1450` and enable CCR `1440`. Stock DMA1 is reserved.
- AAU queue state is `c049b7cc/d0/d4`. Submission at `c0082260` transfers pending
  work to the current queue, writes ANDAR `180c` and enables ACR `1800`.
  The routine at `c0082550` clears control, clears current work, starts queued
  work and invokes descriptor callbacks through fields `+30/+34`. Disabling
  the AAU alone is not equivalent to resolving its software ownership.
- Channel entries have stride `3dc`. Vendor/device are stored at
  `c0384e78/+2`, revision at `c0384e7c`; register mapping/PCI BAR reside at
  `c0384b8c/90`. `c0384b94/98` serve SCRIPT mappings for alternative hardware.
- The `1016` dispatch selects `c0051acc`, calls `c006ea20`, and branches to
  `c006e890`. That routine installs the QLogic callback table at
  `c0384b24..c0384b64`, including `c006ad00`, `c006ec10`, `c0070bd0` and
  `c006d570`. These callback, queue and interrupt dependencies require further
  semantic tracing before takeover.
- This setup uses secondary configuration helper `c0051ed8`, which selects
  through `12a8` and reads `12b0`. Selector 16 encodes `1<<16` in this helper.
  Mapping uses `88000000 | (BAR & 03ffffff)`.
- The Symbios SCRIPT-start routine at `c005e7b0` and the primary configuration
  helper at `c0053d78` are alternate firmware paths. Do not apply their chip
  register offsets to the observed QLogic device.

The physical capture identifies channel metadata `1077:1016`, matching
[FreeBSD's ISP10160 definition](https://raw.githubusercontent.com/freebsd/freebsd-src/releng/12.4/sys/dev/isp/isp_pci.c).
That independently corroborates the name, not the current physical device's
configuration. A direct, bounded, identity-checked secondary configuration
read is still the next corroboration step before chip MMIO or stop operations.

## Reproduction

Clone the accepted immutable bundle, preserving its admission/pin modules.
Build with `ACCELE_TERMINAL=1 ACCELE_TERMINAL_TEST=14 ACCELE_SERVICE=1`, persistent
and reusable mode, keyboard FIFO, and the existing engine identity. Refresh the
manifest (including both inventory sources) and bundle hashes. Use a fresh boot
and the existing single-owner launcher for 64 frames with 32 paired captures;
exercise the console concurrently. Save the complete live archive before STOP.

```sh
bash rtems/accele160/fault/test.sh
python3 rtems/accele160/ownership/verify_inventory.py tested-live.tar.xz
```

After clean global STOP, preserve QUIE/ACK, pending callback/pins and the final
phase-1 report. Reboot, verify fresh firmware reads and restore the immutable
normal profile-5 bundle. The runtime test grants no additional RAM and leaves
SCSI/AAU isolation open.

## On-card outcome (2026-10-19)

Profile 14 kernel `0dfb8e25d5d6e4b4ad13e871b985d385b4a7d7b88e8a1767ea1ef11553f68adf`
passed on boot `4b6636cc-ec67-49ad-b90e-45f1c71d858e`, session
`20261019T074605Z`. All 64 frames, 5045 WAD reads, 709 external console
exchanges and ready/frame32/idle owned-state checks passed. Worst observed card
reply latency was 2710.462 ms; this does not establish a tighter latency bound.
Final STOP also passed with a fourth, phase-1 inventory, QUIE/ACK, intact owned
guards and retained pending admission/pins. There is no normal firmware return.

| Observation across all four samples | Consequence |
| --- | --- |
| DMA1 DAR `c0611320`, PADR `ffd10000`, LADR `c0790000`, DCR `3f`; CCR/NDAR/BCR zero | Stock upload/transfer dependency persists despite the three zero fields |
| DMA2 eight non-status words zero | Quiet samples only; CSR deliberately unobserved |
| IACR `0`, SACR `1554` | Internal agents and external slots have not been denied grants |
| AAU ACR/ADAR/ANDAR/DAR/BCR/DCR and three software queue pointers zero | No queued work visible in these fields; no ASR/completion or permanent-exclusion proof |
| Channel vendor/device `1077:1016`, revision 0, selector `10` | QLogic ISP10160 metadata and its secondary configuration path identified |
| Register mapping `8bf00000`, PCI BAR `fff00000`; SCRIPT fields zero | Use QLogic dependencies, not the alternate Symbios SCRIPT path |

The mapping matches `88000000 | (fff00000 & 03ffffff)`. The firmware's config
helper encodes selector `10` as `1 << 16`, not a Linux BDF. Do not infer its
external-arbiter slot without tracing the board wiring/configuration further.
The metadata identity still requires direct PCI configuration corroboration.
No AAU/SCSI disable, reset, new memory claim or generic cancellation was tested.

[Complete evidence and recovery](../../../artifacts/current/accele160-engine-inventory-20261019/README.md).
Next: corroborate exactly this secondary device with bounded configuration
reads, audit QLogic request/response queues and interrupt/mailbox users, then
implement an identity-gated stop/isolation transaction with reset-only failure.


## Source guard correction and repeat

Review found that the old assembly condition `ACCELE_TERMINAL_TEST >= 6`
would include profile 14 when that flag was passed to assembly. It is now
restricted to 6..13. The cloned profile-5 bundle's older build wrapper did not
pass that flag, so its first binary already omitted the diagnostic CSR read.
The repeated build therefore has the same kernel hash. Both the old wrapper
and an explicit `-DACCELE_TERMINAL_TEST=14` compile of the corrected source
produce the exact accepted profile-5 terminal object (SHA-256
`c58a50215e82dd1602d112651b59d9f26e065523a97246f8c3fa2506c060f507`).
The repository build wrapper already passes the flag. Native preprocessing
now requires profile-5/profile-14 entry equality and keeps the diagnostic read
in profile 13. First-run archives are retained separately; the final acceptance
is the repeat with corrected source. No exception was injected in either run.

The non-status register map comes from Intel 80303 manual 273353-001,
sections 17.6 (arbiters), 19.14 (DMA) and 20.11 (AAU); its PDF hash is recorded
in the preceding [engine-audit provenance](../../../artifacts/current/accele160-engine-audit-20261019/provenance.json).
Firmware RAM addresses instead come from the pinned machine-code audit above.

# Host-visible control ownership — 2026-10-11

**Subsequent live result:** [bounded MU echo and restoration passed](MU-ECHO.md).
The read-only investigation/prototype statements below describe the earlier checkpoint.
Independent STOP and permanent coexistence remain unproven.

Result: **do not reserve a RAM slot in the current BAR yet**. Select IMR1/OMR1
as the next *bounded visibility experiment*, not as a proven permanently owned
channel. No control register or card RAM was written during this investigation.
The web service continued running.

## Evidence provenance

Use the 4.07-0-29 images, not the earlier `remote-analysis` reference directory.
The latter contains 4.07-0-39 unpacked firmware (SHA256 starting `6d35598e`),
which is useful for comparison but is not our installed revision. The scanner
pins the correct unpacked SHA256:

`21f6c1d898a533d7023a53893f03547ed61631016d1b247d3ecbb97b9403c195`

It checks equality with the independently dumped unpacked firmware, and checks
every extracted disassembly byte against the relevant binary. Bootstrap analysis
ends at FEFCF000, where compressed data begins; it is not treated as instructions.
The linear unpacked disassembly still includes embedded data. Extracted leads
were interpreted in their instruction context, not counted as a complete CFG.

Reproduce with:

```sh
python3 rtems/control/audit_ownership.py --out /tmp/control-ownership
```

Artifacts: `artifacts/control-ownership-20261011/` contains byte-checked excerpts,
all direct operand leads, aligned register-literal leads and live MU observations.
Absence from these searches is not proof of absence through computed addresses.

## Proven firmware uses

| Address/range | Evidence in matching firmware | Consequence |
|---|---|---|
| C0000000 upward | Bootstrap FEFC813C–FEFC816C clears to C0140000. Runtime error/scrub code starting C001EC90 also walks low RAM. | A zero snapshot says nothing about reservation; startup and error paths matter. |
| C0000400–C000041F | Bootstrap FEFCB540 builds records and publishes their addresses in internal RAM; C004ED10 patches handler addresses at +14/+1C. | These are active handler data, not index-register scratch space. |
| C0000800 region | PRCB fault table base from earlier live inventory; bootstrap FEFCBBA0 reads entries/record fields based on this address. | Do not overwrite an apparently inactive fault-path structure. |
| C0001000–C000103F | C004B7E4 initialization clears the 64-byte mailbox region; C004B8C4 passes it to command-copy code; C004B978 writes status at C0001018. | Explicit command/status ownership; reject as a sideband page. |
| C0001000 upward | Earlier live core interrupt-stack register FF008704 and PRCB stack field both equal C0001000; stack grows upward. | The remaining BAR tail has no demonstrated bound free of interrupt use. Do not infer a free gap beyond the mailbox. |
| Local 1328 / BAR 28 | C004B7B4 initializes inbound mask; C004B89C, C004B98C and C004B9C8 set/clear bit 2 while handling commands. | It is a live firmware-owned register. Any experiment must preserve all unrelated bits and detect state changes. |
| Local 1320 / BAR 20 | C004B9F0 dispatches doorbell bits 0–4 and acknowledges them; bit 3 enters additional control paths. | Do not invent an unused doorbell command. |
| Local 1310 / BAR 10 | C0039CA0 diagnostic saves IMR0, writes 5A5A5A5A, reads it and restores it. | IMR0 is demonstrably used, even though live samples were zero. |
| Local 1324 / BAR 24 | C004EF20 MU ISR checks inbound doorbell status bit 2 and calls C004B9F0; initialization writes all ones to status. | Pending-bit lifecycle is not ours by default. |

The stack/mailbox overlap is a reason to trace actual frame bounds before RAM
borrowing, not a claim that the existing firmware is corrupt. PCI MU overlay
registers and their low local addresses (13xx) are distinct from translated
C00013xx RAM; these must never be conflated in the ownership map.

## Live read-only observations

`read_mu.c` maps resource0 with PROT_READ and performs only aligned volatile
32-bit reads at 10,14,18,1C,24,28,30,34. It verifies PCI vendor/device first.
It never accesses queue ports, APIC registers, index RAM, reserved offsets or
writable mappings. This implementation was compiled/run on the little-endian
x86 Linux host. Intel's RC status description means write-one-to-clear here;
these status reads do not acknowledge interrupts.

Three samples one second apart while `dac960auto`/HTTP ran:

- IMR0, IMR1, OMR0, OMR1: zero in all samples.
- IISR/OISR: zero in all samples.
- IIMR: 000001FB; inbound messages 0/1 and index notifications masked, ordinary
  doorbell status bit 2 unmasked.
- OIMR: 000000FF; outbound message interrupts masked.

No aligned immediate for IMR1 (1314), OMR0 (1318) or OMR1 (131C) occurs in the
matched unpacked image. The scanner also found no explicit memory-operand lead
for these registers in the inspected bootstrap. Computed accesses, diagnostics,
other boot/recovery code and all future firmware states remain outside that
negative claim. Stable zero values plus masks make IMR1/OMR1 promising, not owned.

## Selected next experiment: masked IMR1/OMR1 echo

Prefer two message words over 128 bytes of unreserved low RAM. The existing CTL1
prototype requires a framing adapter for this narrow transport; do not map its
64-byte slots over adjacent MMIO. First prove one word in each direction, then
add framing, epoch/sequence and STOP. An echo alone will not complete P1.

Implementation requirements for the one-shot experiment:

1. Build a separate exact-image-pinned target/module variant. Stop the web service
   normally and verify STOP/RAM restoration/unload before loading that variant.
   Keep the production binaries for immediate restart afterward.
2. The driver serializes access with its session lock; no raw userspace MMIO
   writes. Require both message values and their pending bits to match the saved
   baseline, message masks set, expected firmware identity and healthy command
   service. Refuse instead of altering the firmware's masks to fit assumptions.
3. Arm a bounded timer-driven echo routine through the existing bootstrap path.
   The target polls only IMR1 and writes only OMR1 for a tagged test request.
   It must preserve mask/doorbell state and have a local watchdog deadline. No
   change to vectors beyond the already verified temporary timer mechanism.
4. Host pauses ordinary firmware transactions, writes one token at BAR14 through
   the driver, and polls BAR1C for a matching transformed reply. Use readl/writel
   and posted-write completion. Record host command count before/after to show
   the exchange did not require stock 20/21/6F commands. Bound every wait.
5. Snapshot inbound/outbound pending bits before/after. Clear only the newly
   generated message-1 bits under exclusive experiment ownership; never write a
   broad status mask. Restore exact message values and verify them. Account for
   restoration writes generating fresh status, too.
6. Stop the timer through the proven normal path and verify its completion before
   restoring handler RAM. If ownership/execution becomes uncertain, retain
   resources. Do not interpret a seen echo as proof of safe STOP or reclamation.
7. Restart the original HTTP/visitor service and verify its page. Preserve captures
   for successful and failed attempts, and separate live echo evidence from
   protocol simulation.

Remaining prerequisite for live writes: complete the dedicated driver/target
implementation and its simulated pending-bit/mask/timeout/restore tests. This
investigation selects the candidate and bounds that experiment; it does not
certify permanent firmware coexistence or enable unrestricted application tasks.

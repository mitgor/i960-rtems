# Live firmware and board-descriptor reads — 2026-10-10

Latest: [RAM-WRITE-VERIFIED.md](RAM-WRITE-VERIFIED.md). Fixed 16-byte scratch upload/readback/restoration passed at C0FAC010 in the extra staging allocation block. All 22 commands clean; original 64 bytes restored, probe removed. No execution/recovery/flash.

**Paired reads verified live firmware bytes, board pointer C0110780, stored memory
alias C1000000, and the expected 512 KiB board callbacks.** No RAM upload,
custom execution, recovery entry or flash programming occurred.

## Live observations

The pointer verification described in STAGING-POINTER-VERIFIED.md is a prerequisite.
After that, the runtime audit reads these exact regions twice with different host
sentinels and requires identical bytes:

| Local address | Length | Observed result |
|---|---|---|
| C004A2E0 | 16 | `061e805c5c2700090030f082985d0ac0`, exact archived program entry |
| C011E22C | 8 | Board pointer C0110780, alias value C1000000 |
| C0110780 | 512 | Matching board descriptor and allocator geometry |

The instruction comparison covers sixteen bytes, not a hash of all running code.
The alias value is observed; its cache/coherency semantics have not been tested.
The board fields include:

| Field offset | Value | Traced role |
|---|---|---|
| 08 | 00080000 | Flash size |
| 0C | FEF80000 | Flash base |
| 10 | FEFF9C00 | Flash descriptor |
| D0 | C004D670 | Descriptor read callback |
| D4 | C004CF20 | Descriptor upload callback |
| D8 | C004D940 | Extended descriptor read callback |
| E0 | C004CE90 | Image read callback |
| E4 | C004CED0 | Image upload callback |
| E8 | C004D6D0 | Unsupported legacy programming callback |
| EC | C004CF80 | Programming callback used by 2B/1 |
| F0 | C00209B0 | Host mailbox-address/ATU setup callback |
| F4 | C0016710 | Additional board callback; not invoked here |
| 124 | 00000739 | Allocator pool block count |

These observations resolve the active-callback uncertainty for the running card.
They agree with the stock 512 KiB bootstrap route. In particular, the 2B/14 callback
previously traced statically is now observed as C00209B0, rather than an arbitrary
execution hook. No descriptor subcommand was submitted to make these reads.

## Probe guard and validation

The workspace already contained the runtime extension and the controller had a
completed runtime probe when this continuation began. Its transcript reported
13 matched completions, status zero, unchanged guards and pending=0. That complete
capture and its exact source/header/module were archived, then the probe removed.

The guard was subsequently tightened and the experiment repeated:
`pointer_check=1 runtime_check=1`, with default `attempt=0`, length=512 and offset=0.
The hardened command gate requires successful pointer verification and permits
only the three exact address/length pairs above. The board pointer and alias must
match their newly observed fixed values before reading the descriptor. A final
Enquiry2 must match the expected profile. There is no user-supplied arbitrary
runtime address and no upload opcode added.

The hardened run also completed all 13 commands with matching IDs, status zero,
unchanged DMA guards and pending=0. The module was removed, and final checks
confirmed the controller driverless and module absent. Normal mailbox/doorbell
and DMA transport writes occurred; these were read commands, not passive inspection.

Artifacts: `artifacts/runtime-read-20261010/`, with the repeated hardened run in
`hardened/`. Each contains the transcript, paired captures, executed source/header,
kernel-specific module and validation report. The initial source is intentionally
preserved separately from the hardened source.

Kernel W=1 build and native guard tests passed. Seventeen Python tests passed,
including live-capture validation and rejection of bad status, guard damage,
pending DMA and paired-but-invalid callbacks. Reproduce validation with:

```sh
make -C host/dump test-guards
python3 -m unittest discover -s host/dump -p 'test_*.py'
python3 host/dump/validate_runtime.py artifacts/runtime-read-20261010/hardened
```

## Next experiment toward RAM execution

A reversible RAM write/readback is now a concrete next target, but upload behavior
outside staging has not been demonstrated. Before adding it, select an explicitly
reserved scratch region, save its bytes, trace upload quiescence/cache behavior,
and design a fixed-address, fixed-length transaction with restoration and readback.
The current module still allows only Enquiry2 and LoadImage; do not simply add an
unrestricted 21 interface.

After a verified data write, a separate reviewed execution handoff can use a
minimal observable payload. It must preserve stock state or provide a tested
recovery path, handle caches and DMA, and initialize the boot monitor's required
fault/interrupt state if that monitor is the destination. Calling its entry alone
is not yet justified. Independent flash recovery remains unresolved; this work
provides progress toward a RAM-only experiment without flashing.

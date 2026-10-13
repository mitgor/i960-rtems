# Staging allocation located by geometry — 2026-10-10

Latest: [STAGING-POINTER-VERIFIED.md](STAGING-POINTER-VERIFIED.md). Live paired four-byte reads confirmed C0F2C000 at C0112A70. Fixed-purpose read gate only; no upload, execution, recovery entry or flash. Probe removed cleanly.

The matching firmware's successful allocator return is predictable from fields
already exposed by Enquiry2. Historical and fresh live geometry both predict
**C0F2C000**. This is a derived address, not yet an observed staging-pointer value.
No out-of-window read, upload, recovery entry or flash was attempted.

## Derivation

C004D230 obtains the staging allocation from C001EA70 and stores its returned
pointer in C0112A70. The allocator uses:

- U = value at C009C3F8 shifted left 9 (allocation unit, bytes).
- N = low 16 bits of board field +124 (pool block count).
- L = requested flash-image size (80000 for our route).
- R = floor(L / U) + 1, held in r6.
- Starting index = (N - R - 2) modulo 65536, held in r9.

It acquires a consecutive block sequence at that index and returns zero if it
cannot acquire the required sequence. On success at C001EB64–EB88:
`staging = C0140000 + starting_index * U`.
This is not a claim that any allocation must succeed or that all firmware builds
share this allocator.

Enquiry2 regenerates its 128-byte response at C001A430, and exposes enough values:

| Response offset | Firmware producer | Interpretation |
|---|---|---|
| 18 | C001A4F8 | Reported DRAM bytes |
| 1C | C001A504–518 | Board +124 multiplied by U |
| 20 | C001A524–530 | Board flash size |
| 68 | C001A5E4 | Low 16 bits of C009C3F8, in 512-byte units |

The pinned live profile yields U=2000, N=739, L=80000, R=41 and index=6F6
(all hexadecimal). Thus staging=C0F2C000 and its reserved extent ends at C0FAE000,
inside the reported 16 MiB DRAM. The firmware reads a dword for +124 when building
Enquiry2 and a halfword in the allocator; the checked model rejects a block count
that would truncate. It also rejects short/wrong-version input, zero units,
non-integral geometry, unsupported flash size, index underflow and DRAM overflow.

`loader/postinit/staging_geometry.py` implements this offline model. It assumes
the exposed 16-bit unit is the actual allocator unit for this profile and geometry
has not changed since allocation. A direct pointer read remains the decisive test.
Evidence is archived in `artifacts/staging-allocation-20261010/allocator-evidence.dis`.

## Live bounded control

Built the unchanged `host/dump/dac960dump.c` on 192.168.2.75 for kernel
6.8.0-138-generic with W=1. On an already driverless controller it issued Enquiry2,
two 512-byte LoadImage reads at offset zero, and Enquiry2 again. Each completion
had matching ID, status zero, unchanged guard and pending=0. Both read buffers
match the first 512 bytes of the archived stock image exactly. Fresh geometry
matches the historical snapshot's geometry.

Three identical control runs were needed: the initial debugfs tar export produced
empty files because the pseudo-files report zero sizes; the second export hit
read-only local permissions inherited from tar. The third used direct `cat` for
each pseudo-file and produced the complete archived capture. Every run completed
with pending=0 and the module was removed cleanly afterward. Final state was
verified driverless. These were firmware read commands (with normal mailbox/DMA
transport writes), not a purely passive PCI inspection. The first image read can
initialize the firmware's staging RAM copy; it does not program flash.

Native dispatcher test and 21 Python tests passed. Tests cover model rejection
and agreement between live and historical inputs. No cross-build of the loader
was necessary because its binary did not change.

## Next concrete verification

A four-byte read of C0112A70 would check the predicted pointer. If the normal
image-read handler permits the same 32-bit offset addition observed in static
code, the derived mailbox offset is FF1E6A70. This exceeds the current harness's
allowed image window, so the existing harness correctly refuses it. Do not relax
that limit globally or expose arbitrary offsets.

A separate fixed-purpose probe must first validate fresh matching geometry and
an ordinary image read, then perform only the derived pointer read with guarded
DMA and matched completions, repeat it, and check for C0F2C000. It must retain
resources on uncertain completion. A predicted address is not yet proof of the
DMA alias or upstream-validation behavior; failure is a stop condition, not a
reason to scan addresses. No such probe was executed in this step.

Even a confirmed pointer would only establish a memory-read route. Cache handling,
quiescence, a RAM payload location and the recovery fault/interrupt setup must be
reviewed before any execution handoff. Photos and later serial access remain
useful for independent recovery entry, but are not needed for this offline work.

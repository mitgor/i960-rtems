# SSH-only recovery-entry investigation — 2026-10-10

Latest: [RAM-WRITE-VERIFIED.md](RAM-WRITE-VERIFIED.md). Fixed 16-byte scratch upload/readback/restoration passed at C0FAC010 in the extra staging allocation block. All 22 commands clean; original 64 bytes restored, probe removed. No execution/recovery/flash.

Latest: [RUNTIME-READ-VERIFIED.md](RUNTIME-READ-VERIFIED.md). Paired live reads verified entry bytes, board C0110780, alias C1000000 and 512 KiB callbacks. Hardened exact read allowlist passed; no upload/execution/recovery/flash.

Latest: [STAGING-POINTER-VERIFIED.md](STAGING-POINTER-VERIFIED.md). Live paired four-byte reads confirmed C0F2C000 at C0112A70. Fixed-purpose read gate only; no upload, execution, recovery entry or flash. Probe removed cleanly.

Latest: [STAGING-ALLOCATION.md](STAGING-ALLOCATION.md). Enquiry2 plus the traced allocator predict C0F2C000; fresh paired in-window reads passed. The pointer has not been directly observed; the normal harness still rejects out-of-window offsets.

**No non-destructive recovery transition has yet been demonstrated.** A possible
RAM-access route has been identified in the matching firmware, but it is not a
validated command for entering recovery. No card command, RAM upload, MMIO write,
PCI configuration write, driver bind/unbind, reset or flash occurred in this step.

SSH was initially unavailable. After the user brought the PC online, read-only
PCI inventory and the existing preflight passed: normal device 1069:0010,
driverless, command 0006, BAR0 EE000000/8192 bytes, no dump module. The bridge
function's sysfs resource table showed no assigned BAR; the controller has its
known MU aperture, not an established general DRAM mapping. There was no output
from listing `/dev/serial/by-id`; that does not exclude other serial devices.
The BIOS-menu setting was not read and cannot be inferred from these observations.

## Paths checked

| Lead | Evidence | Result |
|---|---|---|
| Opcode 53 | Dispatch C001FBA8 branches to C0017770; copies information to a host DMA buffer | Not a recovery entry in this traced handler |
| 2B/subcommand 20 (hex 14) | C0020954 calls board callback +F0; the traced C00209B0 routine configures host mailbox addresses/ATU translation | Not evidence of arbitrary execution; active callback selection still needs verification |
| SYSCTL routine C004CA90 | Hard-coded 300, FEFC8000 and FEFC8B10 | Does not target the installed boot-block fallback. No direct reference to this routine was found in the unpacked disassembly |
| Boot-block entry literals | No aligned literals for FEFFC400, FEFFCC30, FEFFCAA8 or FEFFD600 in the decompressed program | Limited negative evidence only; computed/indirect paths remain possible |
| Image upload 21 | Host offset is added to a runtime staging pointer, then passed to DMA | Promising RAM-access lead, not ready for a live write |

The raw bootstrap disassembly includes compressed ZIP bytes that can decode as
spurious instructions. Searching it for `sysctl` without restricting to executable
regions is not valid evidence of another reset path.

## Image-transfer lead

The traced normal-mode upload chain is:

C001FDC8 → scheduled C004CD00 → board callback +E4 = C004CED0 → C004C010 → C004C090.

C004CED0 reads a 16-bit byte count from mailbox +2, a 32-bit offset from +4,
and host DMA address from +8. At C004CEE4 it adds that offset to the staging
pointer returned by C004D230. The traced handler and DMA helpers do not visibly
compare that result against staging bounds. The DMA helper places the local
address directly into its descriptor at +0C. This suggests the offset may reach
RAM outside staging, subject to address arithmetic, DMA mapping and actual
upstream validation. It does not establish a safe arbitrary-memory primitive.

The staging pointer variable is C0112A70; its current value is **unknown**. The
allocator produces it at runtime. The read handler's analogous addressing offers
a possible way to validate a route before any write, but knowing a variable's
address is not enough when all offsets are relative to the unknown pointer.
We did not guess a staging base or probe unbounded offsets: those could reach
registers or invalid bus addresses, or wedge the controller.

There are also prerequisites beyond address reachability: the handler invokes
C0033980's quiescence checks, DMA may access aliases differently from the CPU,
code caches need handling, and a recovery handoff needs the fault/interrupt setup
performed by boot code. Writing a function pointer and jumping straight to the
monitor is not yet a reviewed transition. Leaving flash unchanged would still
allow a RAM experiment to hang the card or interfere with the host.

## Evidence, instructions and next bounded work

[artifacts/ssh-recovery-investigation-20261010/](artifacts/ssh-recovery-investigation-20261010/)
contains the live preflight, firmware hash, search results and disassembly excerpts.
The normal live harness remains restricted to its previously supported reads;
no unrestricted opcode or RAM-write facility was added.

Next is tracing the allocator/staging-base placement and checking whether an
already understood response can disclose that address. Only after a concrete,
bounded address calculation is established should a known-data RAM read be
considered. A RAM upload and recovery handoff require a separate code/side-effect
review. This is still investigation, not a promise of a software-only solution.

For later physical work, follow [SERIAL-RECOVERY-SETUP.md](SERIAL-RECOVERY-SETUP.md):
identify the board/header and electrical interface first, then record receive-only
output. A serial adapter may provide the practical recovery-entry route if no
safe stock-firmware software entry can be established.

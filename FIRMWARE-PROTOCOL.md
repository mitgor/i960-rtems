# In-system firmware access via the DAC960 mailbox (feasibility + map)

**Verdict: an in-system firmware dump (and flash) looks feasible — no external programmer
needed — but it requires host DMA (vfio-pci) and reversing three command parameter
layouts that the Linux driver never implemented. A safe read-only test (`Enquiry`) is the
gate before anything risky.**

This came from asking "what can the x86 BIOS do for us." Answer: the BIOS itself isn't
worth modifying, but it (and the Linux `DAC960` header) document the **host→i960 command
mailbox**, which is the real lever.

## Key realization

The DAC960-PG register window is **`DAC960_PG_RegisterWindowSize = 0x2000` (8 KB)** — the
**same 8 KB BAR0** we already map at PCI `0xee000000`. So the host can drive the i960
firmware's command mailbox **directly through BAR0**. No BIOS execution, no DOS.

## The PG mailbox interface (from Linux `DAC960.h`, GPL-2.0)

Register offsets within BAR0:

| Offset | Register |
|--------|----------|
| `0x0020` | Inbound doorbell (W: b0=NewCmd, b1=AckStatus, b2=GenInt, b3=Reset; R: b0=MailboxFull, b1=InitInProgress) |
| `0x002C` | Outbound doorbell (W: b0=AckHWMbxInt; R: b0=StatusAvailable) |
| `0x0034` | Interrupt mask (0xFF = disabled) |
| `0x1000` | Command opcode (byte) |
| `0x1001` | Command identifier (byte) |
| `0x1002`–`0x100C` | Command mailbox params (bytes 2–12) |
| `0x1018` | Status command identifier |
| `0x101A` | Status word |
| `0x103F` | Error status (b2=pending; clear by `writeb(0)`) |

**Issue-a-command sequence:** write opcode+params to `0x1000..`, set inbound doorbell b0,
poll until inbound-doorbell b0 (MailboxFull) clears and outbound-doorbell b0
(StatusAvailable) sets, read status at `0x101A`, write outbound-doorbell b0 to ack.

## The commands that matter (V1 opcode enum)

| Opcode | Name | Use to us |
|--------|------|-----------|
| `0x53` | `Enquiry` | **Safe** read-only probe — proves mailbox + DMA work |
| `0x1C` | `Enquiry2` | more controller/firmware detail |
| `0x20` | `LoadImage` | host downloads an image **into** the i960 |
| `0x21` | `StoreImage` | read an image **out** → **in-system firmware dump/backup** |
| `0x22` | `ProgramImage` | commit image to flash → **in-system reflash** |

## What's confirmed vs. still unknown

**Confirmed:** the mailbox layout, doorbell protocol, opcodes, and that BAR0 is the register
window. The card is a PCI bus master, so data-transfer commands DMA to/from a host bus
address placed in the mailbox.

**Unknown (must be reversed from the x86 ROM — the Linux driver only has the *names* of
0x20/0x21/0x22, not their mailbox parameter layout):**
- The exact mailbox fields for `StoreImage`/`LoadImage`/`ProgramImage`: where the 32-bit DMA
  bus address goes, the transfer length, and any flash offset / image-header expectations.
- Whether `ProgramImage` validates an image header/checksum (likely) or a signature
  (unlikely for this era — so a custom image probably flashes).
- Whether `LoadImage` alone *executes* the downloaded image (holy grail: run custom i960
  code in RAM with zero flash risk, reversible by power-cycle) or merely stages it for
  `ProgramImage`. Unknown — worth probing.

## Safe build/verify order (for a `host/myflash` tool)

1. **DMA setup:** bind the device to **vfio-pci** (unbind `myrb` first). vfio gives userspace
   a BAR0 mmap *and* a pinned DMA buffer with an IOVA the card can target — the correct,
   IOMMU-safe way (avoids a custom kernel module and avoids `/dev/mem` DMA guesswork).
2. **`Enquiry` (0x53):** issue it, have the card DMA the enquiry struct to the buffer, read
   it back. Read-only. If this returns sane controller/firmware data → the whole channel
   works. **Do not proceed past here until this passes.**
3. **`StoreImage` (0x21):** reverse its params from the ROM, dump the firmware to a file.
   This is the backup that was otherwise impossible in-system. Verify it (size, i960 IBR at
   top, sane disassembly with `i960-elf-objdump`).
4. **Only with a verified dump in hand:** experiment with `LoadImage` (try to run custom
   code in RAM) and, last of all, `ProgramImage` (flash a custom image). A bad
   `ProgramImage` bricks the card — the step-3 dump is the only recovery.

## Risk summary
- Steps 1–3 are read-only/non-destructive (Enquiry and, believed, StoreImage).
- `ProgramImage` writes flash — do it only after a verified StoreImage dump, or keep the
  external-programmer backup (`REFLASH.md`) as the safety net.
- Driving a bus-master device from userspace is why vfio-pci (not `/dev/mem`) is the right
  tool; a wrong DMA address with an IOMMU off could corrupt host memory.

---

## Progress

### Milestone 0 — read-only register probe: DONE (validated)
`host/myflash.c probe` mmaps BAR0 (`0xee000000`) read-only via `/dev/mem` and reads the PG
registers. Live result on the card:
```
irq mask [0x34]   = 0xfb   <- exactly the driver's "interrupts enabled" value (Mask1=3,Mask2=0x1F)
inbound dbell      = 0x00   (mailbox idle, init done)
outbound dbell     = 0x00   (no status pending)
error status       = 0x00
cmd mailbox        = 2b 00 14 00 00 10 fe ff 00 00 fe ff 00  (stale; fe ff = i960 local addrs)
```
This confirms BAR0 is the live PG register window and the firmware is up. Safe, non-destructive.

### Blocker before milestone 1 (Enquiry)
Issuing commands needs the card detached from `myrb` (two masters on one mailbox = corruption).
But `myrb`'s sysfs **unbind/bind wedges in uninterruptible D-state** on this controller (the
driver's probe/remove hangs talking to the firmware). Clearing it and freeing the card requires:
```
# /etc/modprobe.d/blacklist-myrb.conf
blacklist myrb
```
then `sudo update-initramfs -u && sudo reboot`. The device then comes up driverless; bind it to
`vfio-pci` (for IOMMU-safe DMA) or drive BAR0 directly. **Rollback:** delete that file,
`update-initramfs -u`, reboot. (The box has an active Intel IOMMU `dmar0`, so vfio-pci is the
correct DMA path for the Enquiry/StoreImage data transfers.)

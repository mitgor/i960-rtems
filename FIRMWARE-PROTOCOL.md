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

### Milestone 1 — in-system Enquiry via the mailbox: DONE (end-to-end)
`host/kmod/dac960probe.ko` binds the (blacklisted-myrb) card and issues the read-only
`Enquiry2` (0x1C) through the PG hardware mailbox, with the result DMA'd into a
`dma_alloc_coherent` buffer (IOMMU-correct for the DMA-FQ group). Bounded polling — cannot
wedge. Live result:
```
status = 0x0000 (success)
result[0..7] = 15 01 02 03 04 07 1d 30
  HardwareID: submodel=21 model=2    i960 Firmware: v4.07-29
IOVA = 0xfffeb000 (IOMMU-mapped; 32-bit card DMA succeeded)
```
This proves the full host->i960 command path works in-system: mailbox issue + bus-master
DMA + completion handshake. No BIOS, no external programmer. The same machinery now extends
to `StoreImage` (0x21, dump firmware — read-only) and later `ProgramImage` (0x22, flash).

**Next:** reverse `StoreImage`'s mailbox params (transfer length / flash offset) from the
x86 ROM, dump the firmware to a verified backup, then (only after that) explore `LoadImage`
to run custom i960 code in RAM, and `ProgramImage` to flash it.

### Operational notes
- `myrb` is blacklisted (`/etc/modprobe.d/blacklist-myrb.conf`); card comes up driverless.
  Rollback: delete that file, `sudo update-initramfs -u`, reboot.
- Never let `myrb` and a custom driver both touch the mailbox. `myrb`'s unbind wedges in
  D-state on this controller — blacklist + reboot is the clean way to free the card.
- `host/kmod/` builds against the running kernel headers; `insmod` binds, `rmmod` releases
  cleanly (bounded, no wedge).

### Milestone 2 attempt — StoreImage (0x21) in-system dump: BLOCKED (safely)
Extended `dac960probe.ko` to issue `StoreImage` (0x21) as a Type3 command (BusAddress =
a 512 KB sentinel-filled DMA buffer), with a hard interlock refusing `0x22` (ProgramImage/
burn). Result:
```
cmd=0x21  status=0x0000 (accepted)  changed=0/524288 bytes   <- nothing transferred
cmd=0x1c  status=0x0000  changed=128/4096 bytes              <- Enquiry2 control: exactly 128 B
```
So `StoreImage` is **benign** (status OK, no flash touched — confirms 0x21 is not the burn)
but the simple Type3 form does **not** dump: it's either host->card, or needs undocumented
parameters (transfer length / flash offset / image selector). Those parameters appear in
**no** open-source driver (Linux and FreeBSD both omit the firmware commands) and were not
cheaply recoverable from the real-mode x86 ROM. Recovering them means reversing the DOS
`DACFL`/flash utility (which we don't have) or a much deeper ROM effort.

**Decision:** stop here on the in-system dump. Guessing image-command parameters borders the
destructive `ProgramImage` (0x22) path, and this is the only card. The firmware (v4.07-29)
is confirmed intact after all probes.

## Conclusion
- **Proven:** the in-system host->i960 command channel (BAR0 mailbox + bus-master DMA +
  completion) works — `Enquiry2` returns correct data every time. This is the hard, reusable
  part and the basis for any in-system firmware tool.
- **Not achieved in-system:** the firmware dump, because `StoreImage`'s exact parameters are
  undocumented. The **guaranteed** firmware backup remains the external programmer
  (`REFLASH.md` §3).
- **To finish in-system later:** obtain the DOS `DACFL` flash utility and reverse its
  `StoreImage`/`ProgramImage` mailbox parameter layout, then extend `dac960probe` accordingly
  (dump first, verify, only then flash). The command plumbing is already done here.

### Milestone 2 update — in-system dump blocked on a flash-enable step
Implemented StoreImage(0x21) with the flasher's exact Type-3D layout (len@2-3 bytes <=0xF000,
absolute flash offset@4-7, DMA busaddr@8-11) via the proven PG mailbox. Then, per the flasher
disassembly, implemented the precondition `0x2B subcmd 0x02` (Read Flash Descriptor Table).

Result on the live card: **both `0x2B/02` and `0x21` return `status=0x0000` but DMA zero bytes**
(buffer stays at the 0xA5 sentinel), whereas `Enquiry2 (0x1C)` on the identical mailbox path
DMAs its 128 bytes correctly. So the running firmware **acks flash commands but ignores them**
in its normal operational state — a flash-access enable / maintenance mode / window setup that
the flasher performs at controller-open is still missing. The flasher's recurring string
"Mapping Flash to Physical Address %lxH" suggests the PG flash read may be **memory-mapped**
(flash exposed in a host PCI window the flasher programs) rather than the 0x2B/0x21 mailbox.
Under investigation.

**Guaranteed dump route remains the external programmer (`REFLASH.md` §3).** The in-system
command channel is proven (Enquiry); the flash-read path needs the PG open/enable sequence.

### CONCLUSION — an in-system FULL firmware dump is not possible on this card
Three independent mechanisms were tried and each is definitively closed:

1. **Mailbox flash commands are inert.** `0x2B/02` (Read Flash Descriptor Table) and `0x21`
   (StoreImage) both return `status=0x0000` with **zero DMA** on the live card, while
   `Enquiry2 (0x1C)` DMAs correctly on the identical path. The flasher disassembly confirms the
   PG field firmware does not service these for image transfer.
2. **No host-visible flash window exists.** The card exposes only BAR0 (8 KB) and the Expansion
   ROM (32 KB). A read-only scan of all 8 KB of BAR0 shows a sparse *register* window (8087/8192
   bytes zero, 20 distinct byte values, `+0x60..0x80` all zero) with **no** flash signature
   (`MIMG`/`Mylex`/`DAC960`/`55AA`). The Expansion ROM aperture exposes only the 28 KB x86 option
   ROM (already dumped — see `artifacts/`), not the i960 firmware.
   - Note: the flasher's memory-mapped `window+0x68` flash path lives in its **"FootBridge"**
     module — FootBridge is the Intel 21285 companion for **StrongARM**-based DAC960s
     (AcceleRAID/eXtremeRAID), **not** the i960RP. It does not apply to this card.
3. **ATU remapping is closed.** The i960RP address-translation window registers did not accept
   host-side writes, so the host cannot create a window onto the i960 local bus where flash lives.

**Therefore:** the full i960 firmware can only be read with an **external programmer**
(`REFLASH.md` §3). This is not blocking: the decoded official firmware images
(`407t39b0.bin` for 4.07-0-39, and the PRL package's `Fgj40729.img` for 4.07-0-29) serve as
reference images, and the in-system x86 BIOS dump is already captured.

**What in-system access DID achieve:** a proven host→i960 command channel (Enquiry), the full
PG register map, and the x86 BIOS dump — all without any external hardware.

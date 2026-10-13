# i960 / Mylex DAC960PG — consolidated technical findings

**Current index (2026-10-11): [findings, evidence and unresolved questions](CURRENT-FINDINGS.md).** Earlier milestone notes below retain their historical context.

**Current result:** [In-system recovery succeeded](docs/firmware/SNAPSHOT-RECOVERY.md). A paired
512 KiB capture contains the exact 4.07-0-29 firmware and FWTCBBLK boot block,
plus the independently verified PCI BIOS. This supersedes older no-dump status
and the 256 KiB layout assumption below.

> **Latest follow-up:** [VENDOR-READ-PATH.md](docs/firmware/VENDOR-READ-PATH.md) corrects the
> vendor symbol addresses and verifies opcode 0x20 card-to-host transfers.
> Returned bytes appear to be staging memory; no physical-flash backup exists.
> Opcode 0x21 uploads host bytes and must not be used as a dump command.


> **2026-10-10 live-attempt update:** See [DUMP-ATTEMPT.md](docs/firmware/DUMP-ATTEMPT.md).
> Fresh, matched-ID 0x21 transactions left host buffers untouched; Enquiry2 worked.
> Vendor-code dataflow also puts the claimed card-to-host direction of 0x21 in
> doubt. Historical “safe StoreImage dump” statements below are superseded;
> no verified firmware-read procedure exists yet.

Reverse-engineering notes from repurposing a retired Mylex DAC960PG RAID controller (Intel
i960RP) as a general-purpose i960 computer. One Ubuntu host drives the card; all card work
is on the user's own hardware. Detailed write-ups are cross-referenced; this file is the
index + the headline discoveries.

## 1. Hardware identity
- **Card:** Mylex DAC960PG; core CPU **Intel i960RP** (80960RP), a **BGA** package.
- **PCI:** bridge `37:09.0 [8086:0960]`, controller `37:09.1 [1069:0010]`.
- **BAR0:** one 8 KB (`0x2000`) memory window at `0xee000000` — this is exactly the DAC960
  **PG register window**.
- **Firmware v4.07-0-29**, **BIOS v4.10** (read live; see §3).
- i960 boots its Initialization Boot Record (IBR) from flash at fixed `0xFEFFFF30`.

## 2. Reset mode / running custom code on the silicon
- Live **EBCR** (bridge PCI cfg `0x40`) = `0x0018` ⇒ **Mode 2**: the core boots its own flash
  firmware at power-on; primary PCI accepts config. (Not the host-loadable "Mode 0".)
- Mode is strapped by `RST_MODE#`/`RETRY` pins sampled at `P_RST#`. Forcing Mode 0 would be a
  **board-level resistor change** — the 80960RP is BGA, so there is no chip leg to cut, and
  Mode 0 alone still boots the flash IBR anyway. → see [MODE0.md](docs/firmware/MODE0.md).
- The robust way to run custom code on real silicon is **reflashing the boot flash**
  → see [REFLASH.md](docs/firmware/REFLASH.md).

## 3. In-system host→i960 command channel (PROVEN)
The host can drive the running firmware's command mailbox directly through BAR0 — no BIOS, no
DOS, no external programmer. Confirmed by a small kernel module (`host/kmod/dac960probe.c`)
that binds the card (after `myrb` is blacklisted) and uses the kernel DMA API.

**PG register map (within BAR0, from the Linux `DAC960` header, verified live):**
| offset | register |
|---|---|
| `0x1000` | command mailbox: opcode@0, id@1, params@2–12 (13 bytes) |
| `0x0020` | inbound doorbell (bit0 = new command, bit1 = ack status) |
| `0x002C` | outbound doorbell (bit0 = status available) |
| `0x101A` | status word |
| `0x0034` | interrupt mask (`0xfb` = enabled — matched live) |

Type-3 mailbox: opcode@0, id@1, dummy@2–7, 32-bit DMA **BusAddress@8–11**.
**Verified:** `Enquiry2` (0x1C) returns correct data (firmware v4.07-0-29), `status=0x0000`,
DMA into an IOMMU-mapped buffer. → see [FIRMWARE-PROTOCOL.md](docs/firmware/FIRMWARE-PROTOCOL.md).

**Environment gotchas:**
- `myrb`'s sysfs unbind **wedges in D-state** on this controller → it is blacklisted
  (`/etc/modprobe.d/blacklist-myrb.conf`); card comes up driverless. Rollback documented.
- IOMMU group 14 (`DMA-FQ`) is **not isolated** (shares with FireWire `37:05.0` + bridge
  `00:1e.0`) ⇒ **vfio-pci passthrough is out**; a purpose-built kernel module with
  `dma_alloc_coherent` is the correct DMA path.

## 4. Fujitsu GlobalFlash container encoding — CRACKED
The official firmware package (`DAC960FL.EXE` DOS flasher + `.img` payloads, from Fujitsu's
server, see [FIRMWARE-PACKAGE.md](docs/firmware/FIRMWARE-PACKAGE.md)) stores its payloads in a Fujitsu
"GlobalFlash" encoding. It is **not compression** — a deterministic, keyless per-byte transform:

```
decoded = PERM( stored XOR 0xC3 )
```
where **`PERM` swaps bit *i* with bit *i*⊕6** (bit0↔bit6, bit1↔bit7, bit2↔bit4, bit3↔bit5) and
is its **own inverse**. It coincides with a plain `XOR 0xC3` only on the permutation-invariant
bytes (`00 ff 55 aa 5a c3 3c …`) — which is exactly why whole-file `XOR 0xC3` never revealed
strings and misled the first attempts.

- **How it was cracked:** crib-dragging the card's *plaintext* BIOS dump against the *encoded*
  `BGJ41041.IMG`; five shared BIOS strings gave one consistent byte map that solved to the
  clean `PERM∘xor` form over GF(2). Confirmed deterministic because `DAC960FL.EXE` and
  `BGJ41041.IMG` are **byte-identical** across two different packages (DAC960PG and PRL).
- **Container structure:** `.IMG` files have a **512-byte header** (`MIMGMYLX` + ASCII
  `"Ver 4.10-41 Released on Feb 02 1999"`); raw image at **offset 512**. `DAC960FL.EXE` has
  **no** header (encoded from byte 0).
- **Decoder:** [`host/globalflash_decode.py`](host/globalflash_decode.py) (independently
  verified: yields a valid `MZ` DOS exe and a `55AA` option ROM with real strings).
- The i960 firmware payload is itself **Huffman-packed** internally ("Out of Huffman table
  space!", "Bad CRC %x").

## 5. Firmware image command protocol (from the decoded flasher)
V1 firmware-image opcodes (the Linux/FreeBSD drivers implement none of these):
- **`StoreImage` (0x21) — card→host bulk READ (the safe dump).** Type-3D mailbox:

  | bytes | field |
  |---|---|
  | 0 | opcode `0x21` |
  | 1 | id / unit |
  | 2–3 | transfer length (chunked ≤ `0xF000`) |
  | 4–7 | flash/image byte offset |
  | 8–11 | 32-bit DMA bus address |
  | 12 | status (card-filled) |

- **`0x2B`** — flash-descriptor-table / config DMA (subcommand@byte2, fixed buffer).
- **Flash WRITE is memory-mapped, not a mailbox opcode** — the flasher maps the flash into a
  PCI window and does erase-block / write-word directly ("Erasing Flash BlockNo %xH",
  "Writing FlashAddr %lxH"). So there is **no single destructive `ProgramImage` command**;
  `0x20`/`0x22` are not used by the utility.

**In-system dump: CLOSED (negative result, well-evidenced).** Flash mailbox commands
(`0x2B/02`, `0x21`) are inert in field firmware (status=0, zero DMA, while Enquiry2 works on the
same path); the card exposes no host-visible flash window (BAR0's 8 KB is a sparse register
window — no flash signatures; the Expansion ROM holds only the x86 BIOS); and ATU remapping
refuses host writes. The flasher's memory-mapped `window+0x68` path belongs to its "FootBridge"
(StrongARM) module, not the i960RP. => a full firmware read needs an **external programmer**
(REFLASH.md §3); the decoded official images serve as reference. See FIRMWARE-PROTOCOL.md.

## 6. The x86 BIOS (option ROM)
Plaintext 28 KB option ROM (`55AA`, init `0x3000`, PCIR `1069:0010`, v4.10). It discovers the
card via **PCI BIOS INT 1A**, enters **unreal mode** (`lgdt` + `cr0` PE-bit toggle) to reach
the BAR0 mailbox at `0xee000000`, uses low RAM seg `0x7000` as the DMA buffer, loads the Alt-R
RAID config utility, and hooks INT 13h. It **checks** firmware but does **not** flash it.
→ see [BIOS-ANALYSIS.md](docs/firmware/BIOS-ANALYSIS.md). Dump + disassembly in [artifacts/](artifacts).

## 7. Toolchain + emulator (the working deliverable today)
- i960 cross-toolchain built from source (binutils 2.27 + gcc 3.3.6; `i960-coff-gcc -mrp`).
- `game/` Tetris compiles to `elf32-i960` and runs on `host/emu.c`, a compact i960
  interpreter that executes the real machine code and renders a text-mode framebuffer.
  Two self-checks match a native build exactly. → see [README.md](README.md), [MANUAL.md](docs/project/MANUAL.md).

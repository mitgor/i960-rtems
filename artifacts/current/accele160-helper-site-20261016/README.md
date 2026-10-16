# AcceleRAID 160 firmware-helper site audit

2026-10-16. This is an **offline** investigation of the accepted paired stock
6.00-05 full-flash dump. No candidate was written to disk for programming, and
no card command, MMIO write, flash write, driver change or reboot was issued.
The old DAC960PG remained unbound and untouched.

## What the stock image proves

The IOCTL diagnostic dispatcher reads a subcommand byte from command offset
`+0x15`, subtracts one, bounds the index, and uses the table at
`0xc00232c4`. Subcommand `0x8e` reaches `0xc002371c`, which loads the
function-table `+0xfc` callback and branches to it. The normal callback is
`c0023910`, the existing `SET_MEM_MBOX` implementation. Subcommand `0x8f`
instead reaches the stock unsupported-command path at `c0023790`, which sets
status `0x104` and completes. This makes `0x8f` the cleaner *potential*
extension point: normal `0x8e` behavior could remain unchanged. It is not a
usable extension until the dispatcher table and command/response contract are
implemented and tested.

The archived Linux `myrs.h` describes a 64-byte command mailbox: byte 2 is
main opcode `0x20` (IOCTL), byte 21 is the IOCTL subcommand, bytes 22–31 are
reserved in the common form, and bytes 32–63 hold DMA descriptors. The
firmware dispatcher reads byte 21 from its command object. We have not yet
proved that the other host mailbox bytes arrive unchanged at this point, or
that an `0x8f` request with no DMA can be issued and completed through the
currently loaded `myrsread` extension without disturbing its retained state.

The 24 KiB uncompressed loader copy contains 7,720 erased (`0xff`) bytes from
loader offset `0x41d8` to its end. The copy maps that range to local RAM
`0xc000e1d8..0xc000ffff`. An aligned absolute-word scan of the loader and
expanded runtime found no pointer into that range. This is a **candidate code
site**, not proven owned RAM: indirect branches, runtime allocations, board
variants and boot-time use remain to be ruled out. Eight loader instructions
initialize the normal `+0xfc` callback to `c0023910`, across board profiles;
changing only one would be unreliable. Directly patching that callback in live
RAM remains invalid because external writes do not snoop the 80303 caches.

## Offline image-packaging rehearsal

[`audit_helper_site.py`](../../../host/accele160/startup/audit_helper_site.py)
inserts the existing 80-byte bounded probe into the erased loader space **in
memory only**, recomputes the loader additive checksum and trailer additive
checksum, and reruns the stock image analyzer. It verifies the expanded runtime
is byte-for-byte unchanged and restricts the diff to the 80-byte probe and the
two checksum words. The [receipt](audit.json) records a candidate SHA-256 and
88 changed bytes. This candidate is deliberately **dormant**: no entry points
to it, no full vendor-image validation, and no recovery test. The tool has no
option to export or program this image.

Reproduce from the repository root:

```sh
python3 host/accele160/startup/audit_helper_site.py \
  artifacts/current/accele160-guarded-20261016/rawflash-0/data.bin \
  artifacts/current/accele160-startup-20261016/probe.bin
python3 -m unittest discover -s host/accele160/startup -p 'test_*.py'
```

## Remaining implementation gates

1. Finish the diagnostic command/completion ABI for `0x8f`: map the full host
   mailbox into the internal command object, then establish DMA ownership,
   error status, timeout and concurrent-request behavior. The stock unsupported
   path is the behavior to preserve for malformed requests.
2. Decide how to change the expanded-runtime table. The main image is ZIP
   method 6 (Implode); this repository can unpack it, but has no validated
   packer. A loader-time patch after decompression is an alternative only after
   its timing, cache state and boot variants are traced. Replacing the normal
   `0x8e` callback is less attractive because eight loader initializers set it
   and every unrecognized request must transparently delegate to stock code.
3. Prove an owned code/result/stack allocation. The successful 256-byte
   self-restoring PCI upload proved transport, not permanent ownership.
4. Define a narrowly admitted request (exact version, nonce, lengths, ranges
   and checksum), on-card D/I-cache maintenance, a bounded normal-return call,
   and a completion record that survives STOP/timeout. Exercise rejection and
   restoration in a native model before hardware.
5. Verify a real modified image with **all** vendor admission checks, paired
   complete readbacks, a credible recovery path, and a boot/return plan before
   considering any flash write. Current checksum success alone is insufficient.

The next useful coding task is the command/completion ABI audit and a native
request validator for `0x8f`. No hardware execution is justified yet.

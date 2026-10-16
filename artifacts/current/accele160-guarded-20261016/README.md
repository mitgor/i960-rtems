# AcceleRAID 160: complete stock flash, 2026-10-16

## Accepted result

`rawflash-0/data.bin` and `rawflash-1/data.bin` are identical **1,048,576-byte
full flash images**, not a reconstruction with invented padding. SHA256:

```
0a951782a7ccd1855746ffeb3a1b64563287bc56e0dce77d63b79c71ec3b502a
```

Both live reads completed with status 0, residual 0 and zero changed DMA guard
bytes. Offset matches: boot `0xf0000`, main firmware `0x40000`, BIOS `0x30000`,
diagnostics `0xc0000`, descriptor `0xe0000`. The first three match the earlier
independent paired captures; BIOS also matches the PCI ROM capture. Firmware
and EZAssist ZIP contents pass decompressed length and CRC checks. These are
in-system reads; no external-programmer comparison has been performed.

Old DAC960PG `0000:37:04.1` was unbound and received no targeted operations.
Only AcceleRAID `0000:37:09.1` was addressed. No flash programming was performed.

## Protocol and the previous freeze

READIMAGE uses opcode `0x20`, IOCTL `0x2d`, selector byte 22. The normal range
handler uses the word at byte 16 in 1024-byte units. The accepted full reads use
**selector 9, offset 0, length 1048576**. Stock runtime disassembly shows selector
9 maps from flash offset zero to the actual flash size. Its normal reader copies
flash into temporary controller RAM, then transfers the requested extent.
The intervening routine at file offset `0x45088` is a no-op, not a transformation.

Selector 4 takes a different path: it decompresses EZAssist directly into host
memory without respecting the supplied compressed-image length. Our aligned
164576-byte request produced 551078 bytes, overrunning the requested extent by
386502 bytes. A 1 MiB suffix allocation contained the write. There were 386314
changed sentinel bytes (some output bytes equal the sentinel). The retained
allocation exactly matches EZASSIST.ROM extracted from the complete flash;
prefix and all bytes after the expanded image remain `0xa5`. Prior-boot logs
contain DMA write faults, consistent with the earlier unguarded host freeze.
Alignment alone therefore does not solve this protocol mismatch. Selector 4 is
now excluded from the reader allowlist; extract EZAssist from selector 9 offline.
There is no evidence here that the old card caused the failure.

## Guards, evidence and reproduction

The companion requires explicit new-card PCI identity/BDF, exact `myrsread`
parent, word-aligned size, 64 KiB prefix and 1 MiB suffix guards, serialized
commands, retained DMA lifetime and successful completion before release.
A failed completion or guard check retains the module and allocation. The Python
wrapper also checks old-card binding, absent storage devices and exact accepted
sizes. Its final post-test hardening parses status fields exactly and rejects
another pending READIMAGE; these wrapper checks were added after the live runs.

`tested-readers.tar.gz` retains the exact tested source, modules, header and
Makefiles, including the failed guarded selector-4 reader and successful separate
`rawreader`. `stock-runtime-readimage.txt` contains selected disassembly from the
actual dumped firmware; addresses are file offsets. Request/result receipts
record boot, module hash, identity and status. `retained-ezassist` holds one
losslessly compressed owned-allocation capture and the receipt confirming its
second read matched. `previous` retains the prior module and kernel fault log.

Offline verification (from repository root, requires Python 3 and `unzip` with
method-6 support):

```sh
python3 host/accele160/readimage/verify_full_dump.py \
  artifacts/current/accele160-guarded-20261016 \
  artifacts/current/accele160-readimage-20261016/fresh
python3 -m unittest discover -s host/accele160/readimage -p 'test_*.py'
```

For a future controlled live repeat, use the archived exact driver/header build
and the reviewed wrapper, explicit BDF, `rawreader.ko`, selector 9 and length
1048576. Do not reinitialize/unbind a running or retained driver to obtain it.
The current complete backup removes any need for more live image-selector probes.

## Final state and next work

SSH remained healthy after both full reads; no new DMAR faults appeared. The
successful raw readers released their allocations and unloaded. The failed
selector-4 companion and its owned buffer remain pinned until the next reboot:
**do not forcibly unload/unbind them**. Temporary myrs blacklist was removed,
initramfs rebuilt, existing old-card myrb rules left unchanged. No reboot was
needed to finish this acceptance; the old card remained untouched.

Next work can proceed offline: map startup, RAM and host-command interfaces from
the complete stock image, then design a bounded new-card execution proof. The
old PG runtime/firmware must not be loaded onto this card without that work.

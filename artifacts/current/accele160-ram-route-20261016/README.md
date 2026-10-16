# AcceleRAID 160 RAM upload route

Date: 2026-10-16. Target: new AcceleRAID 160 `0000:37:09.1`, identity
`1069:0050` / subsystem `1069:0054`, stock firmware 6.00-05. The old DAC960PG
`0000:37:04.1` remained unbound and untouched for every live operation.

## Accepted result

The Intel 80303 primary inbound ATU was decoded from its primary manual and the
live PCI configuration:

| Register | Value |
| --- | --- |
| PIABAR / BAR0 | `0xee002008` |
| PIALR / config `0x40` | `0xffffe000` |
| PIATVR / config `0x44` | `0xc0000000` |

BAR0 is 8 KiB. Its first 4 KiB is the 80303 Messaging Unit; its upper 4 KiB
translates to local `0xc0001000..0xc0001fff`. Read-only PIATVR remaps were always
restored under a shell exit trap and confirmed the runtime function-table pointer
without accessing the old card.

The accepted live write was a self-restoring 256-byte round trip at BAR offset
`0x1e00`, local address `0xc0001e00`. Preconditions established the entire upper
4 KiB page was stable zero data. The replacement record contained 64-byte guard
padding, the exact 80-byte probe already retained in
`../accele160-startup-20261016/probe.bin`, and a distinct marker. The helper:

1. compared all 256 target bytes before issuing a store;
2. uploaded the replacement and compared every byte through MMIO;
3. restored all 256 original bytes on every handled post-map exit path;
4. compared the restored bytes;
5. captured the complete upper page again.

It reported `replacement-readback=pass restoration-readback=pass`. Complete
before and after snapshots both hashed to:

```text
ad7facb2586fc6e966c004d7d1d16b024f5805ff7cb47c7a85dabd8b48892ca7
```

PIATVR read back as `c0000000`. SSH stayed responsive. The retained earlier
selector-4 command remained completed and pinned; no pending DMA was disturbed.
No reset, reboot, driver unload, flash operation or disk command occurred.

## Why execution was not attempted

The upload path is proven, but the candidate call path failed its safety check.
The stock diagnostic dispatcher sends IOCTL `0x8e` through function-table slot
`+0xfc` (live stock value `0xc0023910`) into `SET_MEM_MBOX`. Both the function
table and dispatcher lie in regions made cacheable by the stock reset code. The
80303 Developer's Manual sections 4.3.5 and 4.4.6 state that external bus writes
do not snoop either cache. A host-written callback can therefore remain invisible
to the i960 and execute the original memory-mailbox operation. That is neither a
bounded invocation nor a recoverable failure mode.

Other traced routes do not close the gap:

- command opcode `0x01` MEMCOPY resolves a device and enters the normal SCSI
  transfer state machine;
- IOCTL `0x2c`/`0x2d` are allocator-backed StoreImage/ReadImage paths whose
  temporary local state is released during completion;
- IOCTL `0x2e` is a programming path and was not issued;
- zero software-interrupt vector entries alone do not prove the vector cache,
  interrupt frame/return ABI, priority restoration or host-trigger contract.

The bounded probe therefore remains **uploaded/read back only, never called**.
The next execution gate is either a stock command that performs D-cache and
I-cache maintenance on the i960 after host writes, or a fully decoded unused
software-interrupt route with saved/restored vector state and normal return.

## Reproduction tools

`host/accele160/startup/mmio_snapshot.c` is read-only and has no write mode.
`host/accele160/startup/mmio_roundtrip.c` cannot intentionally leave a payload
installed: it requires an exact original-byte comparison and restores the input
on every handled post-map path. Both operate on an explicitly supplied sysfs resource;
selection and identity checks belong in the enclosing harness.

Primary references:

- Intel, *80303 I/O Processor Developer's Manual*, order 273353-001, sections
  4.3.5, 4.4.6, 15.2.1.1, 15.7 and 16.2.
- Intel, *80303 I/O Processor Programming Guide and Initialization*, order
  273395-005, ATU initialization example.

Exact live receipt: [`live-evidence.txt`](live-evidence.txt).

# AcceleRAID 160 cache and interrupt entry audit

Date: 2026-10-16. This is an offline audit of the accepted stock 6.00-05 dump,
followed by a read-only live identity check. No new controller command was
issued and the bounded probe was not executed. The old DAC960PG stayed unbound.

## Result

The firmware contains several `dcctl 2,0` global data-cache invalidations,
but none has a proven bounded host-command route that can be used after a PCI
write to a callback pointer. The clearest direct case is at expanded-runtime
offset `0x386c`: a jump-table entry at `0x377c` points to `0xc001386c`.
The dispatch begins at `0x3678`, gets an input code from a firmware function
pointer at `+0x25c`, subtracts `0x30`, and uses the result to index this table.
Surrounding text is the interactive debug menu. The exact input source and
normal availability of this menu over the current SSH setup are unproven, so
this is not an accepted host command.

The other verified `dcctl 2,0` sites are at runtime file offsets `0x1185c`,
`0x2a42c`, `0x402f8`, `0x404b4`, and `0x40b74`. Their surrounding code handles
controller state, transfer machinery or memory probing; an isolated instruction
does not establish a safe synchronization command. The only verified runtime
`sysctl` instruction is at `0x40404`. It receives `0x300`, which Intel defines
as the **reinitialize** message, not an instruction-cache invalidate. No
callable instruction-cache invalidation gate has been established in the stock
runtime.

Directly posting a software interrupt from the host is also insufficient.
The 80303 caches the highest pending software-interrupt priority internally;
Intel says an external agent must arrange a `sysctl` check for reliable
recognition. It may cache vector entries as well. Writing a zero vector entry
and pending bits would therefore lack a known entry time, a fresh handler
pointer, and a proven restoration path. The Messaging Unit doorbell is a
hardware interrupt that would reuse firmware-owned interrupt routing.

The previous guarded RAM upload/readback/restoration remains valid. A live
execution attempt still fails the cache-coherency and owned-entry preconditions.

## Reproduce the static anchors

From repository root:

```sh
python3 host/accele160/startup/audit_cache_routes.py \
  artifacts/current/accele160-guarded-20261016/rawflash-0/data.bin
```

The script first verifies the accepted 1 MiB dump and expanded-runtime hashes,
then checks exact instruction bytes and the debug-menu jump-table word. Its
output is in [`audit.json`](audit.json). The source dump is already retained;
this batch does not duplicate the binary.
The final [live state](live-state.txt) confirms the same boot, the restored
translation register, and the old card still unbound.

Primary reference: Intel, *80303 I/O Processor Developer's Manual*, order
273353-001, sections 4.3.5, 4.4.6, 6.2.23, 6.2.67, 8.1.4.3, 8.1.6.1-3, and
16.2. The software-interrupt discussion and `sysctl` message table are decisive
for rejecting a host-only pending-bit experiment.

Next viable routes: a **proven** firmware command that invalidates both caches
before a normal-return callback, or a carefully controlled RAM helper entered
through an already verified firmware call route. If neither exists in stock
firmware, a separate, recoverable firmware patch is required. Before any live
execution, identify firmware-owned code/result/stack memory and preserve full
command, ownership and restoration audits.

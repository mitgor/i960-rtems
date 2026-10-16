# AcceleRAID 160 stock debug-interface trace

2026-10-16. This batch traces the accepted 6.00-05 loader and expanded runtime,
and checks a read-only 4 KiB RAM snapshot from the current boot. No command was
sent to the debug menu. No controller command, BAR write, flash write, driver
change or reboot occurred during this trace. The old DAC960PG remained unbound.

## Result

The stock debug interface cannot be used as a bounded SSH upload/call gate in
the present boot. Loader `0xc000d7e0` writes `1` to `0xe0600007`, zero to
`0xe0600006`, and reads `0xe0600007`. Only a readback of `1` selects the real
console callbacks. The live callback table at `0xc048b520` instead contains
the four **stub** pointers. Its input callback `0xc000a230` always returns
ASCII `q` (`0x71`); output callback `0xc000a240` only returns. Thus attaching
a serial cable to the current running card alone would not make the menu
interactive. Why the UART probe failed is not yet established.

The runtime menu at `0xc0013678` calls callback `+0x25c`, masks to one byte,
subtracts ASCII `1` (`0x31`), then dispatches. Input `e` reaches
`0xc001386c` (`dcctl 2,0,g12`), a D-cache invalidate. Input `u` reaches Code
Manager at `0xc0019720`. Its four menu entries display global addresses,
invoke process configuration, initialize memory, or fill memory. The latter
two accept address/length/pattern text and can overwrite controller memory.
There is no verified arbitrary code-call option or I-cache gate here; do not
try the destructive memory menu as a probe. Neither `e` nor `u` is currently
reachable from a host-controlled input source.

The earlier cache audit incorrectly called the D-cache key `d`: it computed
`0x64 - 0x30 = 52`, while the firmware actually computes
`0x65 - 0x31 = 52`. Its table address was correct, but its key label was not.
The [corrected audit](../accele160-cache-gate-20261016/README.md) now verifies
the subtraction instruction and reports `e`.

## Reproduce

From the repository root:

```sh
python3 host/accele160/startup/audit_debug_console.py \
  artifacts/current/accele160-guarded-20261016/rawflash-0/data.bin \
  --live-table artifacts/current/accele160-debug-interface-20261016/live-table-c048b000.bin
python3 host/accele160/startup/audit_cache_routes.py \
  artifacts/current/accele160-guarded-20261016/rawflash-0/data.bin
```

The [audit receipt](audit.json) verifies exact instruction bytes, callbacks,
dispatch targets, and snapshot pointers against the accepted full flash hash.
The [live status](live-state.txt) records the driver/boot state and lack of a
Linux USB serial adapter. `live-table-c048b000.bin` is a read-only local RAM
snapshot; its original collection was a PIATVR remap and page read, followed
by restoration. It is evidence of that boot, not a guarantee after reboot.

## Next gate

A fresh-boot UART presence test would need a confirmed physical UART interface
and an explanation for the failed register readback. Even if the real console
were enabled, its stock menu still lacks a proven normal-return arbitrary call
with both cache-maintenance steps. The more direct engineering path is a
recoverable, narrowly scoped firmware helper that owns scratch RAM, performs
cache maintenance on-card, invokes a bounded returning probe, and reports a
normal completion. Validate the patched image offline against the saved stock
dump before considering a card write. Keep the old DAC960PG untouched.

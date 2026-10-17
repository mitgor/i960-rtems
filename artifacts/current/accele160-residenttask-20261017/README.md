# AcceleRAID 160 post-return RTEMS task, 2026-10-17

**Two accepted RAM-only card batches.** `image/` contains the exact linked
ELF, raw binary, 19-page guarded image, map and symbols. The guarded image
SHA-256 is
`9574e08a321d8374b1ecb3d55a667ae098536634e51decf69174b7f8de4f7f5a`
and FNV `090cb17f`. The stock-coexisting operation-13 firmware remained at
SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
Source and build instructions are in
[`rtems/accele160/residenttask`](../../../rtems/accele160/residenttask/README.md).

`live/accept-0` and `live/accept-1` each contain HALT and no-host expiry,
all 19 page-copy receipts, card-side whole-image digests, callback-return,
task-active, stale-token and terminal snapshots, both ISR stack pages,
firmware-context trace, allocator and page/stage restoration. HALT ended at
tick 22 in 301.436 and 301.353 ms; no-host expiry ended at exactly tick 300
in 3,078.362 and 3,079.001 ms. In both batches the RTEMS task received 2
timer IRQs before HALT and 280 before expiry, after the RTEMS timer callback
fired at tick 20 and operation 13 had returned. The task ignored a wrong
STOP and made progress on its RTEMS stack. Both paths reported zero ISR
faults and restoration flag 1.

`live/pre-flash-{0,1}`, `live/mid-flash-{0,1}` and
`live/post-flash-{0,1}` are six complete guarded 1 MiB reads from boot
`b2f20226-62c9-4f6e-acf1-d543078224f3`; all match the firmware SHA above.
The three independent `preflight`, `midflight` and `postflight` inventories
observed stock timer-1 count/reload/mode zero, pending clear, mask `10c7`,
map `80000` and cached vector 18 `aaaaaaaa`. New card `0000:37:09.1` remained
bound to `myrsread`; old DAC960PG `0000:37:04.1` remained unbound. No flash
write was issued.

Replay from the repository root:

```sh
python3 rtems/accele160/residenttask/verify_live.py artifacts/current/accele160-residenttask-20261017
python3 rtems/accele160/residenttask/test_verify_live.py artifacts/current/accele160-residenttask-20261017
```

Replay passed, and seven independent tamper cases altered flash, allocator
owner, ISR fault, stale token, RTEMS callback, task progress and the task ISR
stack guard; all were rejected. `diagnostic-{0,1}` retain compact completed
HALT captures and guarded host-recovery notes for two host validation errors.
Their obsolete binaries are omitted. The earlier even-page capture is an
alias of the entry page, which is why the final image places task ISR slot 1
on odd page 17.

This is one post-return bounded RTEMS task with whole-instance shutdown. It
does not prove an independent watchdog, DMA ownership or service cleanup for
networking or Doom.

# Safe exclusive-session reuse investigation

**Result:** a reusable resident RTEMS session is a credible next path. Keep
the exclusive grant, kernel and DMA mappings; park only Doom, audit it, then
admit a fresh engine image. No firmware patch or return to stock firmware
is needed. The installed bundle is unchanged and cannot yet restart after
its terminal global STOP. See the [design and next card gate](../../../game/doom/play/accele160/reuse/README.md).

The [live snapshot](card-state.json) confirms that the current card really
is halted: `QUIE`, STOP ACK, no reported fault, DMA phase zero and 1,565
completed transfers; its heartbeat stayed at 15,733 over 250 ms. The selector
was restored to its original `c0000000`, no card command or RAM/flash write
was issued, and the old card remained unbound. Linux reports a `pm` reset
method, but no reset was attempted and no recovery safety is inferred.

The [actual engine experiment](native-result.json) ran three image lifetimes
inside one Linux host32 process, without reinitializing the guarded arena,
heap or seven fixed pinned allocations:

| Exit sequence | Frames | WAD reads | Result |
| --- | ---: | ---: | --- |
| Owned STOP | 64 | 5,045 | Dynamic heap empty; fixed pins unchanged |
| Fresh image, F10/Y menu Quit | 42 | 5,047 | Same entry address; dynamic heap empty |
| Fresh image, owned STOP | 64 | 5,045 | Same entry address; dynamic heap empty |

All three epochs have identical first 32 pixel/palette blocks. The native
loader resets the private Newlib and Doom initialized data/BSS on reload.
Direct reentry into a retired image rejects before allocating. Both plain
and outer-driver/heap/arena ASan/UBSan runs pass; the accepted host engine
object itself remains uninstrumented. The engine module is mapped outside
the native arena, so this is not a proof of i960 template overwrite,
instruction-cache invalidation, retained IRQ contexts or real DMA rearming.

`evidence.tar.xz` is SHA-256
`ed0f2d6a954598443fe9b731096ed443b48336c61347b7e638c4ecaedfff8cd8`.
It contains plain/sanitized logs and exact commands, the sanitized executable
and shared engine, source hashes, live control-page bytes and reset-support
inventory. The pinned upstream source, private runtime and WAD remain in
their existing repository locations. The [test driver](../../../game/doom/play/accele160/reuse/native.c)
is an investigation harness and never accesses PCI.

Before this becomes a supported restart command, a new **RAM kernel** must
preserve an audited idle state before global shutdown, refresh image/data/BSS
through admission, retain monotonic transport sequences, reject old run/frame/
WAD/key messages, and extend heartbeat checking to idle/upload states. The
current global STOP remains the failure/shutdown boundary. One reset will
be required to enter that updated kernel for the first card acceptance.

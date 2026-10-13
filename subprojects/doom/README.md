# Doom: DoomGeneric on i960 RTEMS

Canonical source: [game/doom](../../game/doom/README.md). The engine is
DoomGeneric with Freedoom Phase 1 data, an 8 MiB arena runtime and host-backed
WAD access. The Linux host supplies browser display/input transport; the
engine executes on the card.

- [Interactive browser build/run and controls](../../game/doom/play/README.md)
- [Build and source pins](../../game/doom/README.md)
- [Runtime and libc](../../game/doom/runtime/README.md)
- [RAM contract](../../game/doom/RAM-CONTRACT.md) and [OS integration plan](../../game/doom/OS-PLAN.md)
- [Startup/visible-frame implementation](../../game/doom/runtime/startup/README.md)
- [Accepted visible baseline](../../artifacts/doom-visible-20261013/README.md), including exact build/live/replay scripts and binaries
- [Research progression](../../docs/research.md#doom-progression)

The accepted baseline delivers two identical visible 320×200 frames and exits.
Its static browser gallery is a capture viewer, not gameplay. The new persistent
[play profile](../../artifacts/doom-play-20261013/README.md) passed a six-frame
physical forward/release/STOP run, delivering about 0.169 frames/s. Its fresh
user session is live on port 8088 with browser turning/firing confirmed; see
the guide above for the temporary keyboard bridge, deadline and controls. The user has chosen playability first, then profiling
and optimization from real use.

Keep the accepted compiler workaround (`--point-side-o0`) and pinned source,
WAD and runtime dependencies when reproducing the baseline. Full audit and
native replay captures distinguish real execution results from static assets.

# RTEMS: runtime and operating system

Canonical source is [rtems/](../../rtems/README.md). This is RTEMS 4.6.6 adapted
to the i960RP with pinned sources and lwIP 2.1.3. Builds are profile-specific;
use a payload and generated Linux module from the same build.

| Area | Implementation / evidence |
| --- | --- |
| AcceleRAID 160 bounded task gate | [new-board profile](../../rtems/accele160/README.md), [physical acceptance](../../artifacts/current/accele160-rtems-20261017/README.md) |
| Initial returning RTEMS and networking | [RTEMS guide](../../rtems/README.md), [first acceptance](../../artifacts/rtems-20261011/README.md) |
| Hardware timer and firmware coexistence | [autonomous profile](../../rtems/autonomous/README.md), [web acceptance](../../artifacts/rtems-web-autonomous-20261011/README.md) |
| Owned interrupts and task control | [interrupt contexts](../../rtems/interrupt/README.md), [resident runtime](../../rtems/residentnet/README.md) |
| Larger owned RAM and Doom arena | [12 MiB evidence](../../artifacts/notes/rtems-large-ram-20261012.md), [Doom RAM contract](../../game/doom/RAM-CONTRACT.md) |
| Application/runtime integration | [Doom runtime](../../game/doom/runtime/README.md), [OS plan](../../game/doom/OS-PLAN.md) |

Build dependencies are pinned in [sources.json](../../rtems/sources.json),
[toolchain archive](../../artifacts/toolchain-20261011/README.md) and the exact
artifact build scripts. `make -C rtems test` is offline; hardware runners are
separate. Read the selected profile guide before borrowing commands from the
original cooperative profile: interrupt ownership, memory and module differ.

The current runtime is trusted code in one address space. It is not a generic
protected-process OS or a drop-in BSP for every i960 card. See
[porting another card](../../docs/porting.md).

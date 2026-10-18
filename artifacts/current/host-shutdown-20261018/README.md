# HP Z400 shutdown investigation — 2026-10-18

**A shared-workqueue interaction is identified and a private-queue fix passes the
live card/graphics test. Final physical power-off with the retained card remains
deferred at the user's request. The PC is left running; default launcher unchanged.**

The user reports a black screen with fans running for more than five minutes,
while Num Lock remains switchable. That is a real problem beyond the confirmed
90-second desktop timeout. Num Lock is consistent with some keyboard/interrupt
handling remaining alive; it does not prove that shutdown is progressing.

## Evidence and cause

Previous boot `79fef5a0-de03-410c-8cc0-3b4051afdb3b`:

- Doom stopped cleanly at **18:49:07 CEST**.
- GDM's `session-c1.scope` waited **90 seconds**, then killed **Xorg PID 1110**
  at 18:50:37. Xorg had already removed its input devices.
- Kernel hung-task traces identify `admit_command` waiting indefinitely in
  `wait_for_completion()` on **Workqueue: events**. This is the shared system
  queue. Retained exclusive RTEMS deliberately never completes operation 13.
- The installed NVIDIA 390.157 driver's `os_flush_work_queue()` expands
  `NV_WORKQUEUE_FLUSH()` to **`flush_scheduled_work()`**. Both the installed
  source and shutdown stack establish this link. That global flush can wait
  for our deliberately pending operation, tying unrelated graphics shutdown
  to the retained card. A NVIDIA warning alone is not proof of a broken GPU.
- `myrs_monitor` also waits for firmware completion, on its separate private
  `myrs_wq_7` queue. Quiescing stock monitoring *before* exclusive entry is a
  separate follow-up; do not cancel/unload it after it has become blocked.
- Persisted shutdown logs reach final SIGTERM and journald exit. They do not
  prove whether the last obstacle is a subsequent NVIDIA flush, another late
  shutdown hook or final ACPI power-off. Full power-off qualification is still
  required; do not claim the complete shutdown problem is closed.

Hardware: HP Z400, BIOS 786G3 v03.15 (2010-10-29), Ubuntu kernel
6.8.0-138-generic, GeForce 605 GF119 with NVIDIA 390.157. ACPI warnings are
present but are not sufficient evidence of the cause. No BIOS, GPU driver,
boot parameters, global timeout or firmware was changed.

## Isolation and fix

On boot `289ec386-76a6-4eb5-99bc-9fca421dc2d5`, with Mylex unbound/no retained
modules, GDM stopped within about five seconds and normal NVIDIA module unload
succeeded. The same warning occurred without a hang. A normal
`systemctl poweroff` then **stopped the fans**, confirmed by the user; no exact
duration was supplied. This proves the machine can power off, but changes both
card and GPU state, so it cannot alone attribute the original hang.

The narrowly scoped fix is in `host/accele160/ram_admit/admit_command.c`:
allocate a private **`accele_ram_admit`** workqueue, submit the retained command
there, and destroy it on normal safe module teardown. Initialization failures
release the queue and existing references. The command, completion wait,
module/parent pins, release gate and reboot-only resource lifetime are unchanged.
No timeout pretends the firmware completed, no pending DMA is freed, and no
module is force-unloaded. Moving this wait out of `system_wq` allows unrelated
global flushes to finish.

`write_manifest.py` accepts an optional fifth path argument for the admission
module, recording its exact module and C-source hashes. The Doom bridge checks
those identities before load; legacy manifests retain their exact old module
pin. The whole bundle inventory remains enforced. Other module and all card,
RAM, IRQ, heap, DMA, framebuffer and ownership audits remain in place.

## Physical fixed-driver result

New boot `408be3ad-0813-40c5-b14e-4d65f5a8f8eb`, isolated workspace
`/home/mit/i960-shutdown-wq-20261018`, explicit core launcher
`/home/mit/.local/bin/i960-doom-private-wq`:

- Normal unstarted load/unload passed: `started=0 done=0 ... released=0`.
- Private module SHA-256:
  `2886bd370752621fd82013f27c435c76cf6b40a10e928c12a68e928b0d6e1825`.
- **218 fully audited frames, 32 independent paired PIO/DMA comparisons**,
  all **5,043 native startup WAD requests**, and eight visible F6 pulses passed.
  First 32 images match the existing native-qualified baseline pixels/palette.
- With RTEMS active and `started=1 done=0` still confirmed, normal GDM stop
  returned in **0.9467 seconds** and Xorg exited. This removes the previously
  observed graphics timeout without completing or unpinning the card command.
- GDM restarted, then game STOP passed with all 16 input transitions consumed.
  Clean global RTEMS shutdown reached QUIE and passed final full-bank audits.
  The command remains correctly pending and resources remain pinned.

The RTEMS kernel, Doom engine, WAD, firmware and other host modules are unchanged.
`acceptance.tar.xz` contains the exact changed source/build/KO/manifest, runtime
receipts, guarded captures, graphics test context and installed NVIDIA source
excerpts. Unchanged inputs resolve to the accepted FIFO/flat artifacts. Raw prior
logs explain the original failure; `private-queue-live.json` includes measured
stop timing and pushed-frame identities. `verify.py` replays the card evidence:

```sh
python3 artifacts/current/host-shutdown-20261018/verify.py
```

## Current state and remaining qualification

The user chose **leave it running; test later**. Desktop and SSH are available.
Doom and the gateway are stopped. The card is in terminal global QUIE, with its
private admission worker and DMA allocations retained; **do not force-unload,
unbind, adopt resources or try to load another session before a PC reset**.
The installed ordinary `./doom` still selects the previous FIFO bundle.

Next: issue normal `sudo systemctl poweroff` with the current graphics and fixed
Mylex module present, observe whether the fans stop, then turn the PC back on.
Do not pre-unload NVIDIA for this test: the purpose is to exercise the original
combination. After that, collect two guarded full-flash readbacks on the new boot
and only then promote the private-queue bundle/default wrapper. The previous
successful bare-host control is not a substitute for this acceptance boundary.

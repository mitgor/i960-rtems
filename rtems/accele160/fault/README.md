# P3 — terminal records and owned exception work

Latest: [profile 5 normal owned runtime](OWNED-RUNTIME.md) passed two-game
acceptance with owned fault/NMI handlers and ISP, live console traffic, rearm,
guards and final QUIE ownership. Reset recovery passed and the prompt is restored in the same owned profile.
Its separate live capture is in the new evidence batch. Earlier mode-0 restoration below is historical.

Current P3b status: [owned fault/NMI implementation](OWNED-EXCEPTIONS.md)
passed both real hardware exception tests and both reset-recovery gates.
The normal prompt is restored in mode 0 after a 64-frame game with verified
idle and 577 successful external console exchanges. The owner remains live.
Owned-ISP normal-runtime qualification remains separate from this previously
qualified software-only mode-0 prompt.

Historical P3a status 2026-10-18: cross-built; **both software terminal tests passed on the
card**, including deliberate private guard corruption and retained resources.
Both terminal tests have verified reset recovery. The mode-0 normal profile
ran two 64-frame games with console traffic and audited idle/rearm. Its prompt
was restored; that owner has since shut down cleanly. Mode 0 reset recovery is pending. See
[the evidence ledger](../../../artifacts/current/accele160-fault-20261018/README.md).
This is the first bounded part of P3, not completion of fault/NMI ownership.

## Problem and scope

The baseline `bounded_fatal()` calls `stop_timer()` before parking after RAM
claim. That restores the stock mask, map and timer vector even after upper RAM
has been repurposed. Priority 31 then prevents normal dispatch, but this is not
an appropriate general exception-containment contract. The opt-in terminal
profile branches before that restoration, raises priority, masks interrupts,
disables only the borrowed timer 1, and records a terminal state. It never
returns to stock, acknowledges driver completion, releases pins, or assumes a
DMA disable would abort an in-flight transfer.

This entry is a **software call**, not a fault or NMI vector. The exception
tables and cached NMI remain stock. Hardware exceptions, a damaged current
stack preventing entry, and permanently masked-interrupt watchdog recovery are
not contained by this gate. No new RAM or engine exclusion is claimed.

## Layout and ownership

The linker reserves record page `c0777000..c0778000` and stack page
`c0778000..c0779000` inside the existing 512 KiB grant. Console `c0775000`,
PC samples, workspace and upload pages remain separate. NOLOAD reservations
preserve the established 29-page image shape. The record is uncached; the
single host owner reads it with aperture selector `c0776000`. It does not call
failed application code to retrieve the record.

Words 0..15 belong to the host (nonce, sequence, test token). Card words:

| Word | Meaning |
|---|---|
| 16..18 | AFT1, copied nonzero host nonce, schema 1 |
| 19..22 | Entry processor controls, fatal code, original FP/SP |
| 24..29 | Entry latch, compiled test mode, stack guards, ticks, claimed, IRQ fault |
| 31 | READY or DONE, published last after `syncf` |
| 32..45 | Live PRCB/ISP, cached NMI/timer-1 vectors, ICON, pending/mask/maps, timer counts/reloads |
| 48..56 | CCR/NDAR/BCR for all three DMA channels |
| 64..71 | Fixed ROM PRCB words at `feffdd20` |
| 80..143 | All 32 two-word RAM fault entries at `c0000800` |

Both ends of the terminal stack have 64-byte guards; C begins above the lower
guard on a dedicated upward-growing stack. No timer-mode or DMA CSR read occurs:
those registers have read-clear semantics. The snapshot does not access unknown
SCSI windows or perform PCI configuration cycles. Zero CCR/NDAR/BCR is an idle
observation, not a proof that another bus master cannot start later.

The accepted firmware's ROM PRCB points to RAM fault table `c0000800`, ROM
interrupt table `feffd910`, and stock ISP `c0001000`. This differs from the PG
PRCB address `feffd4d0`. The new board's observed live PRCB is `feffdd20`.
The fixed ROM and the live register must agree before accepting the capture.
Mode 1 captured cached NMI `c00521b0`, ISP `c0001000`, sixteen fault
entries `(c0053400, 0)` and sixteen `(0, 0)`. The next exception gate must review
those stock handlers and routing, then explicitly install/validate board-specific handlers before `faulte`
or real NMI injection. Do not copy PG handlers/addresses unqualified.

## Build and isolated tests after recovery

Use a new copy of `/home/mit/i960-service-20261018/bundle` as
`/home/mit/i960-fault-20261018/bundle`; preserve the original archived bundle.
Overlay changed `doom_dma/` sources, `fault/`, and provision.py. Keep the pinned
engine identity/template and existing inputs. The baseline service must be
stopped and a fresh boot established, with no retained driver owner.

Build separately for `ACCELE_TERMINAL_TEST=1` (explicit software fatal) and `2`
(deliberately change one private guard word, then terminal entry):

```sh
ACCELE_TERMINAL=1 ACCELE_TERMINAL_TEST=1 ACCELE_SERVICE=1 \
 DOOM_REUSABLE=1 DOOM_PERSISTENT=1 DOOM_FPS_FRAMES=32 \
 DOOM_KEY_FIFO_SUPPORT=1 bash project/rtems/accele160/doom_dma/build.sh \
 /home/mit/i960-accele160-rtems-20261017/accele160 \
 /home/mit/i960/tools/bin kernel
python3 project/rtems/accele160/doom_dma/write_manifest.py \
 project/rtems/accele160/doom_dma kernel engine/manifest.json inputs/dma_frames.ko
```

Review build symbols, bounds and disassembly; regenerate explicit bundle file
hashes. Launch with the existing isolated bundle launcher and full two guarded
firmware prechecks. A manifest-pinned nonzero test mode makes the runner test
immediately after RTEMS READY, before Doom admission or DMA initialization.
It tests stale nonce refusal, publishes one exact trigger, verifies stable
DONE/guards/code/retained state, and confirms STOP does not make the admission
complete. The host closes its mappings but never releases retained pins/grant.

Capture all session/bundle files before reboot. Each terminal test needs its own
reset and paired guarded full-flash reads. Do not chain the two modes in one
retained session. After both, qualify a mode-0 kernel with ordinary Doom, console,
STOP and post-reset audits; then restore a service-enabled prompt. Until those
checks pass, no candidate binary is promoted.

```sh
cc -Wall -Wextra -Werror -fsanitize=address,undefined test_policy.c -o /tmp/at-policy
/tmp/at-policy
cc -Wall -Wextra -Werror -fsanitize=address,undefined test_card.c -o /tmp/at-card
/tmp/at-card
python3 test_host.py
python3 verify.py PATH_TO_SESSION/terminal
```

`test_card.c` executes the actual C adapter with bounded mock MMIO and verifies
all guard words, stale-trigger behavior and record publication. Native tests do
not execute i960 assembly or qualify hardware interrupt/fault delivery.

Remaining P3: owned fault/NMI entries and entry-stack policy; real controlled
fault/NMI tests; all interrupt routes; SCSI/cache/other bus-master exclusion;
terminal behavior with genuinely active/stalled DMA; reset recovery. The
existing PG coexistence profile stays unchanged.

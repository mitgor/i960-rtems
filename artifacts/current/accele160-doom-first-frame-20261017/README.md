# AcceleRAID 160 first real Doom frame, 2026-10-17

The third run, `accepted/`, **captured a real Doom frame**. The card served
all 5,043 engine WAD requests in the exact 5,043-record native offset/length
order, reached the owned first-frame boundary in 123.54 seconds, and returned
engine code `0x454e4702` with result 210 and one frame. The 65,536-byte
frame/palette slot was read back in 16 independently FNV-checked 4 KiB pages;
SHA-256 is
`f4d1c27a4ec8e8db4437d9e28012107370749765aa0e09c99758eeb54163b8ce`.
The rendered 320×200 view with the captured Doom palette is
[game-frame-color.png](accepted/persist/game-frame-color.png).
This is one real frame, not continuous browser play or an FPS measurement.

The full 2,048-page reversible bank audit had zero marker or page failures,
preserved lower-bank and code hashes, and found all DMA channels idle.
The exact 867,792-byte image passed admission and relocation, all WAD replies
were checked, the engine released its 6 MiB zone loan and every dynamic
allocation, its text hash stayed `d21d8811`, and the arena guards remained
valid. The host checked the old DAC960PG remained unbound, then published
STOP; the RTEMS heartbeat advanced to tick 14,061 and the retained callback
reached quiescence with no fault. The exact kernel/image hashes are
`9b9a848dc099a2d43db1752561caaf7320b925988a2313a502209f54c231d88e`
and `957e49dc912153ddc0f80f3f22e1276df20e023c3e6ae427efe1b6c96778cdde`.
`accepted/build/` and `accepted/source.tar.gz` preserve the exact binaries
and source. The callback/grant were released by reboot, never by module
unload. On new boot `c9773c0f-9b64-414b-8712-4d9e6bf1ae5e`, the stock descriptor was idle, the old card remained unbound, and two independent guarded 1 MiB READIMAGE transfers had zero status, residual or guard changes. Both matched unchanged firmware SHA-256 `1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`; compact records are in `accepted/post-reset-{0,1}/`.

## Earlier attempts

The accepted new-card WAD service was extended to call the pinned Doom engine
under RTEMS ownership. The old DAC960PG at `0000:37:04.1` remained unbound,
and no firmware write was issued.

`attempt-0/` records the first host-monitor error: it treated an uninitialized
engine report (`ffffffff`) as a fault after starting the engine. The host
stopped answering; the card's first WAD request timed out after 500 timer
ticks. This was a test-harness error, not evidence of an engine failure.

`attempt-1/` records the corrected first physical run. The host served 1,401
engine WAD requests; its saved first 1,400 entries match `native-requests.bin`
exactly. The 1,401st on-card request at offset 24,551,936, length 4,096 had
matching reply sequence, offset, length, status and FNV. No subsequent request
or frame appeared for about 15 minutes. Timer interrupts advanced at 100 Hz
with balanced ISR entries and returns. The saved `pc-samples.json` field
`pc=0x2002` is **process controls**, not an instruction address. STOP was
published but the engine did not reach a cooperative STOP boundary. The host
process was terminated while the card grant and command module remained
retained. The PC was rebooted to release them. On new boot
`51bf0372-c77c-4c06-a1c3-d466f1b1fbe1`, `myrsread` bound the new card,
its stock descriptor was idle, and two independent 1 MiB READIMAGE transfers
had zero status/residual/guard changes and both SHA-256
`1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd`.
The old card was still unbound. `attempt-1/build/` contains the exact image,
kernel, ELF and symbols for that run.

`attempt-2/` records a second physical run with WAD-read progress counters.
It crossed the earlier stall point and served 3,801 engine requests in about
95 seconds; **all 3,801 match the native request trace byte-for-byte**. The
last request, offset 16,061,440 and length 512, completed with card-reported
status zero, exact reply number and FNV. No next request or frame appeared
for another 120 seconds. At 214.9 seconds total, the host saved the complete
control page and interrupt sample ring, published STOP and left the card
retained. Its timer continued; the engine did not return. The attempted
`frame.bin` in these runs is only the earlier **diagnostic** pattern, not a
Doom frame. The first version of the interrupt sampler read frame−4, which
was zero and did not locate execution; the next source revision samples
`rip` at ISR entry.

`attempt-2` also closed on new boot `bc179e7b-b047-4b6b-bce6-9cce95b1a4b9`: idle descriptor, old card unbound, and two guarded complete READIMAGE transfers matched unchanged stock firmware. The retained module/grant were released by reset, not unloaded. The current source, build instructions and strict runner are in
[doom_first_frame](../../../rtems/accele160/doom_first_frame/README.md).

The pinned WAD is not duplicated here. Its SHA-256 is
`7323bcc168c5a45ff10749b339960e98314740a734c30d4b9f3337001f9e703d`.
`native-requests.bin` is the 5,043-record host oracle (8-byte little-endian
offset and length pairs). Each run's `engine-reads.json.gz` preserves its
host-served request sequence and per-slice hashes. The exact engine template
and relocations are in
[the accepted bridge artifact](../accele160-doom-bridge-20261017/README.md).

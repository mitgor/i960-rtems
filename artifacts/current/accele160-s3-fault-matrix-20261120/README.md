# Compiled updater: S3 emulator fault matrix

Offline interpreter run on 2026-11-20. The tested experimental ROM has SHA-256
`867f7320d5f8cc2623cd6b024cecf988df754eaa92dd3eaf6452fecb8e2a6453`.
The modeled target has SHA-256
`01ed56f51152a4c9f62ce227431ad429a8386dc0d05cdffd1c3b476e6dabcf23`
and differs at mutable flash offset `0xb0000`. Neither image is approved for
physical flashing.

Each run started the cross-built RTEMS firmware, uploaded all 256 UPD1 chunks,
sealed the image, and issued APPLY. The five fault runs also attempted ABORT
and a second APPLY after failure; both were refused in latched state 4. All
fault runs closed the modeled board write gate.

| Model case | UPD1 result/state | Writer result | S3 status | Receipt |
| --- | --- | ---: | ---: | --- |
| Normal program | 0 / 3 | 0 | `0x80` | [success-final.json](success-final.json) |
| Gate stuck off | 9 / 4 | 8 | `0x00` | [fault-gate.json](fault-gate.json) |
| Low VPP | 9 / 4 | 5 | `0xa8` | [fault-vpp.json](fault-vpp.json) |
| Wrong chip ID | 9 / 4 | 2 | `0x00` | [fault-id.json](fault-id.json) |
| Locked mutable block | 9 / 4 | 3 | `0x00` | [fault-lock.json](fault-lock.json) |
| Program leaves byte unchanged | 9 / 4 | 7 | `0x80` | [fault-program.json](fault-program.json) |

The emulator's S3 model assumes immediate operation completion and represents
VPP and the board gate as logical switches. It does not model electrical
levels, bus strobes, timing, power loss, or actual card behavior. These passes
establish software error handling only; the real flash path still needs
card-side qualification.

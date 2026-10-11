# CHIP-8 native validation and i960 RTEMS build — 2026-10-11

**Implemented and tested on the card.** Initial native tests and cross-builds
ran while the parallel RTEMS batch owned hardware. Once it completed, the web
service stopped through its normal verified cleanup, then two exclusive game
sessions ran. Both restored RAM and unloaded; IPv6 HTTP was restored with 200.
No flash write or reboot. Isolated build:
`/home/mit/i960-chip8-20261011-3W3aWm/work-final`.

| Session | Native-matching replies | Periodic full audits | Median / max callback |
| --- | ---: | ---: | --- |
| `live1`: reset + 300 scripted updates | 301 | 9 | 51.43 / 74.03 ms |
| `live-web`: browser over SSH, movement and restart | 404 | 12 | 51.65 / 73.98 ms |

All 705 replies were independently replayed from the saved trace. There are
23 saved audit snapshots: 21 full 512 KiB periodic reads plus two initial
471,136-byte prefix reads. Final close additionally verifies full restoration. The browser
trace contains two resets and ten requests with held keys; screenshot/DOM checks
confirmed the Mylex/RTEMS backend, movement, then reset to instruction count zero.
The production service's previous close reported restored/unloaded/unbound before
loading the game module. Its replacement uses `http-after-chip8` for captures;
existing visitor statistics remain in their previous host directory.

- `kernel.bin`, `.elf`, `.map`, `.symbols`, `.dis`: exact RTEMS application build.
- `build.json`: compiler, flags, source-archive pins and payload hash.
- `chip8-build.json`: exact application/profile hashes and the historical build-time `hardware_tested: false` flag.
- `target-source/`: exact app/core, startup, context assembly, libc and linker
  source used. RTEMS upstream sources are pinned in build.json and already
  covered by the repository's RTEMS licensing/source preservation.
- `build.log`: successful final isolated build.
- `native-tests.txt`: ASan/UBSan core checks and four Python replay/protocol/HTTP
  tests, including 1,200 demo frames / 24,000 guest instructions.
- `native-linux.txt`: the same native suite on the card host.
- `dac960rtems.ko`, `module-source.tar.gz`, `module-build.log`: baseline bounded
  RIO transport binary and generated sources. The kernel build reports the
  compiler-name difference and unavailable-vmlinux BTF notice; module loading
  and both hardware sessions passed.
- `chip8-live.tar.gz`: full `live1` and `live-web` capture directories (traces,
  paired snapshots, audits, request hashes, final restoration and summaries).
- `live1-verified.json`, `live-web-verified.json`: offline verification results.
- `card-browser.jpg`: actual card browser screenshot after restart.
- `http-restored.headers`, `http-restored.html`: post-test IPv6 HTTP 200 check.
- `validation.json`: independent hashes/source correspondence and memory layout
  checks performed by `game/chip8/verify_build.py`.

Target size: 22,560 bytes text, 452 data, 55,472 BSS. Flat binary extent is
187,012 bytes, including its address gap/BSS. SHA256:
`3a0dfb3bd1e0fed27092690f4e06349acd9557c97abba562d3b25cac7df33e06`.
Both isolated builds produced this same raw payload; the final manifest omits
irrelevant macOS archive metadata. No compiler/linker diagnostic remains in the
final log. The initial local native compile found misleading indentation in a
draw-loop `break`; it was reformatted before the passing tests and target builds.

A reverse-DNS startup delay found during initial native browser checking was
removed from the loopback server. The final HTTP tests complete without that
lookup. The tests cover the specified interpreter dialect and original project
demo, not universal CHIP-8 ROM compatibility or a long-duration hardware soak.

[Application and card reproduction](../../game/chip8/README.md),
[Doom choice and OS dependency plan](../../GAME-PROGRESSION.md).

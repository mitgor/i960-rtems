# T2 bounded Tetris evidence

Collected 2026-10-10 Europe/Berlin. See ../../TETRIS-STEP.md.

- target/: exact 4,064-byte i960 payload, disassembly and linker map.
- acceptance/: nine live runs, request bytes, CLI transcripts, native expected
  responses, paired firmware/RAM captures, state/frame splits and unload records.
- offline-validation.json: freshly rebuilt native oracle versus every saved live
  response, plus independent loader transaction/restoration checks.
- cross-tests.txt: ASan/UBSan native and actual interpreted i960 both returned
  1161671136 across rule tests and 1,024 state/frame transitions; setbit/fatal-exit
  interpreter tests passed.
- native-tests.txt: local sanitizer run.
- loader-regression.txt: unchanged scalar/BIO1 transport regression suite.
- final-host-state.txt: kernel/boot identity; collection also checked module
  absent and card driverless.
- source/: implementation, tests and host interpreter snapshot.

The Linux module is unchanged from ../buffer-io-20261010/module/dac960loadrun.ko;
each request.json records its hash. Runner and flashed firmware are unchanged.
Each hardware transaction completed 128 commands. Eight returned exactly 2,160
bytes; the invalid 21-tick request returned application status 1 and no output,
with clean restoration/unload. All used boot a9429ca4-0144-452d-8a80-7189608ce99b.
No flash or reboot was performed. Captures are transient RAM, not new physical
flash dumps. The 1,024 transitions were native/interpreted; hardware ran nine
transactions. An interactive terminal client is not part of this milestone.

Files are intended for Git, with repository-wide inventory and SHA256SUMS.

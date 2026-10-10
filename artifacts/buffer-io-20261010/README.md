# BIO1 / T1 hardware evidence

Collected 2026-10-10 Europe/Berlin. See ../../BUFFER-IO.md for the protocol,
commands, outcomes and remaining scope. No new flash or reboot was needed.

`target/` contains the exact compiled i960 buffer demo, map and disassembly.
`module/` contains the generated sources and exact Linux 6.8.0-138-generic module.
`source/` preserves the host/target implementation and tests for this milestone.
`inputs/` holds the exact test inputs. Each run directory contains request
metadata, the upload image, complete transaction log, paired RAM captures,
response bytes/metadata where applicable and clean unload evidence.

- run-text: sequence 101, 36 output bytes, successful greeting/transformation.
- run-frame: sequence 102, 1920 output bytes; frame.txt is the card-drawn screen.
- run-small-capacity: sequence 103, application status 2, zero output; the CLI
  deliberately returned exit 1 after saving evidence and clean restoration.
- run-repeat: sequence 104, new input, 37 output bytes after the rejected request.
- run-legacy: scalar Fibonacci(20)=6765 using the new module, no buffer output.

All runs share boot a9429ca4-0144-452d-8a80-7189608ce99b. Four buffer runs have
128 commands each; the scalar run has 110. All completed without pending/dirty
state and the card was left driverless. Empty/zero payload-after captures in
scalar mode are unused, not evidence of a buffer response.

payload-after-* is the pre-restoration RAM containing CPU-produced output.
stage-candidate-* is the pre-execution upload. These are NOT flash candidates or
new physical ROM acquisitions. Firmware bytes were restored to the prior patched
image hash. Archive files are intended for Git and included in the root artifact
inventory and checksums. validation.json and native-tests.txt report independent
checks; legacy-loader-tests.txt records existing regression tests.

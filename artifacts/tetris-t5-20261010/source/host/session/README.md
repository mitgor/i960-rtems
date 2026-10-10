# Persistent BIO1 sessions

See [PERSISTENT-SESSION.md](../../PERSISTENT-SESSION.md) for the hardware results,
audit coverage, ownership contract and build/use instructions.

- `build.py`: guarded derivation of the existing one-shot transport, distinct driver.
- `transaction.h`: OPEN / bounded STEP / audited CLOSE.
- `fileops.h`: exclusive character-device ownership, serialized release and pinning.
- `session.py`: Linux client; one write/read per request, verified final close.
- `test_session.py`, `test_session_main.c`: native production-transaction fault tests.
- `live_test.py`: explicit oracle-checked card replay and lossless evidence capture.
- `lifecycle_test.py`: explicit card ownership/process-death tests.
- `cadence_test.py`: explicit paced 20 Hz card test.
- `validate.py`: independent offline replay reconstruction and native comparison.

The device is root-only. Never retry an uncertain execution or unload a pinned
failure. `Session` assumes a correctly loaded module; it does not load/unload it.
`Session.close()` verifies the final-release debugfs record because Linux does
not propagate the driver's release return value through close(2).

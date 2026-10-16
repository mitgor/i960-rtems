# Bounded IMR1/OMR1 hardware experiment

**Later milestone:** [framed control and independent bounded STOP/HALT passed](MU-FRAMED.md).
Earlier next-step statements below describe their checkpoint.

Live echo and full cleanup passed; see [captures and failed trial](../../artifacts/notes/mu-echo-20261011.md).
This is an opt-in experiment, separate from production `autonet`.

Build `build.py --profile mu` in the established RTEMS build workspace, then:

```sh
python3 project/rtems/control/build_echo_transport.py --payload mu/kernel.bin --out mu-module
make -C /lib/modules/$(uname -r)/build M="$PWD/mu-module" modules
sudo python3 project/rtems/control/live_echo.py --payload mu/kernel.bin \
  --module mu-module/dac960auto.ko --reader control-prototype/read_mu \
  --output mu-echo
```

Stop the production relay normally first; verify its restoration/unload. The
reader is built from `read_mu.c`. Never run two owners. Keep production binaries
for restarting the service. The experiment requires the existing patched card,
exact payload pinning, zero message words/pending bits and masked message 1.

The private ioctl 0xc0204d01 takes eight uint32 words: request, response, firmware
sequence before/after, IISR, OISR, IIMR, OIMR. One accepted invocation per armed
session writes the c71e-tagged request; the ISR replies with XOR 5a5a5a5a. Host
polling is limited to 200 pauses (1–1.5 ms each, plus scheduling delay); target
polling disables itself after 200 timer ticks. Neither is an independent STOP.
The session mutex excludes ordinary firmware transactions during the exchange.
No message interrupt is enabled, and no queue/index/ATU mapping is changed.

Target STOP restores message values and clears IISR bit 1. OISR is **read-only
locally**: only the host clears its bit 1, after validated STOP plus the MUOK
ownership marker, zero values and expected masks (IIMR=1fb, OIMR=ff). Uncertain
cleanup retains resources. Reclamation continues through existing full RAM
restoration. Other pending bits must survive.

`python3 rtems/control/test_mu.py` runs shared C host/target code with ASan/UBSan:
echo, occupied/pending refusal, malformed tag, mask changes, timeout, watchdog,
local read-only OISR semantics and ownership-gated host acknowledgement.

Next is a framed transport with epoch/sequence/retry semantics and a bounded
independent STOP handler. Do not relax the firmware callback or preemption
contract on the strength of this echo result.

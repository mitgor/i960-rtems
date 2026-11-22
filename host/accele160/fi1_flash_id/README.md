# Firmware injection v1 flash ID probe

This probe runs through the accepted operation-13 RAM admission handler on
the working card, serial `10112500320`. The 200-byte payload is linked at
`0xc0710000`, SHA-256
`048e32f7f8af97744df4ba87bd3e647ed61e2c4d88a4962242078340ddbca72c`.
It writes only Intel read-array `FF`, read-identifier `90`, and read-array
`FF` commands to the mapped flash. It reads manufacturer, device, master
lock, all sixteen block-lock bytes and array byte zero, then records six
words at `0xc000fa60` beside the operation-13 control report. It never sets the board gate,
erases, programs, locks, or writes persistent data. The static disassembly
audit is `audit.py`; rebuild with `build_id.sh` and the archived i960 toolchain.

`run_id.py` pins the installed Firmware injection v1 SHA, handler, payload and
five host command modules. It requires two independent full reads from the
current boot, an idle descriptor, the expected sole card at `37:09.1`, and a
blank peer slot. It checks the loader page and owner table before and after,
uploads one page, verifies its hash in the card, issues one returning
operation-13 call, checks the six-word ID record and that nothing else in the
control page changed, and restores staging, report, owner and BAR mappings.
It leaves resources in place after an uncertain command; cold reset is then
the recovery path. A `/run` marker limits it to one ID probe per boot.

Expected record: Intel manufacturer `0x89`, S3 device `0xa6`, master lock 0,
sixteen-block lock mask 0, and array byte `0x50` from this card's exact
installed image. A full independent `READIMAGE` after the probe must match
the installed image again.

This tests the live flash command-read path in the stock-derived firmware
context. It does **not** measure VPP or prove that native firmware can erase,
program, or cold boot. The separate no-erase gate-hold experiment requires an
external VPP measurement and is not part of this run.

## First attempt and revision

On boot `725fcfca-e805-493b-8987-80d981674be3`, an initial payload
(`400a2696…f6634`) wrote its ID record to `0xc0710100` in the granted page.
The operation-13 host report returned status 0 and payload result 0, but a
subsequent BAR read of that granted page showed unrelated bytes, so the
launcher stopped before cleanup. A full `READIMAGE` attempted while the
admission command and grant were retained returned status 2/residual 1 MiB;
that read says nothing about persistent flash contents. The PC was sent a
power-off request to clear the retained RAM state. Post-boot flash validation
is required before any new attempt. The granted-page mismatch may be a
card-cache visibility issue, but that is an inference, not a chip-ID result.

The revised payload above writes the record into `0xc000fa60`, adjacent to
the host-visible operation-13 report. The launcher audits and restores that
control-page region, then releases resources even if the recorded ID differs
from expectation. It is a new image and has **not** run on hardware.

# Firmware injection v1 flash ID probe

This probe runs through the accepted operation-13 RAM admission handler on
the working card, serial `10112500320`. The 200-byte payload is linked at
`0xc0710000`, SHA-256
`400a269688b991ddfefc8fafef6d41c5b900d13f992da3b794131c85d63f6634`.
It writes only Intel read-array `FF`, read-identifier `90`, and read-array
`FF` commands to the mapped flash. It reads manufacturer, device, master
lock, all sixteen block-lock bytes and array byte zero, then records six
words at `0xc0710100` in its granted RAM page. It never sets the board gate,
erases, programs, locks, or writes persistent data. The static disassembly
audit is `audit.py`; rebuild with `build_id.sh` and the archived i960 toolchain.

`run_id.py` pins the installed Firmware injection v1 SHA, handler, payload and
five host command modules. It requires two independent full reads from the
current boot, an idle descriptor, the expected sole card at `37:09.1`, and a
blank peer slot. It checks the loader page and owner table before and after,
uploads one page, verifies its hash in the card, issues one returning
operation-13 call, checks the six-word ID record and that nothing else in the
granted page changed, and restores staging, report, owner and BAR mappings.
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

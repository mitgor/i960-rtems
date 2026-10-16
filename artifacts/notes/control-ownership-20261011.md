> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Control-slot ownership investigation

See `rtems/control/OWNERSHIP.md` for findings, sources and the next experiment.

The evidence generator pins vendor 4.07-0-29 and checks it against the independently
dumped unpacked firmware. `references.json` preserves source hashes and search
leads. Named text excerpts are byte-verified instruction regions, not new dumps.
`audit.txt` records verification counts. `mu-samples.json` contains three fixed-
offset, read-only MU register observations from the running card.

No hardware writes, module replacement, firmware changes or web-server restart
were performed. IMR1/OMR1 are selected for a future bounded echo experiment;
neither a permanently owned sideband nor a safe RAM reservation is claimed.

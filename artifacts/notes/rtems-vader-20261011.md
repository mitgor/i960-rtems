> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Darth Vader web page — 2026-10-11

Added original Darth Vader ASCII art in an accessible preformatted block, dark
styling and a responsive monospace font to the card HTTP response. The runtime
and transport protocol are unchanged.

Rebuilt `autonet` and its exact image-pinned `autonet-module-vader` module on
192.168.2.75. Stopped the previous service cleanly, checked the module unloaded,
and started `i960-http6` with the new image. The launcher now selects that module.
The active capture directory is `/home/mit/i960-rtems-web-20261011/http-vader-live`.

The Mac fetched the complete 1,252-byte HTML body through
`http://[2a02:8106:40:9000:f662:19ee:dbad:1f1e]:8080/`; `response.html` preserves
it. All 24 existing live HTTP request checks passed (`http-tests.json`).
`build.tar.xz` preserves the target binary/ELF/build metadata, matching Linux
module, changed HTTP source and launcher. The service remains running for the
user. The preceding autonomous-runtime report describes unchanged limitations.

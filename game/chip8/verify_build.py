#!/usr/bin/env python3
"""Read-only verification of preserved build bytes, source identity and layout."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ART = HERE.parents[1] / 'artifacts/chip8-20261011'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
meta = json.loads((ART / 'build.json').read_text())
app = json.loads((ART / 'chip8-build.json').read_text())
assert sha(ART / 'kernel.bin') == meta['payload_sha256']
assert (ART / 'kernel.bin').stat().st_size == meta['payload_bytes']
assert app['application'] == 'chip8' and app['hardware_tested'] is False
for name, digest in app['source_sha256'].items():
    assert sha(ART / 'target-source' / name) == digest, name
for name in ['chip8.c', 'chip8.h']:
    assert sha(HERE / name) == app['source_sha256'][name], name
assert sha(HERE / 'rtems/app.c') == app['source_sha256']['app.c']
symbols = {}
for line in (ART / 'kernel.symbols').read_text().splitlines():
    fields = line.split()
    if len(fields) == 3:
        symbols[fields[2]] = int(fields[0], 16)
assert symbols['_start'] == 0xc0f2c000
assert 0xc0f4c010 <= symbols['__bss_start'] < symbols['__bss_end'] <= 0xc0f9bff0
assert symbols['_c8_request'] < 0xc0f4c000
assert meta['payload_bytes'] <= 0x6fff0
assert ' U ' not in (ART / 'kernel.symbols').read_text()
print(json.dumps(dict(payload_sha256=meta['payload_sha256'],
                     payload_bytes=meta['payload_bytes'],
                     source_hashes_verified=len(app['source_sha256']),
                     bss_start=hex(symbols['__bss_start']),
                     bss_end=hex(symbols['__bss_end']),
                     hardware_tested_by_this_check=False), indent=2))

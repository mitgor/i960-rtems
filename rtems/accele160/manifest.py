#!/usr/bin/env python3
"""Build the bounded AcceleRAID RTEMS grant admission manifest."""
import argparse
import hashlib
import json
from pathlib import Path

BASE = 0xc0710000
STAGING = 0xc078f000
PAGE = 4096

def fnv(data: bytes) -> int:
    value = 0x811c9dc5
    for byte in data:
        value = ((value ^ byte) * 0x01000193) & 0xffffffff
    return value

def symbols(path: Path) -> dict[str, int]:
    result = {}
    for line in path.read_text().splitlines():
        fields = line.split()
        if len(fields) == 3:
            try:
                result[fields[2]] = int(fields[0], 16)
            except ValueError:
                pass
    return result

def build(image: bytes, sym: dict[str, int]) -> tuple[bytes, dict]:
    if not image or len(image) > STAGING - BASE:
        raise ValueError('payload exceeds owned grant')
    pages = (len(image) + PAGE - 1) // PAGE
    if not 1 <= pages <= 127:
        raise ValueError('page count')
    if sym.get('_start') != BASE or sym.get('__bss_start', 0) < BASE or \
       sym.get('__bss_end', STAGING) > BASE + len(image) or \
       sym['__bss_start'] > sym['__bss_end']:
        raise ValueError('entry/BSS outside uploaded image')
    padded = image.ljust(pages * PAGE, b'\0')
    meta = {
        'board': 'AcceleRAID 160 1069:0050 1069:0054',
        'bdf': '0000:37:09.1',
        'load_address': f'0x{BASE:08x}',
        'entry': f'0x{sym["_start"]:08x}',
        'staging_address': f'0x{STAGING:08x}',
        'report_address': '0xc000f800',
        'original_bytes': len(image),
        'pages': pages,
        'padded_bytes': len(padded),
        'image_sha256': hashlib.sha256(image).hexdigest(),
        'padded_sha256': hashlib.sha256(padded).hexdigest(),
        'padded_fnv32': f'0x{fnv(padded):08x}',
        'first_80_sha256': hashlib.sha256(padded[:80]).hexdigest(),
        'bss_start': f'0x{sym["__bss_start"]:08x}',
        'bss_end': f'0x{sym["__bss_end"]:08x}',
        'bss_bytes': sym['__bss_end'] - sym['__bss_start'],
        'grant_bytes': 512 * 1024,
        'free_payload_pages': 127 - pages,
        'clock': 'ten synchronous RTEMS software ticks, worker wake at tick five',
        'interrupts': 'masked; no card timer/DMA/IRQ ownership',
        'return': 'normal return, fixed report and nonce echo; no persistent RTEMS instance',
    }
    return padded, meta

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('kernel', type=Path)
    p.add_argument('symbols', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    padded, meta = build(a.kernel.read_bytes(), symbols(a.symbols))
    a.output.mkdir(parents=True, exist_ok=False)
    (a.output / 'padded.bin').write_bytes(padded)
    (a.output / 'prefix.bin').write_bytes(padded[:80])
    (a.output / 'manifest.json').write_text(json.dumps(meta, indent=2) + '\n')
    print(json.dumps(meta, indent=2))

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Inspect a captured ISP1216 RISC image without executing unknown microcode.

The input is the little-endian word stream returned by the emulator's K bridge
command. Addresses in this report are ISP word addresses, starting at 0x1000.
"""

import argparse
import hashlib
from pathlib import Path
import struct


LOAD_ADDRESS = 0x1000


def inspect_image(data: bytes) -> dict:
    if len(data) < 10 or len(data) % 2:
        raise ValueError('image must contain at least five complete 16-bit words')
    words = struct.unpack(f'<{len(data) // 2}H', data)
    declared_words = words[3]
    if declared_words != len(words):
        raise ValueError(f'declared length {declared_words:#x} differs from '
                         f'captured length {len(words):#x}')
    if LOAD_ADDRESS + len(words) > 0x10000:
        raise ValueError('image exceeds the ISP 64K-word RAM aperture')
    checksum = sum(words) & 0xffff
    if checksum:
        raise ValueError(f'16-bit checksum is {checksum:#06x}, expected zero')
    # The same first two words occur in QLogic's published ISP12160 image.
    # Their instruction semantics are deliberately not assumed here.
    if words[0] != 0x0804:
        raise ValueError(f'unexpected first word {words[0]:#06x}')
    if not LOAD_ADDRESS <= words[1] < LOAD_ADDRESS + len(words):
        raise ValueError(f'second word {words[1]:#06x} is outside the image')
    # QLogic packs two display characters per word, high byte first. The
    # captured header ends at 0x2400; internal NULs separate its fields.
    try:
        text_end = words.index(0x2400, 5, min(len(words), 128))
    except ValueError as error:
        raise ValueError('QLogic header terminator is absent') from error
    header_bytes = b''.join(struct.pack('>H', word) for word in words[5:text_end])
    header = header_bytes.decode('ascii').replace('\0', ' ').strip()
    if not header.startswith('COPYRIGHT ') or ' ISP1216 Firmware ' not in header:
        raise ValueError('QLogic ISP1216 text header is absent')
    return {
        'load_address': LOAD_ADDRESS,
        'end_address': LOAD_ADDRESS + len(words),
        'declared_words': declared_words,
        'first_word': words[0],
        'second_word': words[1],
        'header': header,
        'checksum': checksum,
        'sha256': hashlib.sha256(data).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    args = parser.parse_args()
    report = inspect_image(args.image.read_bytes())
    for key, value in report.items():
        print(f'{key}={value:#x}' if isinstance(value, int) else f'{key}={value}')


if __name__ == '__main__':
    main()

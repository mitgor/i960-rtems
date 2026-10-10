#!/usr/bin/env python3
"""Extract the verified public-symbol block from this exact decoded vendor EXE.

This is a version-specific offline analysis tool, not a general MZ/debug parser.
Vendor bytes are never executed. Addresses precede names in each record.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

SHA256 = '1be1c11f5e030be80cd55b5c9215734f472daf4ee651abd1da57284e4888c552'
START, END = 0x5a29e, 0x5bba7
ANCHORS = {'_GetImageHeader': 0x1800, '_ReadFile': 0x53ef,
           '_load_image2': 0x5232, '_load_image': 0x52d5,
           '_StoreRoadRunnerImage': 0x552e, '_ProgramRoadRunnerImage': 0x58f7,
           '_StoreI2O': 0x5ac4, '_ReadFlashDescTbl': 0x3c83,
           '_xdcmd': 0x8722, '_PCI_issue_cmd': 0x992d}


def records(data, start, end, header_size):
    if not 0 <= start <= end <= len(data):
        raise ValueError('invalid symbol block bounds')
    result = {}
    pos = start
    while pos < end:
        if end - pos < 7:
            raise ValueError('truncated symbol record')
        offset, segment, flags, size = struct.unpack_from('<HHHB', data, pos)
        stop = pos + 7 + size
        if not size or stop > end:
            raise ValueError('invalid symbol name length')
        raw = data[pos + 7:stop]
        if any(c < 32 or c > 126 for c in raw):
            raise ValueError('invalid symbol name')
        name = raw.decode('ascii')
        if name in result:
            raise ValueError('duplicate symbol name')
        result[name] = dict(record_file_offset=pos, offset=offset, segment=segment,
                            flags=flags, file_offset=header_size + segment * 16 + offset)
        pos = stop
    return result


def analyze(data):
    digest = hashlib.sha256(data).hexdigest()
    if digest != SHA256:
        raise ValueError('unsupported vendor binary hash; refuse guessed symbol bounds')
    if data[:2] != b'MZ':
        raise ValueError('expected decoded MZ executable')
    header_size = struct.unpack_from('<H', data, 8)[0] * 16
    symbols = records(data, START, END, header_size)
    for name, address in ANCHORS.items():
        if symbols[name]['file_offset'] != address or data[address:address + 3] != b'\x55\x8b\xec':
            raise ValueError(f'code anchor failed: {name}')
    return dict(sha256=digest, mz_header_bytes=header_size,
                symbol_count=len(symbols), symbols=symbols)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exe', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(analyze(args.exe.read_bytes()), indent=2))
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')

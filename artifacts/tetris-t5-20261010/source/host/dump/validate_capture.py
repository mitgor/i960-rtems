#!/usr/bin/env python3
"""Classify one dac960dump experiment; never label a capture a flash backup."""
import argparse
import hashlib
import json
import pathlib
import re


def classify(directory):
    directory = pathlib.Path(directory)
    log = (directory / 'result.txt').read_text()
    header = re.search(r'bdf=(\S+) attempt=(\d+) length=(\d+) offset=([0-9a-f]+)', log)
    if not header:
        raise ValueError('missing experiment header')
    completed = re.findall(r'complete op=([0-9a-f]+) id=([0-9a-f]+) status=([0-9a-f]+) changed=(\d+) guard-changed=(\d+)', log)
    results = [{'opcode': int(op, 16), 'id': int(tag, 16), 'status': int(st, 16),
                'changed': int(n), 'guard_changed': int(guard)}
               for op, tag, st, n, guard in completed]
    length = int(header[3])
    files = {}
    for name in ['enquiry-before.bin', 'read-a5.bin', 'read-5a.bin', 'enquiry-after.bin']:
        b = (directory / name).read_bytes()
        expected = length if name.startswith('read-') else 512
        if len(b) != expected:
            raise ValueError(f'{name}: expected {expected} bytes, got {len(b)}')
        files[name] = b
    before, after = files['enquiry-before.bin'], files['enquiry-after.bin']
    a, b = files['read-a5.bin'], files['read-5a.bin']
    verified_transport = (
        [x['opcode'] for x in results] in ([0x1c, 0x21, 0x21, 0x1c],
                                             [0x1c, 0x20, 0x20, 0x1c]) and
        [x['id'] for x in results] == [1, 2, 3, 4] and
        all(x['status'] == 0 and x['guard_changed'] == 0 for x in results) and
        'pending=0;' in log and
        before[4:8] == after[4:8] and before[4:6] == bytes([4, 7])
    )
    a_changed = sum(x != 0xa5 for x in a)
    b_changed = sum(x != 0x5a for x in b)
    if verified_transport and a_changed == b_changed == 0:
        outcome = 'no_host_buffer_update'
    elif verified_transport and a == b and (a == bytes([0xa5]) * length or a == bytes([0x5a]) * length):
        outcome = 'repeatable_sentinel_value_not_firmware'
    elif verified_transport and a == b:
        outcome = 'repeatable_capture_requires_semantic_and_image_validation'
    else:
        outcome = 'unverified_capture'
    return {
        'bdf': header[1], 'offset': int(header[4], 16), 'length': length,
        'transport_checks_passed': verified_transport, 'outcome': outcome,
        'firmware_version_bytes_before': list(before[4:8]),
        'firmware_version_bytes_after': list(after[4:8]),
        'changed_from_a5': a_changed, 'changed_from_5a': b_changed,
        'captures_equal': a == b, 'transactions': results,
        'sha256': {name: hashlib.sha256(data).hexdigest() for name, data in files.items()},
        'physical_flash_backup_verified': False,
        'command_direction_verified': verified_transport and results[1]['opcode'] == 0x20,
        'source_is_physical_flash_verified': False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory')
    a = p.parse_args()
    try:
        result = classify(a.directory)
    except (OSError, ValueError) as error:
        p.exit(1, f'capture validation failed: {error}\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

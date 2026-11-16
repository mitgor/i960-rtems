#!/usr/bin/env python3
"""Sweep the exploratory reset-time board byte for the failed-spare image."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


FAILED_SPARE_SHA256 = '6f16d71310d75937b5f3961b1faae81eab3258a29371c8505d788c50c545e3bd'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--emulator', required=True, type=Path)
    parser.add_argument('--image', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    digest = hashlib.sha256(args.image.read_bytes()).hexdigest()
    if digest != FAILED_SPARE_SHA256:
        parser.error(f'image SHA-256 {digest} is not the failed-spare candidate')
    rows = []
    for board_id in range(32):
        run = subprocess.run(
            [str(args.emulator.resolve()), str(args.image.resolve()),
             '3000000', f'--board-id={board_id}', '--quiet-trace'],
            capture_output=True, text=True, timeout=30)
        report = re.search(r'^checkpoint native-report ([0-9a-f ]+)$',
                           run.stdout, re.MULTILINE)
        stop = re.search(r'^stop cycle=(\d+) reason=([^ \n]+)(?: ip=([0-9a-f]+))?$',
                         run.stdout, re.MULTILINE)
        result = {
            'board_id': board_id,
            'returncode': run.returncode,
            'report': report.group(1).split() if report else None,
            'stop_cycle': int(stop.group(1)) if stop else None,
            'stop_reason': stop.group(2) if stop else None,
            'stop_ip': stop.group(3) if stop else None,
            'first_unmodeled_read': (
                re.search(r'^audit first-unmodeled-read=([0-9a-f]+)$',
                          run.stdout, re.MULTILINE) or [None, None])[1],
        }
        result['passed'] = (
            result['report'] is not None and len(result['report']) >= 8 and
            result['report'][7] == '50415353' and
            result['stop_reason'] == 'self-loop' and
            result['stop_ip'] == 'c0010030')
        rows.append(result)
        print(f"board_id={board_id:02d} passed={int(result['passed'])} "
              f"cycle={result['stop_cycle']} stop={result['stop_reason']} "
              f"ip={result['stop_ip']}", flush=True)
    document = {'image_sha256': digest, 'model': 'exploratory reset-byte override',
                'rows': rows}
    args.output.write_text(json.dumps(document, indent=2) + '\n')
    print(f"passed={sum(row['passed'] for row in rows)}/32 "
          f"budget={sum(row['stop_reason'] == 'budget' for row in rows)}")


if __name__ == '__main__':
    main()

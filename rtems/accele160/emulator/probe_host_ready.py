#!/usr/bin/env python3
"""Test the stock firmware's two PCI-command readiness conditions offline."""
import argparse
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import time


def one_run(emulator, image, commands, step_chunks):
    with tempfile.TemporaryDirectory(prefix='accele160-host-ready-') as directory:
        path = Path(directory) / 'bridge.sock'
        process = subprocess.Popen(
            [str(emulator.resolve()), str(image.resolve()), '60000000',
             '--board-id=11', '--quiet-trace', f'--bridge-socket={path}'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 90
            while not path.exists():
                if process.poll() is not None:
                    raise AssertionError(f'emulator exited: {process.communicate()}')
                if time.monotonic() > deadline:
                    raise TimeoutError('emulator did not reach bridge-ready')
                time.sleep(0.05)
            with socket.socket(socket.AF_UNIX) as connection:
                connection.connect(str(path))
                stream = connection.makefile('rwb', buffering=0)
                for command in [*commands, *(['S 1000000'] * step_chunks)]:
                    stream.write((command + '\n').encode('ascii'))
                    answer = stream.readline().decode('ascii').strip()
                    if not answer or answer == 'ERR':
                        raise AssertionError(f'{command}: {answer}')
        finally:
            process.terminate()
            output, error = process.communicate(timeout=5)
    steps = [line for line in output.splitlines()
             if line.startswith('checkpoint bridge-step ')]
    if len(steps) != step_chunks:
        raise AssertionError(output + error)
    counts = [re.search(r'gate-loops=(\d+) gate-exits=(\d+) unmask=(\d+)', line)
              for line in steps]
    if any(match is None for match in counts):
        raise AssertionError('\n'.join(steps))
    if any('fault=ffffffff' not in line for line in steps):
        raise AssertionError('i960 stopped on a fault:\n' + '\n'.join(steps))
    totals = tuple(sum(int(match.group(i)) for match in counts)
                   for i in range(1, 4))
    samples = [line for line in output.splitlines()
               if line.startswith('checkpoint bridge-sample ')]
    return totals, steps[-1], samples[-6:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--emulator', required=True, type=Path)
    parser.add_argument('--image', required=True, type=Path)
    parser.add_argument('--both-chunks', type=int, default=1)
    parser.add_argument('--case', choices=['all', 'none', 'atu-only',
                                           'bridge-only', 'both',
                                           'both-doorbell-2'], default='all')
    args = parser.parse_args()
    cases = [
        ('none', []),
        ('atu-only', ['H 1204 6']),
        ('bridge-only', ['H 1004 4']),
        ('both', ['H 1204 6', 'H 1004 4']),
        ('both-doorbell-2', ['H 1204 6', 'H 1004 4', 'D 2']),
    ]
    for name, commands in cases:
        if args.case != 'all' and name != args.case:
            continue
        chunks = args.both_chunks if name.startswith('both') else 1
        (loops, exits, unmask), line, samples = one_run(
            args.emulator, args.image, commands, chunks)
        print(f'{name}: chunks={chunks} loops={loops} exits={exits} '
              f'unmask={unmask} final={line}')
        if name.startswith('both'):
            for sample in samples:
                print(f'  {sample}')
        if name.startswith('both'):
            assert exits > 0, 'stock did not pass the PCI readiness gate'
            if name == 'both-doorbell-2':
                assert 'next-wait=0' in line, 'stock still waits for doorbell bit 1'
        else:
            assert loops > 0 and exits == 0, f'{name} unexpectedly passed the gate'
    if args.case == 'all':
        print('host_readiness_gate=PASS requires_atu_and_bridge_commands=PASS')
    else:
        print(f'host_readiness_case={args.case} PASS')


if __name__ == '__main__':
    main()

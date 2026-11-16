#!/usr/bin/env python3
"""Dump a bounded RAM range from a paused offline i960 emulator."""
import argparse
from pathlib import Path
import socket
import subprocess
import tempfile
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--emulator', required=True, type=Path)
    parser.add_argument('--image', required=True, type=Path)
    parser.add_argument('--address', required=True, type=lambda value: int(value, 0))
    parser.add_argument('--size', required=True, type=lambda value: int(value, 0))
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.address & 3 or args.size < 1 or args.size > 65536 or args.size & 3:
        raise ValueError('address and size must be word-aligned; size <= 65536')
    with tempfile.TemporaryDirectory(prefix='accele160-dump-') as directory:
        path = Path(directory) / 'bridge.sock'
        process = subprocess.Popen(
            [str(args.emulator.resolve()), str(args.image.resolve()),
             '60000000', '--board-id=11', '--quiet-trace',
             f'--bridge-socket={path}'],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 90
            while not path.exists():
                if process.poll() is not None:
                    raise AssertionError(f'emulator exited: {process.communicate()}')
                if time.monotonic() > deadline:
                    raise TimeoutError('emulator did not reach bridge-ready')
                time.sleep(0.05)
            contents = bytearray()
            with socket.socket(socket.AF_UNIX) as connection:
                connection.connect(str(path))
                stream = connection.makefile('rwb', buffering=0)
                for address in range(args.address, args.address + args.size, 4):
                    stream.write(f'R {address:08x} 4 0\n'.encode('ascii'))
                    answer = stream.readline().decode('ascii').strip()
                    if not answer or answer == 'ERR':
                        raise AssertionError(f'{address:#x}: {answer}')
                    contents.extend(int(answer, 16).to_bytes(4, 'little'))
            args.output.write_bytes(contents)
            print(f'ram_dump=PASS address={args.address:08x} '
                  f'size={args.size} output={args.output}')
        finally:
            process.terminate()
            process.communicate(timeout=5)


if __name__ == '__main__':
    main()

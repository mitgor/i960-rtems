#!/usr/bin/env python3
"""Export one post-run simulated i960 RAM page through the local bridge."""
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
    parser.add_argument('--cycles', required=True, type=int)
    parser.add_argument('--base', required=True, type=lambda s: int(s, 0))
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.base < 0xc0000000 or args.base > 0xc0fff000 or args.base & 0xfff:
        raise ValueError('base must be a 4 KiB-aligned address in controller RAM')
    if args.output.exists():
        raise FileExistsError(args.output)
    with tempfile.TemporaryDirectory(prefix='accele160-dump-') as directory:
        path = Path(directory) / 'bridge.sock'
        process = subprocess.Popen(
            [str(args.emulator.resolve()), str(args.image.resolve()),
             str(args.cycles), '--board-id=11', '--quiet-trace',
             f'--bridge-socket={path}'], stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 90
            while not path.exists():
                if process.poll() is not None:
                    raise RuntimeError(f'emulator exited: {process.communicate()}')
                if time.monotonic() > deadline:
                    raise TimeoutError('bridge did not become ready')
                time.sleep(0.05)
            output = bytearray()
            with socket.socket(socket.AF_UNIX) as connection:
                connection.connect(str(path))
                with connection.makefile('rwb') as stream:
                    for offset in range(0, 4096, 4):
                        stream.write(f'R {args.base + offset:08x} 4 00000000\n'.encode())
                        stream.flush()
                        reply = stream.readline().strip()
                        output += int(reply, 16).to_bytes(4, 'little')
            args.output.write_bytes(output)
            print(f'dumped=4096 base={args.base:08x} path={args.output}')
        finally:
            process.terminate()
            process.communicate(timeout=5)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Prove native first mailbox stays pending until host PCI readiness appears."""
import argparse
import json
from pathlib import Path
import socket
import subprocess
import tempfile
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--emulator', type=Path, required=True)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--first-fixture', type=Path, required=True)
    args = parser.parse_args()
    fixture = json.loads(args.first_fixture.read_text())
    packet = fixture['request']['mailbox_hex']
    with tempfile.TemporaryDirectory(prefix='accele160-readiness-') as temp:
        bridge = Path(temp) / 'bridge.sock'
        with (Path(temp) / 'emu.log').open('w') as log:
            process = subprocess.Popen([
                str(args.emulator.resolve()), str(args.image.resolve()),
                '3000000', '--board-id=11', '--quiet-trace',
                f'--bridge-socket={bridge}'], stdout=log,
                stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 15
                while not bridge.exists():
                    if process.poll() is not None:
                        raise RuntimeError('emulator exited before bridge')
                    if time.monotonic() > deadline:
                        raise TimeoutError('emulator bridge unavailable')
                    time.sleep(0.05)
                with socket.socket(socket.AF_UNIX) as connection:
                    connection.connect(str(bridge))
                    wire = connection.makefile('rwb', buffering=0)

                    def command(line):
                        wire.write((line + '\n').encode('ascii'))
                        answer = wire.readline().strip()
                        if len(answer) != 8 or answer == b'ERR':
                            raise AssertionError(f'{line}: {answer!r}')
                        return int(answer, 16)

                    def report(index):
                        return command(f'R {0xc0001f00 + 4 * index:08x} 4 0')

                    assert report(7) == 0x50415353  # RTEMS scheduler reached
                    command('E 7')
                    command(f'M 000000000009f120 {packet}')
                    command('D 1')
                    command('S 100000')
                    assert report(31) == 0 and report(21) == 0
                    assert command('I 132c') == 0
                    assert command('I 1320') & 1
                    # Providing just the boot doorbell still cannot satisfy
                    # the bridge and RAID PCI command bits.
                    command('D 2')
                    command('S 100000')
                    assert report(31) == 0 and command('I 132c') == 0
                    command('H 1004 107')
                    command('H 1204 107')
                    command('S 100000')
                    assert report(31) == 1 and report(21) == 2
                    assert command('I 1318') == 0x7f
                    assert command('I 132c') == 1
                    wire.close()
            finally:
                process.terminate()
                process.wait(timeout=5)
    print('native_readiness_negative=PASS pending_without_PCI=PASS completed_with_PCI=PASS')


if __name__ == '__main__':
    main()

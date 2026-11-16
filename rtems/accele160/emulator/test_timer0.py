#!/usr/bin/env python3
"""Check Jx timer-0 prescale, reload and TINT0 pending on a synthetic ROM."""
from pathlib import Path
import socket
import struct
import subprocess
import tempfile
import time

ROOT = Path(__file__).parent


def main():
    image = bytearray(0x100000)
    probe = (ROOT / 'isa_probe.bin').read_bytes()
    image[0xf0000:0xf0000 + len(probe)] = probe
    entry, prcb = 0xfeff0000, 0xfeffdd20
    struct.pack_into('<III', image, 0xfff40, entry, prcb,
                     (-entry - prcb) & 0xffffffff)
    with tempfile.TemporaryDirectory(prefix='accele160-timer0-') as directory:
        rom = Path(directory) / 'timer.rom'
        sock = Path(directory) / 'timer.sock'
        rom.write_bytes(image)
        process = subprocess.Popen(
            [str(ROOT / 'build/accele160-emu'), str(rom), '1000',
             '--quiet-trace', '--explore-timer-clock', f'--bridge-socket={sock}'],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 20
            while not sock.exists():
                if process.poll() is not None:
                    raise AssertionError(process.communicate())
                if time.monotonic() > deadline:
                    raise TimeoutError('emulator bridge did not start')
                time.sleep(0.01)
            with socket.socket(socket.AF_UNIX) as connection:
                connection.connect(str(sock))
                stream = connection.makefile('rwb', buffering=0)

                def request(command):
                    stream.write((command + '\n').encode('ascii'))
                    answer = stream.readline().decode('ascii').strip()
                    if not answer or answer == 'ERR':
                        raise AssertionError(f'{command}: {answer}')
                    return int(answer, 16)

                assert request('C ff000308 0') == 0
                assert request('C ff008500 0') == 0
                assert request('C ff000300 3') == 3
                assert request('C ff000304 3') == 3
                assert request('C ff000308 36') == 0x36
                request('S 23')
                assert request('I ff000304') == 1
                assert request('I ff008500') == 0
                request('S 1')
                assert request('I ff000304') == 3
                assert request('I ff008500') & (1 << 12)
                assert request('C ff008500 0') == 0
                request('S 24')
                assert request('I ff000304') == 3
                assert request('I ff008500') & (1 << 12)
                print('timer0=PASS prescale_8=PASS reload=PASS tint0_ipnd=PASS '
                      'cpu_delivery=UNMODELED')
        finally:
            process.terminate()
            process.communicate(timeout=5)


if __name__ == '__main__':
    main()

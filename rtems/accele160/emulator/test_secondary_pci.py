#!/usr/bin/env python3
"""Check opt-in, captured QLogic secondary PCI configuration readback."""
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
    with tempfile.TemporaryDirectory(prefix='accele160-secondary-pci-') as directory:
        rom = Path(directory) / 'probe.rom'
        sock = Path(directory) / 'bridge.sock'
        rom.write_bytes(image)
        process = subprocess.Popen(
            [str(ROOT / 'build/accele160-emu'), str(rom), '1000',
             '--quiet-trace', '--explore-qlogic-pci', f'--bridge-socket={sock}'],
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

                for offset, expected in ((0, 0x10161077), (4, 0x02b00006),
                                         (8, 0x01000006), (0x10, 1),
                                         (0x14, 0xfff00000)):
                    selector = 0x10000 | offset
                    assert request(f'C 12a8 {selector:x}') == selector
                    assert request('I 12b0') == expected
                assert request('C 12a8 20000') == 0x20000
                assert request('I 12b0') == 0xffffffff
                assert request('C 12a8 1000c') == 0x1000c
                assert request('I 12b0') == 0  # unobserved present-device dword
                assert request('I 12a8') == 0x1000c
                print('secondary_pci=PASS qlogic_id=10161077 absent_slot=ffffffff '
                      'selector_restore=PASS')
        finally:
            process.terminate()
            process.communicate(timeout=5)


if __name__ == '__main__':
    main()

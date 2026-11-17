#!/usr/bin/env python3
"""Verify both PCI functions' command writes reach stock i960 firmware."""
import argparse
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qemu', required=True, type=Path)
    parser.add_argument('--emulator', required=True, type=Path)
    parser.add_argument('--image', required=True, type=Path)
    parser.add_argument('--ack-status', action='store_true',
                        help='replay myrs LP init ACK_STS write at BAR0+0x20')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='accele160-pci-command-') as directory:
        bridge_socket = Path(directory) / 'bridge.sock'
        emu = subprocess.Popen(
            [str(args.emulator.resolve()), str(args.image.resolve()),
             '60000000', '--board-id=11', '--quiet-trace',
             f'--bridge-socket={bridge_socket}'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        qemu = None
        try:
            deadline = time.monotonic() + 90
            while not bridge_socket.exists():
                if emu.poll() is not None:
                    raise AssertionError(f'emulator exited: {emu.communicate()}')
                if time.monotonic() > deadline:
                    raise TimeoutError('emulator did not reach bridge-ready')
                time.sleep(0.05)
            qemu = subprocess.Popen(
                [str(args.qemu.resolve()), '-machine', 'pc', '-m', '64',
                 '-display', 'none', '-nodefaults', '-accel', 'qtest',
                 '-device', 'accele160-pci-bridge,addr=05.0,multifunction=on',
                 '-device', f'accele160-probe,addr=05.1,bridge-socket={bridge_socket}',
                 '-qtest', 'stdio'], stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, bufsize=1)

            def command(line):
                qemu.stdin.write(line + '\n')
                qemu.stdin.flush()
                response = qemu.stdout.readline().strip()
                if not response.startswith('OK'):
                    details = qemu.stderr.read() if qemu.poll() is not None else ''
                    raise AssertionError(f'{line}: {response}; qemu={qemu.poll()} {details}')
                return int(response.split()[1], 0) if len(response.split()) > 1 else None

            command('outl 0xcf8 0x80002800')
            assert command('inl 0xcfc') == 0x29628086
            command('outl 0xcf8 0x80002808')
            assert command('inl 0xcfc') >> 16 == 0x0604
            command('outl 0xcf8 0x8000280c')
            assert (command('inl 0xcfc') >> 16) & 0xff == 0x81
            command('outl 0xcf8 0x80002900')
            assert command('inl 0xcfc') == 0x00501069
            command('outl 0xcf8 0x80002904')
            command('outw 0xcfc 0x0006')
            assert command('inw 0xcfc') == 6
            command('outl 0xcf8 0x80002804')
            command('outw 0xcfc 0x0004')
            assert command('inw 0xcfc') == 4
            if args.ack_status:
                command('outl 0xcf8 0x80002910')
                command('outl 0xcfc 0xf0000008')
                command('writeb 0xf0000020 0x02')
            qemu.terminate()
            _, qemu_stderr = qemu.communicate(timeout=5)
            qemu = None

            with socket.socket(socket.AF_UNIX) as connection:
                connection.connect(str(bridge_socket))
                stream = connection.makefile('rwb', buffering=0)

                def request(line):
                    stream.write((line + '\n').encode('ascii'))
                    answer = stream.readline().decode('ascii').strip()
                    if not answer or answer == 'ERR':
                        raise AssertionError(f'{line}: {answer}')
                    return int(answer, 16)

                assert request('I 1004') & 4
                assert request('I 1204') & 6 == 6
                doorbell = request('I 1320')
                if args.ack_status:
                    assert doorbell & 2, f'ACK_STS did not reach i960: {doorbell:#x}'
                else:
                    assert doorbell == 0, f'unexpected doorbell: {doorbell:#x}'
                assert request('S 1000000') != 0
            print('pci_functions=PASS bridge=8086:2962 raid=1069:0050 '
                  'command_mirror=PASS')
            assert 'accele160 pci-command local=0x1004 value=0x0004' in qemu_stderr
            assert 'accele160 pci-command local=0x1204 value=0x0006' in qemu_stderr
            if args.ack_status:
                assert 'accele160 lp ack-status posted to i960 doorbell bit 1' in qemu_stderr
        finally:
            if qemu is not None:
                qemu.terminate()
                qemu.communicate(timeout=5)
            emu.terminate()
            emu_stdout, _ = emu.communicate(timeout=5)
        steps = [line for line in emu_stdout.splitlines()
                 if line.startswith('checkpoint bridge-step ')]
        assert len(steps) == 1 and 'fault=ffffffff' in steps[0], steps
        wait = re.search(r'next-wait=(\d+)', steps[0])
        assert 'gate-exits=1' in steps[0] and wait, steps[0]
        if args.ack_status:
            assert int(wait.group(1)) == 0, steps[0]
            print('stock_lp_init_ack=PASS gate_exits=1 doorbell_bit1=HOST_POSTED')
        else:
            assert int(wait.group(1)) > 0, steps[0]
            print('stock_pci_readiness=PASS gate_exits=1 doorbell_bit1=PENDING')


if __name__ == '__main__':
    main()

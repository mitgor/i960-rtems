#!/usr/bin/env python3
"""Gate the native i960 ROM replies through a live QEMU option ROM."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--emulator', type=Path, required=True)
    parser.add_argument('--qemu', type=Path, required=True)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--bios', type=Path, required=True)
    parser.add_argument('--request-fixture', type=Path, required=True)
    parser.add_argument('--second-fixture', type=Path,
                        help='exact captured stock IOCTL 0x11 request and reply')
    parser.add_argument('--third-fixture', type=Path,
                        help='exact captured stock IOCTL 0x15 request and reply')
    parser.add_argument('--fourth-fixture', type=Path,
                        help='exact captured stock IOCTL 0xd0 request and reply')
    parser.add_argument('--fifth-fixture', type=Path,
                        help='exact captured stock IOCTL 0x2d request and reply')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=5)
    args = parser.parse_args()
    if args.third_fixture and not args.second_fixture:
        parser.error('--third-fixture requires --second-fixture')
    if args.fourth_fixture and not args.third_fixture:
        parser.error('--fourth-fixture requires --third-fixture')
    if args.fifth_fixture and not args.fourth_fixture:
        parser.error('--fifth-fixture requires --fourth-fixture')
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    for name in ('native-coupled-emu.log', 'native-coupled-qemu.log',
                 'native-coupled-rom.json', 'native-coupled-gate.json'):
        if (output / name).exists():
            raise FileExistsError(output / name)
    fixture = json.loads(args.request_fixture.read_text())
    with tempfile.TemporaryDirectory(prefix='accele160-native-coupled-') as temp:
        bridge = Path(temp) / 'bridge.sock'
        with (output / 'native-coupled-emu.log').open('w') as log:
            emulator = subprocess.Popen(
                [str(args.emulator.resolve()), str(args.image.resolve()),
                 '60000000', '--board-id=11', '--quiet-trace',
                 f'--bridge-socket={bridge}'],
                stdout=log, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 15
                while not bridge.exists():
                    if emulator.poll() is not None:
                        raise RuntimeError('i960 emulator exited before bridge')
                    if time.monotonic() > deadline:
                        raise TimeoutError('i960 bridge did not appear')
                    time.sleep(0.05)
                command = [
                    'python3', str(Path(__file__).with_name('run_pci_rom.py')),
                    str(args.image.resolve()), '--qemu',
                    str(args.qemu.resolve()), '--bios', str(args.bios.resolve()),
                    '--bridge-socket', str(bridge), '--explore-native-poll',
                    '--seconds', str(args.seconds), '--output',
                    str(output / 'native-coupled-rom.json'),
                    '--qemu-stderr-output',
                    str(output / 'native-coupled-qemu.log'),
                ]
                if args.second_fixture:
                    command.append('--trace-live-reply')
                result = subprocess.run(command, capture_output=True,
                                        text=True, timeout=args.seconds + 45)
                if result.returncode:
                    raise RuntimeError(f'QEMU ROM probe failed: {result.stderr[-2000:]}')
            finally:
                emulator.terminate()
                emulator.wait(timeout=5)
    rom = json.loads((output / 'native-coupled-rom.json').read_text())
    qemu_lines = (output / 'native-coupled-qemu.log').read_text(
        errors='replace').splitlines()
    first = fixture['request']
    expected = {name: first[name] for name in
                ('id', 'opcode', 'control', 'transfer_bytes', 'ioctl',
                 'sg0_dma', 'sg0_bytes')}
    if not rom['option_rom_entry_executed'] or not rom['native_ctlr_info_completed']:
        raise AssertionError('native first ROM completion missing')
    if len(rom['mailbox_requests']) < 2 or rom['mailbox_requests'][0] != expected:
        raise AssertionError('first ROM mailbox differs from fixture')
    if rom['mailbox_requests'][1]['ioctl'] != 0x11:
        raise AssertionError('ROM did not advance to second IOCTL')
    completion = [line for line in qemu_lines if line.startswith(
        'accele160 EXPLORE native firmware completion ')]
    if len(completion) != (5 if args.fifth_fixture else
                           4 if args.fourth_fixture else
                           3 if args.third_fixture else
                           2 if args.second_fixture else 1) or not all(
            part in completion[0] for part in (
            'ioctl=0x01', 'id=127', 'status=0x0000',
            'residual=0xfffffe00', 'dma=0x0009f3e0', 'bytes=512')):
        raise AssertionError('unexpected native completion record')
    second_reply_sha = None
    if args.second_fixture:
        second = json.loads(args.second_fixture.read_text())
        request_bytes = (args.second_fixture.parent /
                         second['request_file']).read_bytes()
        reply_bytes = (args.second_fixture.parent /
                       second['reply_file']).read_bytes()
        if (hashlib.sha256(request_bytes).hexdigest() != second['request_sha256'] or
                hashlib.sha256(reply_bytes).hexdigest() != second['reply_sha256'] or
                len(request_bytes) != 64 or len(reply_bytes) != 128):
            raise AssertionError('second stock fixture checksum or length mismatch')
        if (len(rom['mailbox_requests']) < 3 or
                bytes.fromhex(rom['mailbox_bytes_hex'][1]) != request_bytes or
                rom['mailbox_requests'][2]['ioctl'] != 0x15):
            raise AssertionError('ROM did not submit captured second request then advance')
        if len(completion) < 2 or not all(part in completion[1] for part in (
                'ioctl=0x11', 'id=127', 'status=0x0000',
                'residual=0x00000000', 'dma=0x0009f3e0', 'bytes=128')):
            raise AssertionError('unexpected second native completion')
        traced = [line.partition(' hex=')[2] for line in qemu_lines if line.startswith(
            'accele160 EXPLORE live reply ioctl=0x11 id=127 bytes=128 hex=')]
        if len(traced) != 1 or bytes.fromhex(traced[0]) != reply_bytes:
            raise AssertionError('second native output differs from stock fixture')
        second_reply_sha = hashlib.sha256(bytes.fromhex(traced[0])).hexdigest()
    third_reply_sha = None
    if args.third_fixture:
        third = json.loads(args.third_fixture.read_text())
        request_bytes = (args.third_fixture.parent /
                         third['request_file']).read_bytes()
        reply_bytes = (args.third_fixture.parent /
                       third['reply_file']).read_bytes()
        if (hashlib.sha256(request_bytes).hexdigest() != third['request_sha256'] or
                hashlib.sha256(reply_bytes).hexdigest() != third['reply_sha256'] or
                len(request_bytes) != 64 or len(reply_bytes) != 64):
            raise AssertionError('third stock fixture checksum or length mismatch')
        if (len(rom['mailbox_requests']) < 4 or
                bytes.fromhex(rom['mailbox_bytes_hex'][2]) != request_bytes or
                rom['mailbox_requests'][3]['ioctl'] != 0xd0):
            raise AssertionError('ROM did not submit captured third request then advance')
        if not all(part in completion[2] for part in (
                'ioctl=0x15', 'id=127', 'status=0x0000',
                'residual=0x00000000', 'dma=0x0009f3e0', 'bytes=64')):
            raise AssertionError('unexpected third native completion')
        traced = [line.partition(' hex=')[2] for line in qemu_lines if line.startswith(
            'accele160 EXPLORE live reply ioctl=0x15 id=127 bytes=64 hex=')]
        if len(traced) != 1 or bytes.fromhex(traced[0]) != reply_bytes:
            raise AssertionError('third native output differs from stock fixture')
        third_reply_sha = hashlib.sha256(bytes.fromhex(traced[0])).hexdigest()
    fourth_reply_sha = None
    if args.fourth_fixture:
        fourth = json.loads(args.fourth_fixture.read_text())
        request_bytes = (args.fourth_fixture.parent /
                         fourth['request_file']).read_bytes()
        reply_bytes = (args.fourth_fixture.parent /
                       fourth['reply_file']).read_bytes()
        if (hashlib.sha256(request_bytes).hexdigest() != fourth['request_sha256'] or
                hashlib.sha256(reply_bytes).hexdigest() != fourth['reply_sha256'] or
                len(request_bytes) != 64 or len(reply_bytes) != 128):
            raise AssertionError('fourth stock fixture checksum or length mismatch')
        if (len(rom['mailbox_requests']) < 5 or
                bytes.fromhex(rom['mailbox_bytes_hex'][3]) != request_bytes or
                rom['mailbox_requests'][4]['ioctl'] != 0x2d):
            raise AssertionError('ROM did not submit captured fourth request then advance')
        if not all(part in completion[3] for part in (
                'ioctl=0xd0', 'id=127', 'status=0x0000',
                'residual=0x00000000', 'dma=0x0009f3e0', 'bytes=128')):
            raise AssertionError('unexpected fourth native completion')
        traced = [line.partition(' hex=')[2] for line in qemu_lines if line.startswith(
            'accele160 EXPLORE live reply ioctl=0xd0 id=127 bytes=128 hex=')]
        if len(traced) != 1 or bytes.fromhex(traced[0]) != reply_bytes:
            raise AssertionError('fourth native output differs from stock fixture')
        fourth_reply_sha = hashlib.sha256(bytes.fromhex(traced[0])).hexdigest()
    fifth_reply_sha = None
    if args.fifth_fixture:
        fifth = json.loads(args.fifth_fixture.read_text())
        request_bytes = (args.fifth_fixture.parent /
                         fifth['request_file']).read_bytes()
        reply_bytes = (args.fifth_fixture.parent /
                       fifth['reply_file']).read_bytes()
        if (hashlib.sha256(request_bytes).hexdigest() != fifth['request_sha256'] or
                hashlib.sha256(reply_bytes).hexdigest() != fifth['reply_sha256'] or
                len(request_bytes) != 64 or len(reply_bytes) != 512):
            raise AssertionError('fifth stock fixture checksum or length mismatch')
        image_bytes = args.image.read_bytes()
        if (len(image_bytes) != 0x100000 or
                image_bytes[0xe0000:0xe0200] != reply_bytes):
            raise AssertionError('fifth reply must match this card image descriptor')
        if (len(rom['mailbox_requests']) < 5 or
                bytes.fromhex(rom['mailbox_bytes_hex'][4]) != request_bytes):
            raise AssertionError('ROM did not submit captured fifth request')
        if not all(part in completion[4] for part in (
                'ioctl=0x2d', 'id=127', 'status=0x0000',
                'residual=0x00000000', 'dma=0x0009f3e0', 'bytes=512')):
            raise AssertionError('unexpected fifth native completion')
        traced = [line.partition(' hex=')[2] for line in qemu_lines if line.startswith(
            'accele160 EXPLORE live reply ioctl=0x2d id=127 bytes=512 hex=')]
        if len(traced) != 1 or bytes.fromhex(traced[0]) != reply_bytes:
            raise AssertionError('fifth native output differs from stock fixture')
        fifth_reply_sha = hashlib.sha256(bytes.fromhex(traced[0])).hexdigest()
    image_sha = hashlib.sha256(args.image.read_bytes()).hexdigest()
    next_index = (5 if args.fifth_fixture else
                  4 if args.fourth_fixture else 3 if args.third_fixture else
                  2 if args.second_fixture else 1)
    gate = {
        'gate': 'PASS', 'image_sha256': image_sha,
        'first_mailbox_sha256': first['mailbox_sha256'],
        'first_completion': completion[0],
        'next_ioctl': (rom['mailbox_requests'][next_index]['ioctl']
                       if len(rom['mailbox_requests']) > next_index else None),
        'second_reply_sha256': second_reply_sha,
        'third_reply_sha256': third_reply_sha,
        'fourth_reply_sha256': fourth_reply_sha,
        'fifth_reply_sha256': fifth_reply_sha,
        'scope': 'exploratory i960 model plus modified QEMU and SeaBIOS',
        'physical_card_tested': False, 'safe_to_flash': False,
    }
    (output / 'native-coupled-gate.json').write_text(
        json.dumps(gate, indent=2) + '\n')
    print('native_qemu_mailboxes=PASS next_ioctl=' +
          (hex(gate['next_ioctl']) if gate['next_ioctl'] is not None else 'none'))


if __name__ == '__main__':
    main()

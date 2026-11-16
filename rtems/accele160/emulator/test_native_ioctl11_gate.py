#!/usr/bin/env python3
"""Check native ROM mailboxes and malformed later requests."""
import argparse
import hashlib
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
    parser.add_argument('--first-reply', type=Path, required=True)
    parser.add_argument('--second-fixture', type=Path, required=True)
    parser.add_argument('--corrupt-second-length', action='store_true')
    parser.add_argument('--third-fixture', type=Path)
    parser.add_argument('--corrupt-third-length', action='store_true')
    parser.add_argument('--fourth-fixture', type=Path)
    parser.add_argument('--corrupt-fourth-length', action='store_true')
    parser.add_argument('--fifth-fixture', type=Path)
    parser.add_argument('--corrupt-fifth-length', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.corrupt_third_length and not args.third_fixture:
        parser.error('--corrupt-third-length requires --third-fixture')
    if args.third_fixture and args.corrupt_second_length:
        parser.error('third request requires a valid second request')
    if args.fourth_fixture and (not args.third_fixture or args.corrupt_third_length):
        parser.error('fourth request requires a valid third request')
    if args.corrupt_fourth_length and not args.fourth_fixture:
        parser.error('--corrupt-fourth-length requires --fourth-fixture')
    if args.fifth_fixture and (not args.fourth_fixture or args.corrupt_fourth_length):
        parser.error('fifth request requires a valid fourth request')
    if args.corrupt_fifth_length and not args.fifth_fixture:
        parser.error('--corrupt-fifth-length requires --fifth-fixture')
    if args.output.exists():
        raise FileExistsError(args.output)
    first = json.loads(args.first_fixture.read_text())
    second = json.loads(args.second_fixture.read_text())
    packet1 = bytes.fromhex(first['request']['mailbox_hex'])
    reply1 = args.first_reply.read_bytes()
    packet2 = (args.second_fixture.parent / second['request_file']).read_bytes()
    reply2 = (args.second_fixture.parent / second['reply_file']).read_bytes()
    assert hashlib.sha256(packet1).hexdigest() == first['request']['mailbox_sha256']
    assert hashlib.sha256(reply1).hexdigest() == first['response_sha256']
    assert hashlib.sha256(packet2).hexdigest() == second['request_sha256']
    assert hashlib.sha256(reply2).hexdigest() == second['reply_sha256']
    packet3 = reply3 = None
    if args.third_fixture:
        third = json.loads(args.third_fixture.read_text())
        packet3 = (args.third_fixture.parent / third['request_file']).read_bytes()
        reply3 = (args.third_fixture.parent / third['reply_file']).read_bytes()
        assert hashlib.sha256(packet3).hexdigest() == third['request_sha256']
        assert hashlib.sha256(reply3).hexdigest() == third['reply_sha256']
        assert len(packet3) == 64 and len(reply3) == 64
        if args.corrupt_third_length:
            packet3 = bytearray(packet3)
            packet3[40] = 63
            packet3 = bytes(packet3)
    if args.corrupt_second_length:
        packet2 = bytearray(packet2)
        packet2[40] = 127
        packet2 = bytes(packet2)
    packet4 = reply4 = None
    if args.fourth_fixture:
        fourth = json.loads(args.fourth_fixture.read_text())
        packet4 = (args.fourth_fixture.parent / fourth['request_file']).read_bytes()
        reply4 = (args.fourth_fixture.parent / fourth['reply_file']).read_bytes()
        assert hashlib.sha256(packet4).hexdigest() == fourth['request_sha256']
        assert hashlib.sha256(reply4).hexdigest() == fourth['reply_sha256']
        assert len(packet4) == 64 and len(reply4) == 128
        if args.corrupt_fourth_length:
            packet4 = bytearray(packet4)
            packet4[40] = 127
            packet4 = bytes(packet4)
    packet5 = reply5 = None
    if args.fifth_fixture:
        fifth = json.loads(args.fifth_fixture.read_text())
        packet5 = (args.fifth_fixture.parent / fifth['request_file']).read_bytes()
        reply5 = (args.fifth_fixture.parent / fifth['reply_file']).read_bytes()
        assert hashlib.sha256(packet5).hexdigest() == fifth['request_sha256']
        assert hashlib.sha256(reply5).hexdigest() == fifth['reply_sha256']
        assert len(packet5) == 64 and len(reply5) == 512
        if args.corrupt_fifth_length:
            packet5 = bytearray(packet5)
            packet5[40] = 0xff
            packet5[41] = 0x01
            packet5 = bytes(packet5)
    with tempfile.TemporaryDirectory(prefix='accele160-native-ioctl11-') as temp:
        bridge = Path(temp) / 'bridge.sock'
        with args.output.with_suffix('.emu.log').open('w') as log:
            process = subprocess.Popen(
                [str(args.emulator.resolve()), str(args.image.resolve()),
                 '3000000', '--board-id=11', '--quiet-trace',
                 f'--bridge-socket={bridge}'],
                stdout=log, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 15
                while not bridge.exists():
                    if process.poll() is not None:
                        raise RuntimeError('i960 emulator exited before bridge')
                    if time.monotonic() > deadline:
                        raise TimeoutError('i960 bridge did not appear')
                    time.sleep(0.05)
                with socket.socket(socket.AF_UNIX) as connection:
                    connection.connect(str(bridge))
                    wire = connection.makefile('rwb', buffering=0)

                    def raw(line):
                        wire.write((line + '\n').encode('ascii'))
                        return wire.readline().strip()

                    def command(line):
                        answer = raw(line)
                        if len(answer) != 8 or answer == b'ERR':
                            raise AssertionError(f'{line}: {answer!r}')
                        return int(answer, 16)

                    def report(index):
                        return command(f'R {0xc0001f00 + index * 4:08x} 4 0')

                    def output(length):
                        return b''.join(command(f'U {0x9f3e0 + i * 4:08x}')
                                        .to_bytes(4, 'little')
                                        for i in range(length // 4))

                    assert report(7) == 0x50415353
                    command('H 1004 107')
                    command('H 1204 107')
                    command('D 2')
                    command('E 7')
                    command(f'M 000000000009f120 {packet1.hex()}')
                    command('D 1')
                    command('S 100000')
                    assert report(30) == (0x35514552 if packet5 else
                                          0x34514552 if packet4 else
                                          0x33514552 if packet3 else 0x32514552)
                    assert report(31) == 1 and report(32) == 1
                    assert report(29) == 2 and output(512) == reply1
                    assert command('I 1318') == 0x7f
                    assert command('I 131c') == 0xfffffe00
                    assert command('I 132c') == 1
                    command('A 1')
                    command('D 2')
                    command(f'M 000000000009f120 {packet2.hex()}')
                    command('D 1')
                    command('S 100000')
                    if args.corrupt_second_length:
                        assert report(21) == 0x102 and report(31) == 1
                        assert command('I 132c') == 0
                        assert raw('U 0009f3e0') == b'ERR'
                        seq = report(16)
                        command('S 100000')
                        assert report(16) == seq and report(31) == 1
                        final_state = 'rejected'
                        reply_sha = None
                    else:
                        assert report(21) == 2 and report(31) == 2
                        assert report(32) == 0x11 and report(29) == 2
                        actual = output(128)
                        assert actual == reply2
                        assert command('I 1318') == 0x7f
                        assert command('I 131c') == 0
                        assert command('I 132c') == 1
                        final_state = 'completed'
                        reply_sha = hashlib.sha256(actual).hexdigest()
                    third_state = third_reply_sha = None
                    if packet3:
                        command('A 1')
                        command('D 2')
                        command(f'M 000000000009f120 {packet3.hex()}')
                        command('D 1')
                        command('S 100000')
                        if args.corrupt_third_length:
                            assert report(21) == 0x102 and report(31) == 2
                            assert command('I 132c') == 0
                            assert raw('U 0009f3e0') == b'ERR'
                            seq = report(16)
                            command('S 100000')
                            assert report(16) == seq and report(31) == 2
                            third_state = 'rejected'
                        else:
                            assert report(21) == 2 and report(31) == 3
                            assert report(32) == 0x15 and report(29) == 2
                            actual3 = output(64)
                            assert actual3 == reply3
                            assert command('I 1318') == 0x7f
                            assert command('I 131c') == 0
                            assert command('I 132c') == 1
                            third_state = 'completed'
                            third_reply_sha = hashlib.sha256(actual3).hexdigest()
                    fourth_state = fourth_reply_sha = None
                    if packet4:
                        command('A 1')
                        command('D 2')
                        command(f'M 000000000009f120 {packet4.hex()}')
                        command('D 1')
                        command('S 100000')
                        if args.corrupt_fourth_length:
                            assert report(21) == 0x102 and report(31) == 3
                            assert command('I 132c') == 0
                            assert raw('U 0009f3e0') == b'ERR'
                            seq = report(16)
                            command('S 100000')
                            assert report(16) == seq and report(31) == 3
                            fourth_state = 'rejected'
                        else:
                            assert report(21) == 2 and report(31) == 4
                            assert report(32) == 0xd0 and report(29) == 2
                            actual4 = output(128)
                            assert actual4 == reply4
                            assert command('I 1318') == 0x7f
                            assert command('I 131c') == 0
                            assert command('I 132c') == 1
                            fourth_state = 'completed'
                            fourth_reply_sha = hashlib.sha256(actual4).hexdigest()
                    fifth_state = fifth_reply_sha = None
                    if packet5:
                        command('A 1')
                        command('D 2')
                        command(f'M 000000000009f120 {packet5.hex()}')
                        command('D 1')
                        command('S 100000')
                        if args.corrupt_fifth_length:
                            assert report(21) == 0x102 and report(31) == 4
                            assert command('I 132c') == 0
                            assert raw('U 0009f3e0') == b'ERR'
                            seq = report(16)
                            command('S 100000')
                            assert report(16) == seq and report(31) == 4
                            fifth_state = 'rejected'
                        else:
                            assert report(21) == 2 and report(31) == 5
                            assert report(32) == 0x2d and report(29) == 2
                            actual5 = output(512)
                            assert actual5 == reply5
                            assert command('I 1318') == 0x7f
                            assert command('I 131c') == 0
                            assert command('I 132c') == 1
                            fifth_state = 'completed'
                            fifth_reply_sha = hashlib.sha256(actual5).hexdigest()
                    wire.close()
            finally:
                process.terminate()
                process.wait(timeout=5)
    result = {
        'gate': 'PASS', 'second_state': final_state,
        'second_reply_sha256': reply_sha,
        'second_request_sha256': hashlib.sha256(packet2).hexdigest(),
        'third_state': third_state,
        'third_reply_sha256': third_reply_sha,
        'third_request_sha256': hashlib.sha256(packet3).hexdigest()
        if packet3 else None,
        'fourth_state': fourth_state,
        'fourth_reply_sha256': fourth_reply_sha,
        'fourth_request_sha256': hashlib.sha256(packet4).hexdigest()
        if packet4 else None,
        'fifth_state': fifth_state,
        'fifth_reply_sha256': fifth_reply_sha,
        'fifth_request_sha256': hashlib.sha256(packet5).hexdigest()
        if packet5 else None,
        'image_sha256': hashlib.sha256(args.image.read_bytes()).hexdigest(),
        'scope': 'exploratory i960 emulator and bounded host DMA model',
        'physical_card_tested': False, 'safe_to_flash': False,
    }
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('native_rom_sequence=' +
          (fifth_state.upper() if fifth_state else
           fourth_state.upper() if fourth_state else
           third_state.upper() if third_state else final_state.upper()))


if __name__ == '__main__':
    main()

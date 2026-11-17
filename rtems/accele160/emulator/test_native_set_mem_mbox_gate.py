#!/usr/bin/env python3
"""Check bounded native mailbox setup and optional first ring completion."""
import argparse
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / 'artifacts/current'


def captured_request(directory, fixture):
    record = json.loads((directory / fixture).read_text())
    packet = (directory / record['request_file']).read_bytes()
    assert hashlib.sha256(packet).hexdigest() == record['request_sha256']
    assert len(packet) == 64
    return packet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--emulator', type=Path, required=True)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--sixth-request', type=Path, required=True)
    parser.add_argument('--sixth-dma', type=lambda value: int(value, 0),
                        default=0x06197000)
    parser.add_argument('--corrupt-control', action='store_true')
    parser.add_argument('--ring-slot', type=Path,
                        help='stage one 64-byte guest ring command for read-only observation')
    parser.add_argument('--corrupt-ring-control', action='store_true')
    parser.add_argument('--ring-reply', action='store_true',
                        help='require one observed 1004-byte output and status completion')
    parser.add_argument('--followup-slot1', type=Path)
    parser.add_argument('--followup-slot2', type=Path)
    parser.add_argument('--corrupt-followup2-control', action='store_true')
    parser.add_argument('--corrupt-followup1-control', action='store_true')
    parser.add_argument('--health-reply', action='store_true',
                        help='require exact 128-byte native health DMA and second status')
    parser.add_argument('--pdev-reply', action='store_true',
                        help='require exact 512-byte native target-0 pdev DMA and third status')
    parser.add_argument('--next-slot3', type=Path)
    parser.add_argument('--next-slot4', type=Path)
    parser.add_argument('--corrupt-next4-control', action='store_true')
    parser.add_argument('--corrupt-next3-control', action='store_true')
    parser.add_argument('--zero-next4-id', action='store_true')
    parser.add_argument('--repeat-info-reply', action='store_true',
                        help='require observed slot-3 controller-info repeat completion')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.corrupt_ring_control and not args.ring_slot:
        parser.error('--corrupt-ring-control requires --ring-slot')
    if args.ring_slot and args.corrupt_control:
        parser.error('ring observation requires valid SET_MEM_MBOX setup')
    if args.ring_reply and not args.ring_slot:
        parser.error('--ring-reply requires --ring-slot')
    if bool(args.followup_slot1) != bool(args.followup_slot2):
        parser.error('both follow-up slots are required')
    if args.followup_slot1 and not args.ring_reply:
        parser.error('follow-up observation requires --ring-reply')
    if args.corrupt_followup2_control and not args.followup_slot2:
        parser.error('corrupt follow-up requires both slots')
    if args.corrupt_followup1_control and not args.followup_slot1:
        parser.error('corrupt follow-up requires both slots')
    if args.health_reply and not args.followup_slot1:
        parser.error('--health-reply requires both follow-up slots')
    if args.pdev_reply and not args.health_reply:
        parser.error('--pdev-reply requires --health-reply')
    if bool(args.next_slot3) != bool(args.next_slot4):
        parser.error('both next slots are required')
    if args.next_slot3 and not args.pdev_reply:
        parser.error('next-slot observation requires --pdev-reply')
    if args.corrupt_next4_control and not args.next_slot4:
        parser.error('corrupt next slot requires --next-slot4')
    if args.corrupt_next3_control and not args.next_slot3:
        parser.error('corrupt next slot requires --next-slot3')
    if args.zero_next4_id and not args.next_slot4:
        parser.error('zero next ID requires --next-slot4')
    if args.repeat_info_reply and not args.next_slot3:
        parser.error('--repeat-info-reply requires both next slots')
    if args.output.exists():
        raise FileExistsError(args.output)
    first = json.loads((ART / 'accele160-offline-build-20261115/first-controller-info-fixture.json').read_text())
    packets = [bytes.fromhex(first['request']['mailbox_hex'])]
    base = ART / 'accele160-stock-ioctl11-20261116'
    packets.extend(captured_request(base, name) for name in
                   ('ioctl11-fixture.json', 'ioctl15-fixture.json',
                    'ioctld0-fixture.json'))
    packets.append(captured_request(ART / 'accele160-stock-ioctl2d-20261116',
                                    'ioctl2d-fixture.json'))
    sixth = bytearray(args.sixth_request.read_bytes())
    assert len(sixth) == 64 and sixth[21] == 0x8e
    expected_health = int.from_bytes(sixth[24:28], 'little')
    expected_command = int.from_bytes(sixth[32:36], 'little')
    expected_status = int.from_bytes(sixth[40:44], 'little')
    sixth_sha = hashlib.sha256(sixth).hexdigest()
    if args.corrupt_control:
        sixth[3] = 0x10
    ring_slot = None
    ring_digest = None
    if args.ring_slot:
        ring_slot = bytearray(args.ring_slot.read_bytes())
        assert len(ring_slot) == 64
        if args.corrupt_ring_control:
            ring_slot[3] = 0x10
        ring_digest = 2166136261
        for byte in ring_slot:
            ring_digest = ((ring_digest ^ byte) * 16777619) & 0xffffffff
    expected_output = (ART / 'accele160-stock-ring-dma1-completion-20261116/'
                       'model-first-output-1004.bin').read_bytes() if args.ring_reply else None
    expected_status_bytes = (ART / 'accele160-stock-ring-dma1-completion-20261116/'
                             'model-first-status-8.bin').read_bytes() if args.ring_reply else None
    followup = []
    if args.followup_slot1:
        for path in (args.followup_slot1, args.followup_slot2):
            data = bytearray(path.read_bytes())
            assert len(data) == 64
            followup.append(data)
        if args.corrupt_followup1_control:
            followup[0][3] = 0x10
        if args.corrupt_followup2_control:
            followup[1][3] = 0x10
    expected_health_bytes = (ART / 'accele160-stock-followup-source-20261116/'
                             'stock-health-source-128.bin').read_bytes() if args.health_reply else None
    expected_pdev_bytes = (ART / 'accele160-stock-followup-pdev-source-20261116/'
                           'stock-pdev-source-512.bin').read_bytes() if args.pdev_reply else None
    next_slots = []
    if args.next_slot3:
        for path in (args.next_slot3, args.next_slot4):
            data = bytearray(path.read_bytes())
            assert len(data) == 64
            next_slots.append(data)
        if args.corrupt_next3_control:
            next_slots[0][3] ^= 0x40
        if args.corrupt_next4_control:
            next_slots[1][3] ^= 0x40
        if args.zero_next4_id:
            next_slots[1][0:2] = b'\0\0'
    with tempfile.TemporaryDirectory(prefix='accele160-native-set-mbox-') as tmp:
        bridge = Path(tmp) / 'bridge.sock'
        with args.output.with_suffix('.emu.log').open('w') as log:
            command = [str(args.emulator.resolve()), str(args.image.resolve()),
                       '3000000', '--board-id=11', '--quiet-trace',
                       f'--bridge-socket={bridge}']
            if args.ring_reply:
                command.append('--explore-native-ring-dma1')
            if args.health_reply:
                command.append('--explore-native-ring-health-dma1')
            if args.pdev_reply:
                command.append('--explore-native-ring-pdev-dma1')
            process = subprocess.Popen(command, stdout=log,
                stderr=subprocess.STDOUT)
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

                    def cmd(line):
                        result = raw(line)
                        if len(result) != 8 or result == b'ERR':
                            raise AssertionError(f'{line}: {result!r}')
                        return int(result, 16)

                    def report(index):
                        return cmd(f'R {0xc0001f00 + 4 * index:08x} 4 0')

                    assert report(7) == 0x50415353
                    assert report(30) == 0x36514552
                    cmd('H 1004 107')
                    cmd('H 1204 107')
                    cmd('D 2')
                    cmd('E 7')
                    for index, packet in enumerate(packets, 1):
                        cmd(f'M 000000000009f120 {packet.hex()}')
                        cmd('D 1')
                        cmd('S 100000')
                        assert report(31) == index and report(21) == 2
                        assert cmd('I 1318') == 0x7f
                        assert cmd('I 132c') == 1
                        cmd('A 1')
                        cmd('D 2')
                    assert report(31) == 5
                    cmd(f'M {args.sixth_dma:016x} {sixth.hex()}')
                    cmd('D 1')
                    cmd('S 100000')
                    if args.corrupt_control:
                        assert report(21) == 0x102 and report(31) == 5
                        assert cmd('I 132c') == 0
                        assert report(33) == 0 and report(34) == 0 and report(35) == 0
                        sequence = report(16)
                        cmd('S 100000')
                        assert report(16) == sequence and report(31) == 5
                        state = 'rejected'
                    else:
                        assert report(21) == 2 and report(26) == 2
                        assert report(29) == 3 and report(31) == 6
                        assert report(32) == 0x8e
                        assert cmd('I 1318') == 1 and cmd('I 131c') == 0x420
                        assert cmd('I 132c') == 1
                        assert report(33) == expected_command
                        assert report(34) == expected_status
                        assert report(35) == expected_health
                        state = 'completed'
                    if ring_slot is not None:
                        assert report(36) == 0x31474e52 and report(37) == 0
                        cmd('A 1')
                        cmd(f'N {expected_command:016x} {ring_slot.hex()}')
                        if args.ring_reply:
                            cmd(f'G S {expected_status:016x} {40 if args.repeat_info_reply else 32 if next_slots else 24 if args.health_reply else 8}')
                            cmd(f'G H {expected_health:016x} 128')
                            output_bus = int.from_bytes(ring_slot[32:36], 'little')
                            cmd(f'G O {output_bus:016x} 1004')
                        cmd('D 10')
                        cmd('S 100000')
                        assert report(37) == (0x102 if args.corrupt_ring_control
                                              else 3 if args.ring_reply else 2)
                        assert report(38) == ring_digest
                        assert report(39) == expected_command + (
                            64 if args.ring_reply and not args.corrupt_ring_control else 0)
                        assert report(43) == 0x10
                        assert report(44) == (1 if args.ring_reply and
                                              not args.corrupt_ring_control else 0)
                        assert report(31) == 6
                        after = b''.join(
                            cmd(f'R {expected_command + i * 4:08x} 4 0').to_bytes(4, 'little')
                            for i in range(16))
                        if args.corrupt_ring_control:
                            assert after == ring_slot and cmd('I 132c') == 0
                            assert report(40) == 0 and report(41) == 0 and report(42) == 0
                            if args.ring_reply:
                                assert all(cmd(f'R {expected_status + i * 4:08x} 4 0') == 0
                                           for i in range(2))
                                assert all(cmd(f'R {output_bus + i * 4:08x} 4 0') == 0
                                           for i in range(251))
                        else:
                            assert report(40) == int.from_bytes(ring_slot[32:36], 'little')
                            assert report(41) == 1004 and report(42) == 1
                            if args.ring_reply:
                                assert after[:4] == b'\0' * 4 and after[4:] == ring_slot[4:]
                                assert cmd('I 132c') == 2
                                assert report(46) == 2 and report(47) == 1
                                assert report(48) == 0xffffffec
                                actual_output = b''.join(
                                    cmd(f'R {output_bus + i * 4:08x} 4 0').to_bytes(4, 'little')
                                    for i in range(251))
                                actual_status = b''.join(
                                    cmd(f'R {expected_status + i * 4:08x} 4 0').to_bytes(4, 'little')
                                    for i in range(2))
                                assert actual_output == expected_output
                                assert actual_status == expected_status_bytes
                            else:
                                assert after == ring_slot and cmd('I 132c') == 0
                        state = ('observed-invalid' if args.corrupt_ring_control else
                                 'completed-ring' if args.ring_reply else 'observed')
                    if followup:
                        assert state == 'completed-ring'
                        cmd('A 2')
                        for index, data in enumerate(followup, 1):
                            address = expected_command + index * 64
                            cmd(f'N {address:016x} {data.hex()}')
                            if index == 2 and args.pdev_reply:
                                pdev_output = int.from_bytes(data[32:36], 'little')
                                cmd(f'G P {pdev_output:016x} 512')
                            cmd('D 10')
                            cmd('S 100000')
                            digest = 2166136261
                            for byte in data:
                                digest = ((digest ^ byte) * 16777619) & 0xffffffff
                            assert report(49) == 0x32474e52
                            assert report(50) == index and report(51) == index
                            assert report(52) == address and report(53) == digest
                            valid = (index == 1 and not args.corrupt_followup1_control or
                                     index == 2 and not args.corrupt_followup2_control)
                            assert report(54) == (2 if valid else 0x102)
                            if valid:
                                assert report(55) == (2 if index == 1 else 1)
                                assert report(56) == (0x11 if index == 1 else 0x05)
                                assert report(57) == int.from_bytes(data[32:36], 'little')
                                assert report(58) == (128 if index == 1 else 512)
                            health_completed = args.health_reply and not args.corrupt_followup1_control
                            pdev_completed = (args.pdev_reply and index == 2 and
                                              health_completed and not args.corrupt_followup2_control)
                            completions = 3 if pdev_completed else 2 if health_completed else 1
                            assert report(59) == expected_status + completions * 8
                            assert report(60) == completions and report(44) == completions
                            assert report(39) == expected_command + completions * 64
                            if args.health_reply:
                                if index == 2 and args.pdev_reply:
                                    assert report(61) == (3 if pdev_completed else 0)
                                    assert report(62) == (2 if pdev_completed else 0)
                                    assert report(63) == (1 if pdev_completed else 0)
                                else:
                                    assert report(61) == (3 if health_completed else 0)
                                    assert report(62) == (2 if health_completed else 0)
                                    assert report(63) == (2 if health_completed else 0)
                            assert cmd('I 1320') & 0x10 == 0
                            assert cmd('I 132c') == (2 if (index == 1 and health_completed or
                                                            pdev_completed) else 0)
                            after_followup = b''.join(
                                cmd(f'R {address + i * 4:08x} 4 0').to_bytes(4, 'little')
                                for i in range(16))
                            if (index == 1 and health_completed) or pdev_completed:
                                assert after_followup[:4] == b'\0' * 4
                                assert after_followup[4:] == data[4:]
                            else:
                                assert after_followup == data
                            assert b''.join(
                                cmd(f'R {expected_status + i * 4:08x} 4 0').to_bytes(4, 'little')
                                for i in range(2)) == expected_status_bytes
                            assert b''.join(
                                cmd(f'R {output_bus + i * 4:08x} 4 0').to_bytes(4, 'little')
                                for i in range(251)) == expected_output
                            if args.health_reply:
                                actual_health = b''.join(
                                    cmd(f'R {expected_health + i * 4:08x} 4 0').to_bytes(4, 'little')
                                    for i in range(32))
                                status_second = b''.join(
                                    cmd(f'R {expected_status + 8 + i * 4:08x} 4 0').to_bytes(4, 'little')
                                    for i in range(2))
                                assert actual_health == (expected_health_bytes if health_completed else b'\0' * 128)
                                assert status_second == (b'\x02' + b'\0' * 7 if health_completed else b'\0' * 8)
                            if index == 2 and args.pdev_reply:
                                actual_pdev = b''.join(
                                    cmd(f'R {pdev_output + i * 4:08x} 4 0').to_bytes(4, 'little')
                                    for i in range(128))
                                status_third = b''.join(
                                    cmd(f'R {expected_status + 16 + i * 4:08x} 4 0').to_bytes(4, 'little')
                                    for i in range(2))
                                assert actual_pdev == (expected_pdev_bytes if pdev_completed else b'\0' * 512)
                                assert status_third == (b'\x01' + b'\0' * 7 if pdev_completed else b'\0' * 8)
                            if index == 1 and health_completed:
                                cmd('A 2')
                        state = ('observed-followup-invalid' if args.corrupt_followup2_control
                                 else 'observed-followups')
                    if next_slots:
                        assert state == 'observed-followups'
                        assert report(60) == 3 and report(39) == expected_command + 192
                        cmd('A 2')
                        for index, data in enumerate(next_slots, 3):
                            address = expected_command + index * 64
                            cmd(f'N {address:016x} {data.hex()}')
                            if index == 3 and args.repeat_info_reply:
                                cmd(f'G T {int.from_bytes(data[32:36], "little"):016x} 1004')
                            cmd('D 10')
                            cmd('S 100000')
                            digest = 2166136261
                            for byte in data:
                                digest = ((digest ^ byte) * 16777619) & 0xffffffff
                            assert report(50) == index and report(51) == index
                            assert report(52) == address and report(53) == digest
                            invalid = (index == 3 and args.corrupt_next3_control or
                                       index == 4 and (args.corrupt_next4_control or
                                                       args.zero_next4_id))
                            assert report(54) == (0x102 if invalid else 2)
                            if not invalid:
                                assert report(55) == (1 if index == 3 else
                                                      int.from_bytes(data[:2], 'little'))
                                assert report(56) == (1 if index == 3 else 2)
                                assert report(57) == int.from_bytes(data[32:36], 'little')
                                assert report(58) == (1004 if index == 3 else 36)
                            repeat_completed = args.repeat_info_reply and not args.corrupt_next3_control
                            completed = 4 if repeat_completed else 3
                            assert (report(60), report(44)) == (completed, completed), (
                                index, report(54), report(61), report(62),
                                report(39), report(60), report(44))
                            assert report(39) == expected_command + completed * 64
                            assert report(59) == expected_status + completed * 8
                            assert cmd('I 1320') & 0x10 == 0
                            assert cmd('I 132c') == (2 if index == 3 and repeat_completed else 0)
                            after_next = b''.join(
                                cmd(f'R {address + i * 4:08x} 4 0').to_bytes(4, 'little')
                                for i in range(16))
                            assert after_next == (b'\0' * 4 + data[4:] if
                                                  index == 3 and repeat_completed else data)
                            status_next = b''.join(
                                cmd(f'R {expected_status + 24 + i * 4:08x} 4 0').to_bytes(4, 'little')
                                for i in range(2))
                            assert status_next == (expected_status_bytes if
                                                   repeat_completed else b'\0' * 8)
                            if index == 3 and repeat_completed:
                                output_next = int.from_bytes(data[32:36], 'little')
                                actual_repeat = b''.join(
                                    cmd(f'R {output_next + i * 4:08x} 4 0').to_bytes(4, 'little')
                                    for i in range(251))
                                assert actual_repeat == expected_output
                                assert report(61) == 3 and report(62) == 2 and report(63) == 1
                                cmd('A 2')
                            if index == 4:
                                if args.repeat_info_reply:
                                    assert all(cmd(f'R {expected_status + 32 + i * 4:08x} 4 0') == 0
                                               for i in range(2))
                        state = ('observed-next-invalid' if
                                 args.corrupt_next3_control or args.corrupt_next4_control
                                 or args.zero_next4_id
                                 else 'observed-next')
                    wire.close()
            finally:
                process.terminate()
                process.wait(timeout=5)
    result = {'gate': 'PASS', 'sixth_state': state,
              'sixth_request_sha256': sixth_sha,
              'sixth_mailbox_dma': args.sixth_dma,
              'ring_slot_sha256': hashlib.sha256(ring_slot).hexdigest()
              if ring_slot is not None else None,
              'ring_digest_fnv1a32': ring_digest,
              'image_sha256': hashlib.sha256(args.image.read_bytes()).hexdigest(),
              'scope': ('exploratory i960 model first three ring replies; no guest mirror'
                        if args.pdev_reply else
                        'exploratory i960 model controller and health replies; no guest mirror'
                        if args.health_reply else
                        'exploratory i960 model first ring reply; no guest mirror'
                        if args.ring_reply else
                        'exploratory i960 emulator mailbox/ring observation'),
              'physical_card_tested': False, 'safe_to_flash': False}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('native_set_mem_mbox=' + state.upper())


if __name__ == '__main__':
    main()

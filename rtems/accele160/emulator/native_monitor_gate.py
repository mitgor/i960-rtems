#!/usr/bin/env python3
"""Exercise the opt-in native read-only host monitor against explicit inputs."""
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
    parser.add_argument('--mailbox-fixture', type=Path, required=True)
    parser.add_argument('--mailbox-dma', type=lambda value: int(value, 0),
                        default=0x9f120)
    parser.add_argument('--corrupt-opcode', action='store_true')
    parser.add_argument('--corrupt-output-address', action='store_true')
    parser.add_argument('--wrong-output-address', action='store_true',
                        help='well-formed but outside the one captured ROM destination')
    parser.add_argument('--expect-ingress', action='store_true')
    parser.add_argument('--expect-reply', type=Path,
                        help='captured 512-byte stock reply; checks local composition only')
    parser.add_argument('--reply-local-address', type=lambda value: int(value, 0),
                        help='i960 symbol address of the composed 512-byte local buffer')
    parser.add_argument('--expect-dma', action='store_true',
                        help='enable the exploratory DMA1 model and verify output/completion')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if sum((args.corrupt_opcode, args.corrupt_output_address,
            args.wrong_output_address)) > 1:
        parser.error('choose one mailbox modification')
    if args.expect_reply and not args.expect_ingress:
        parser.error('--expect-reply requires --expect-ingress')
    if args.reply_local_address is not None and (not args.expect_reply or
                                                  args.reply_local_address & 3):
        parser.error('--reply-local-address requires --expect-reply and 4-byte alignment')
    if args.expect_dma and not args.expect_reply:
        parser.error('--expect-dma requires --expect-reply')
    if args.output.exists():
        raise FileExistsError(args.output)
    fixture = json.loads(args.mailbox_fixture.read_text())
    packet = bytes.fromhex(fixture['request']['mailbox_hex'])
    if len(packet) != 64 or hashlib.sha256(packet).hexdigest() != fixture['request']['mailbox_sha256']:
        raise ValueError('invalid saved ROM mailbox fixture')
    reply = args.expect_reply.read_bytes() if args.expect_reply else None
    if reply is not None and (len(reply) != 512 or
                              hashlib.sha256(reply).hexdigest() != fixture['response_sha256']):
        raise ValueError('reply fixture differs from saved stock replay')
    if args.corrupt_opcode or args.corrupt_output_address or args.wrong_output_address:
        packet = bytearray(packet)
        if args.corrupt_opcode:
            packet[2] = 0
        elif args.corrupt_output_address:
            packet[32] |= 1
        else:
            packet[32:36] = (0x9f7e0).to_bytes(4, 'little')
        packet = bytes(packet)
    local_reply_sha256 = None
    dma_output_sha256 = None
    with tempfile.TemporaryDirectory(prefix='accele160-native-monitor-') as temp:
        bridge = Path(temp) / 'bridge.sock'
        log = args.output.with_suffix('.emu.log')
        with log.open('w') as stream:
            process = subprocess.Popen(
                [str(args.emulator.resolve()), str(args.image.resolve()),
                 '3000000', '--board-id=11', '--quiet-trace',
                 f'--bridge-socket={bridge}'],
                stdout=stream, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 30
                while not bridge.exists():
                    if process.poll() is not None:
                        raise RuntimeError('native emulator exited before bridge')
                    if time.monotonic() > deadline:
                        raise TimeoutError('native emulator did not reach bridge')
                    time.sleep(0.05)
                with socket.socket(socket.AF_UNIX) as connection:
                    connection.connect(str(bridge))
                    wire = connection.makefile('rwb', buffering=0)

                    def command(line):
                        wire.write((line + '\n').encode('ascii'))
                        answer = wire.readline().strip()
                        if len(answer) != 8 or answer == b'ERR':
                            raise RuntimeError(f'{line}: {answer!r}')
                        return int(answer, 16)

                    def snapshot():
                        count = 30 if args.expect_dma else 28 if reply is not None else 25
                        words = [command(f'R {0xc0001f00 + i * 4:08x} 4 0')
                                 for i in range(count)]
                        if words[0] != 0x32544753 or words[7] != 0x50415353 or words[9] != 0x30545348:
                            raise AssertionError('native PASS/HST0 report missing')
                        if words[19] != 0x31545348 or words[16] & 1:
                            raise AssertionError('stable HST1 report missing')
                        if args.expect_ingress and words[20] != 0x3058424d:
                            raise AssertionError('MBX0 ingress report missing')
                        if reply is not None and words[25] != 0x304c5052:
                            raise AssertionError('RPL0 local reply report missing')
                        if args.expect_dma and words[28] != 0x31414d44:
                            raise AssertionError('DMA1 diagnostic report missing')
                        return {'bridge': words[10], 'raid': words[11],
                                'doorbell': words[12], 'status': words[13],
                                'mask': words[14], 'ready': words[15],
                                'sequence': words[16],
                                'mailbox_pointer': (words[18] << 32) | words[17],
                                'ingress_state': words[21] if args.expect_ingress else None,
                                'command_id': words[22] if args.expect_ingress else None,
                                'output_bus': words[23] if args.expect_ingress else None,
                                'request_fnv32': words[24] if args.expect_ingress else None,
                                'reply_state': words[26] if reply is not None else None,
                                'reply_fnv32': words[27] if reply is not None else None,
                                'dma_state': words[29] if args.expect_dma else None}

                    def step():
                        command('S 100000')

                    samples = {}
                    samples['reset'] = snapshot()
                    if samples['reset']['ready'] != 0 or samples['reset']['mask'] != 0xffffffff:
                        raise AssertionError('unexpected readiness before host writes')
                    command('H 1004 107')
                    step()
                    samples['bridge_only'] = snapshot()
                    if samples['bridge_only']['ready'] != 1:
                        raise AssertionError('bridge-only readiness not 1')
                    command('H 1204 107')
                    step()
                    samples['both_pci'] = snapshot()
                    if samples['both_pci']['ready'] != 3:
                        raise AssertionError('PCI readiness not 3')
                    command('D 2')
                    step()
                    samples['boot_doorbell'] = snapshot()
                    if samples['boot_doorbell']['ready'] != 7:
                        raise AssertionError('boot doorbell readiness not 7')
                    if args.expect_dma:
                        command('E 7')  # opt-in bounded DMA1 model
                    command(f'M {args.mailbox_dma:016x} {packet.hex()}')
                    command('D 1')
                    step()
                    samples['first_request'] = snapshot()
                    expected_complete = args.expect_dma and not (
                        args.corrupt_opcode or args.corrupt_output_address or
                        args.wrong_output_address or args.mailbox_dma != 0x9f120)
                    expected_doorbell = 0 if expected_complete else 3
                    expected_status = 3 if expected_complete else 7
                    if (samples['first_request']['doorbell'] != expected_doorbell or
                            samples['first_request']['status'] != expected_status or
                            samples['first_request']['mailbox_pointer'] != args.mailbox_dma):
                        raise AssertionError('first mailbox transition not visible')
                    if samples['first_request']['mask'] != 0xffffffff:
                        raise AssertionError('read-only monitor changed MU mask')
                    ordered = [samples[name] for name in (
                        'reset', 'bridge_only', 'both_pci',
                        'boot_doorbell', 'first_request')]
                    if not all(a['sequence'] < b['sequence'] and
                               a['sequence'] % 2 == b['sequence'] % 2 == 0
                               for a, b in zip(ordered, ordered[1:])):
                        raise AssertionError('HST1 sequence did not advance cleanly')
                    if any(s['mailbox_pointer'] for s in ordered[:-1]):
                        raise AssertionError('mailbox pointer appeared before submission')
                    if args.expect_ingress:
                        expected_state = (0x200 if args.mailbox_dma != 0x9f120
                                          else 0x102 if args.corrupt_opcode
                                          else 0x103 if args.corrupt_output_address
                                          else 2)
                        final = samples['first_request']
                        if final['ingress_state'] != expected_state:
                            raise AssertionError(f'ingress state {final["ingress_state"]:#x} '
                                                 f'!= {expected_state:#x}')
                        if expected_state == 2 and (final['command_id'] != 0x7f or
                                                    final['output_bus'] !=
                                                    (0x9f7e0 if args.wrong_output_address
                                                     else 0x9f3e0)):
                            raise AssertionError('accepted mailbox fields differ')
                        if expected_state != 2 and (final['command_id'] or
                                                    final['output_bus']):
                            raise AssertionError('rejected mailbox exposed parsed fields')
                        expected_digest = 0
                        if args.mailbox_dma == 0x9f120:
                            expected_digest = 2166136261
                            for byte in packet:
                                expected_digest = ((expected_digest ^ byte) *
                                                   16777619) & 0xffffffff
                        if final['request_fnv32'] != expected_digest:
                            raise AssertionError('firmware read unexpected mailbox bytes')
                    if reply is not None:
                        expected_reply_state = 2 if samples['first_request']['ingress_state'] == 2 else 0
                        final = samples['first_request']
                        if final['reply_state'] != expected_reply_state:
                            raise AssertionError('local reply composition state differs')
                        expected_reply_digest = 0
                        if expected_reply_state == 2:
                            expected_reply_digest = 2166136261
                            for byte in reply:
                                expected_reply_digest = ((expected_reply_digest ^ byte) *
                                                         16777619) & 0xffffffff
                        if final['reply_fnv32'] != expected_reply_digest:
                            raise AssertionError('local reply digest differs from stock replay')
                        if args.expect_dma:
                            expected_dma_state = (2 if expected_complete else
                                                  0x101 if args.wrong_output_address else 0)
                            if final['dma_state'] != expected_dma_state:
                                raise AssertionError(f'DMA state {final["dma_state"]:#x} '
                                                     f'!= {expected_dma_state:#x}')
                            if expected_complete:
                                output = b''.join(command(
                                    f'U {0x9f3e0 + i * 4:08x}'
                                ).to_bytes(4, 'little') for i in range(128))
                                if output != reply:
                                    raise AssertionError('DMA1 host output differs from stock reply')
                                dma_output_sha256 = hashlib.sha256(output).hexdigest()
                                if (command('I 1318') != 0x7f or
                                        command('I 131c') != 0xfffffe00 or
                                        command('I 132c') != 1):
                                    raise AssertionError('outbound MU completion differs')
                            else:
                                if command('I 132c') != 0:
                                    raise AssertionError('rejected request published outbound doorbell')
                                wire.write(b'U 0009f3e0\n')
                                if wire.readline().strip() != b'ERR':
                                    raise AssertionError('rejected request exposed DMA output')
                        if expected_reply_state == 2 and args.reply_local_address is not None:
                            local = b''.join(command(
                                f'R {args.reply_local_address + i * 4:08x} 4 0'
                            ).to_bytes(4, 'little') for i in range(128))
                            if local != reply:
                                mismatch = next(i for i in range(512) if local[i] != reply[i])
                                raise AssertionError(f'local reply differs at byte {mismatch:#x}')
                            local_reply_sha256 = hashlib.sha256(local).hexdigest()
                    wire.close()
            finally:
                process.terminate()
                process.wait(timeout=5)
    result = {'gate': 'PASS', 'scope': 'offline i960 model with explicit host writes',
              'image_sha256': hashlib.sha256(args.image.read_bytes()).hexdigest(),
              'mailbox_sha256': fixture['request']['mailbox_sha256'],
              'staged_mailbox_sha256': hashlib.sha256(packet).hexdigest(),
              'local_reply_sha256': local_reply_sha256,
              'dma_output_sha256': dma_output_sha256,
              'samples': samples, 'emulator_log': log.name,
              'model_limits': ['exploratory reset selector 11',
                               'host PCI and doorbell writes injected through local bridge',
                               'host mailbox bytes supplied by emulator backing',
                               ('DMA1 output and MU completion use exploratory model'
                                if args.expect_dma else 'no output DMA or command completion')]}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('native_host_monitor=PASS reset->bridge->PCI->doorbell->mailbox')


if __name__ == '__main__':
    main()

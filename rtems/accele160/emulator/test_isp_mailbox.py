#!/usr/bin/env python3
"""Check the opt-in ISP register, word RAM, and bounded DMA mailbox model."""
import argparse
from pathlib import Path
import socket
import struct
import subprocess
import tempfile
import time


ROOT = Path(__file__).parent
BASE = 0x8bf00000


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-ack', action='store_true',
                        help='also check that the execute stub rejects an incomplete image')
    parser.add_argument('--about-ack', action='store_true',
                        help='also check that ABOUT is held before execution')
    parser.add_argument('--queue-ack', action='store_true',
                        help='also check that queue setup is held before firmware setup')
    parser.add_argument('--retry-ack', action='store_true',
                        help='also check that retry setup is held before queues exist')
    parser.add_argument('--reset-delay-ack', action='store_true',
                        help='also check that reset delay is held before retry setup')
    parser.add_argument('--active-negation-ack', action='store_true',
                        help='also check that active negation is held before reset delay')
    parser.add_argument('--feature-ack', action='store_true',
                        help='also check that feature setup is held before active negation')
    parser.add_argument('--status-zero', action='store_true',
                        help='also check that status is held before feature setup')
    parser.add_argument('--init-id-ack', action='store_true',
                        help='also check that initiator ID is held before status')
    parser.add_argument('--bus-reset-ack', action='store_true',
                        help='also check that bus reset is held before initiator ID')
    parser.add_argument('--target0-ack', action='store_true',
                        help='also check that target setup is held before bus reset')
    args = parser.parse_args()
    if args.about_ack and not args.execute_ack:
        parser.error('--about-ack requires --execute-ack')
    if args.queue_ack and not args.about_ack:
        parser.error('--queue-ack requires --about-ack')
    if args.retry_ack and not args.queue_ack:
        parser.error('--retry-ack requires --queue-ack')
    if args.reset_delay_ack and not args.retry_ack:
        parser.error('--reset-delay-ack requires --retry-ack')
    if args.active_negation_ack and not args.reset_delay_ack:
        parser.error('--active-negation-ack requires --reset-delay-ack')
    if args.feature_ack and not args.active_negation_ack:
        parser.error('--feature-ack requires --active-negation-ack')
    if args.status_zero and not args.feature_ack:
        parser.error('--status-zero requires --feature-ack')
    if args.init_id_ack and not args.status_zero:
        parser.error('--init-id-ack requires --status-zero')
    if args.bus_reset_ack and not args.init_id_ack:
        parser.error('--bus-reset-ack requires --init-id-ack')
    if args.target0_ack and not args.bus_reset_ack:
        parser.error('--target0-ack requires --bus-reset-ack')
    image = bytearray(0x100000)
    probe = (ROOT / 'isa_probe.bin').read_bytes()
    image[0xf0000:0xf0000 + len(probe)] = probe
    entry, prcb = 0xfeff0000, 0xfeffdd20
    struct.pack_into('<III', image, 0xfff40, entry, prcb,
                     (-entry - prcb) & 0xffffffff)
    with tempfile.TemporaryDirectory(prefix='accele160-isp-mailbox-') as directory:
        rom = Path(directory) / 'probe.rom'
        sock = Path(directory) / 'bridge.sock'
        rom.write_bytes(image)
        command = [str(ROOT / 'build/accele160-emu'), str(rom), '1000',
                   '--quiet-trace', '--explore-isp-mailbox', f'--bridge-socket={sock}']
        if args.execute_ack:
            command.append('--explore-isp-execute-ack')
        if args.about_ack:
            command.append('--explore-isp-about-ack')
        if args.queue_ack:
            command.append('--explore-isp-queue-ack')
        if args.retry_ack:
            command.append('--explore-isp-retry-ack')
        if args.reset_delay_ack:
            command.append('--explore-isp-reset-delay-ack')
        if args.active_negation_ack:
            command.append('--explore-isp-active-negation-ack')
        if args.feature_ack:
            command.append('--explore-isp-feature-ack')
        if args.status_zero:
            command.append('--explore-isp-status-zero')
        if args.init_id_ack:
            command.append('--explore-isp-init-id-ack')
        if args.bus_reset_ack:
            command.append('--explore-isp-bus-reset-ack')
        if args.target0_ack:
            command.append('--explore-isp-target0-ack')
        process = subprocess.Popen(
            command,
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

                def request(op, offset, value=0):
                    stream.write(f'{op} {BASE + offset:08x} 2 {value:x}\n'.encode())
                    answer = stream.readline().decode().strip()
                    if not answer or answer == 'ERR':
                        raise AssertionError((op, offset, answer))
                    return int(answer, 16)

                def write(offset, value):
                    request('W', offset, value)

                def read(offset):
                    return request('R', offset)

                write(0x70, 6)
                write(0xc0, 0x5000)
                assert (read(0x70), read(0x0a), read(0x0c)) == (0x4000, 6, 3)
                write(0xc0, 0x7000)
                assert (read(0x0a), read(0x0c)) == (0, 0)
                write(0x70, 4)
                write(0x72, 0x1234)
                write(0x74, 0xabcd)
                write(0xc0, 0x5000)
                assert read(0x70) == 0x4000
                write(0xc0, 0x7000)
                write(0x70, 5)
                write(0x74, 0)
                write(0xc0, 0x5000)
                assert (read(0x70), read(0x74)) == (0x4000, 0xabcd)
                write(0xc0, 0x7000)
                def ram_request(op, address, value=0):
                    stream.write(f'{op} {address:08x} 2 {value:x}\n'.encode())
                    answer = stream.readline().decode().strip()
                    if not answer or answer == 'ERR':
                        raise AssertionError((op, address, answer))
                    return int(answer, 16)

                for index in range(32):
                    ram_request('W', 0xc0600df0 + index * 2, index)
                write(0x70, 9)
                write(0x72, 0x1000)
                write(0x74, 0xfe60)
                write(0x76, 0x0df0)
                write(0x78, 32)
                write(0xc0, 0x5000)
                assert (read(0x70), read(0x0a), read(0x0c)) == (0x4000, 6, 3)
                write(0xc0, 0x7000)
                write(0x70, 10)
                write(0x76, 0x4df0)
                write(0xc0, 0x5000)
                assert read(0x70) == 0x4000
                assert [ram_request('R', 0xc0604df0 + index * 2)
                        for index in range(32)] == list(range(32))
                write(0xc0, 0x7000)
                write(0x70, 1)
                write(0x72, 0x1100)
                write(0x76, 0x0df0)
                write(0xc0, 0x5000)
                assert read(0x70) == 0x4000
                write(0xc0, 0x7000)
                write(0x70, 3)
                write(0x76, 0x4df0)
                write(0xc0, 0x5000)
                assert read(0x70) == 0x4000
                assert [ram_request('R', 0xc0604df0 + index * 2)
                        for index in range(32)] == list(range(32))
                write(0xc0, 0x7000)
                ram_request('W', 0xc0600df0, 0xfc20)  # balances two 0..31 blocks
                write(0x70, 1)
                write(0x72, 0x1120)
                write(0x76, 0x0df0)
                write(0x78, 1)
                write(0xc0, 0x5000)
                assert read(0x70) == 0x4000
                write(0xc0, 0x7000)
                write(0x70, 7)
                write(0x72, 0x1000)
                write(0xc0, 0x5000)
                assert read(0x70) == 0x4000
                write(0xc0, 0x7000)
                write(0x70, 4)
                write(0x72, 0x1120)
                write(0x74, 1)
                write(0xc0, 0x5000)
                write(0xc0, 0x7000)
                write(0x70, 7)
                write(0x72, 0x1000)
                write(0xc0, 0x5000)
                assert (read(0x70), read(0x0a), read(0x0c)) == (7, 0, 0)
                stream.write(b'L\n')
                assert int(stream.readline().decode().strip(), 16) == 0x1121
                stream.write(b'K 1100 33\n')
                dump = stream.readline().decode().strip()
                assert len(dump) == 33 * 4
                assert [int(dump[index * 4:index * 4 + 4], 16)
                        for index in range(33)] == list(range(32)) + [1]
                write(0x70, 9)
                write(0x74, 0xffff)  # outside observed bus aperture
                write(0xc0, 0x5000)
                assert (read(0x70), read(0x0a), read(0x0c)) == (9, 0, 0)
                if args.execute_ack:
                    write(0xc0, 0x7000)
                    write(0x70, 2)
                    write(0x72, 0x1000)
                    write(0xc0, 0x5000)
                    assert (read(0x70), read(0x0a), read(0x0c)) == (2, 0, 0)
                if args.about_ack:
                    write(0xc0, 0x7000)
                    write(0x70, 8)
                    write(0xc0, 0x5000)
                    assert (read(0x70), read(0x0a), read(0x0c)) == (8, 0, 0)
                if args.queue_ack:
                    write(0xc0, 0x7000)
                    write(0x70, 0x10)
                    write(0x72, 0x100)
                    write(0x74, 0xfe60)
                    write(0x76, 0x0df0)
                    write(0x78, 0)
                    write(0xc0, 0x5000)
                    assert (read(0x70), read(0x0a), read(0x0c)) == (0x10, 0, 0)
                if args.retry_ack:
                    write(0xc0, 0x7000)
                    write(0x70, 0x32)
                    write(0x72, 0)
                    write(0x74, 2)
                    write(0x76, 0)
                    write(0x78, 0)
                    write(0x7a, 0)
                    write(0xc0, 0x5000)
                    assert (read(0x70), read(0x0a), read(0x0c)) == (0x32, 0, 0)
                if args.reset_delay_ack:
                    write(0xc0, 0x7000)
                    write(0x70, 0x3a)
                    write(0x72, 1)
                    write(0x74, 1)
                    write(0x76, 0)
                    write(0x78, 0)
                    write(0x7a, 0)
                    write(0xc0, 0x5000)
                    assert (read(0x70), read(0x0a), read(0x0c)) == (0x3a, 0, 0)
                if args.active_negation_ack:
                    write(0xc0, 0x7000)
                    write(0x70, 0x35)
                    write(0x72, 0x30)
                    write(0x74, 0x30)
                    write(0x76, 0)
                    write(0x78, 0)
                    write(0x7a, 0)
                    write(0xc0, 0x5000)
                    assert (read(0x70), read(0x0a), read(0x0c)) == (0x35, 0, 0)
                if args.feature_ack:
                    write(0xc0, 0x7000)
                    write(0x70, 0x4a)
                    write(0x72, 0x16)
                    write(0x74, 0x30)
                    write(0x76, 0)
                    write(0x78, 0)
                    write(0x7a, 0)
                    write(0xc0, 0x5000)
                    assert (read(0x70), read(0x0a), read(0x0c)) == (0x4a, 0, 0)
                if args.status_zero:
                    write(0xc0, 0x7000)
                    write(0x70, 0x1f)
                    write(0xc0, 0x5000)
                    assert (read(0x70), read(0x0a), read(0x0c)) == (0x1f, 0, 0)
                if args.init_id_ack:
                    write(0xc0, 0x7000)
                    write(0x70, 0x30)
                    write(0x72, 7)
                    write(0x74, 0)
                    write(0xc0, 0x5000)
                    assert (read(0x70), read(0x0a), read(0x0c)) == (0x30, 0, 0)
                if args.bus_reset_ack:
                    write(0xc0, 0x7000)
                    write(0x70, 0x18)
                    write(0x72, 1)
                    write(0x74, 0)
                    write(0xc0, 0x5000)
                    assert (read(0x70), read(0x0a), read(0x0c)) == (0x18, 0, 0)
                if args.target0_ack:
                    write(0xc0, 0x7000)
                    write(0x70, 0x38)
                    write(0x72, 0)
                    write(0x74, 0xc500)
                    write(0x76, 0x0c0c)
                    write(0xc0, 0x5000)
                    assert (read(0x70), read(0x0a), read(0x0c)) == (0x38, 0, 0)
                print('isp_mailbox=PASS commands=0006,0004,0005,0009,000a,0001,0003,0007 '
                      'dma_roundtrip=32 checksum_guard=PASS dump=PASS invalid_bus=PENDING' +
                      (' incomplete_execute=PENDING' if args.execute_ack else '') +
                      (' premature_about=PENDING' if args.about_ack else '') +
                      (' premature_queue=PENDING' if args.queue_ack else '') +
                      (' premature_retry=PENDING' if args.retry_ack else '') +
                      (' premature_reset_delay=PENDING' if args.reset_delay_ack else '') +
                      (' premature_active_negation=PENDING' if args.active_negation_ack else '') +
                      (' premature_feature=PENDING' if args.feature_ack else '') +
                      (' premature_status=PENDING' if args.status_zero else '') +
                      (' premature_init_id=PENDING' if args.init_id_ack else '') +
                      (' premature_bus_reset=PENDING' if args.bus_reset_ack else '') +
                      (' premature_target0=PENDING' if args.target0_ack else ''))
        finally:
            process.terminate()
            process.communicate(timeout=5)


if __name__ == '__main__':
    main()

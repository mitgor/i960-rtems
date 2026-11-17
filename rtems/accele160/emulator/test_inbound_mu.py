#!/usr/bin/env python3
"""Exercise the stock emulator's inbound message-unit latch over its test socket."""
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
    parser.add_argument('--cycles', type=int, default=60_000_000)
    parser.add_argument('--observe-cycles', type=int, default=0,
                        help='advance this many instructions with the doorbell pending')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='accele160-mu-') as directory:
        path = Path(directory) / 'bridge.sock'
        process = subprocess.Popen(
            [str(args.emulator.resolve()), str(args.image.resolve()),
             str(args.cycles), '--board-id=11', '--quiet-trace',
             f'--bridge-socket={path}'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 90
            while not path.exists():
                if process.poll() is not None:
                    raise AssertionError(f'emulator exited: {process.communicate()}')
                if time.monotonic() > deadline:
                    raise TimeoutError('emulator did not reach bridge-ready')
                time.sleep(0.05)
            with socket.socket(socket.AF_UNIX) as connection:
                connection.connect(str(path))
                stream = connection.makefile('rwb', buffering=0)

                def request(command):
                    stream.write((command + '\n').encode('ascii'))
                    answer = stream.readline().decode('ascii').strip()
                    if answer == 'ERR' or not answer:
                        raise AssertionError(f'{command}: {answer}')
                    return int(answer, 16)

                assert request('I 1320') == 0
                assert request('I 1324') & 4 == 0
                initial_mask = request('I 1328')
                assert request('I ff008510') == 0x6000
                assert request('I ff008520') == 0x4444
                assert request('I ff008524') == 0x6754
                assert request('I ff008528') == 0x80000
                assert request('M 0000000000100000 ' + '00' * 64) == 0
                assert request('I 1310') == 0x100000
                assert request('I 1314') == 0
                assert request('I 1320') & 1
                assert request('I 1324') & 7 == 7
                assert request('Q') == 0  # reset IIMR masks every source
                assert request('C 1328 fffffffb') == 0xfffffffb
                assert request('Q') == 4  # only the doorbell source is unmasked
                assert request('C 1328 ffffffff') == 0xffffffff
                assert request('Q') == 0  # re-masking preserves pending status
                for chunk_start in range(0, args.observe_cycles, 1_000_000):
                    request(f'S {min(1_000_000, args.observe_cycles - chunk_start)}')
                if args.observe_cycles:
                    print(f'pending_after_{args.observe_cycles}='
                          f'{request("I 1320"):08x} '
                          f'status={request("I 1324"):08x}')
                # Message status can clear while the doorbell remains asserted.
                status_after_message_clear = request('C 1324 ffffffff')
                if args.observe_cycles and not (status_after_message_clear & 4):
                    raise AssertionError('firmware consumed the doorbell during observation')
                assert status_after_message_clear & 7 == 4
                assert request('Q') == 0
                assert request('C 1328 fffffffb') == 0xfffffffb
                assert request('Q') == 4
                assert request('S 4096') != 0
                assert request('I 1320') & 1
                assert request('C 1320 1') == 0
                assert request('I 1324') & 7 == 0
                assert request('Q') == 0
                print('inbound_mu=PASS message_words=PASS doorbell=PASS '
                      'status_clear=PASS mask_gating=PASS cpu_step=PASS '
                      'completion=PENDING')
                print(f'inbound_mu_mask={initial_mask:08x}')
        finally:
            process.terminate()
            output, _ = process.communicate(timeout=5)
        state = [line for line in output.splitlines()
                 if line.startswith('checkpoint cpu-interrupt-state ')]
        assert len(state) == 1, output
        print(state[0])


if __name__ == '__main__':
    main()

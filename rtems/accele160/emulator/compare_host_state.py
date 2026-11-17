#!/usr/bin/env python3
"""Compare offline i960 host-visible state at stock and native-ROM milestones."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import time


REGISTERS = {
    'bridge_pci_command': 0x1004,
    'raid_pci_command': 0x1204,
    'pirsr': 0x1050,
    'ipnd': 0xff008500,
    'imsk': 0xff008504,
    'mu_inbound_message0': 0x1310,
    'mu_inbound_message1': 0x1314,
    'mu_inbound_doorbell': 0x1320,
    'mu_inbound_status': 0x1324,
    'mu_inbound_mask': 0x1328,
    'mu_outbound_doorbell': 0x132c,
    'native_report_marker': 0xc0001f00,
    'native_report_result': 0xc0001f04,
    'native_report_pass': 0xc0001f1c,
    'board_context': 0xc04ad650,
}


def capture(emulator: Path, image: Path, cycles: int, label: str,
            output_dir: Path) -> dict:
    image_bytes = image.read_bytes()
    if len(image_bytes) != 0x100000:
        raise ValueError(f'{label}: expected a complete 1 MiB image')
    with tempfile.TemporaryDirectory(prefix=f'accele160-{label}-') as name:
        bridge = Path(name) / 'bridge.sock'
        log = output_dir / f'{label}-emu.log'
        with log.open('w') as stream:
            process = subprocess.Popen(
                [str(emulator.resolve()), str(image.resolve()), str(cycles),
                 '--board-id=11', '--quiet-trace', f'--bridge-socket={bridge}'],
                stdout=stream, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 60
                while not bridge.exists():
                    if process.poll() is not None:
                        raise RuntimeError(f'{label}: emulator exited before bridge')
                    if time.monotonic() > deadline:
                        raise TimeoutError(f'{label}: bridge did not become ready')
                    time.sleep(0.05)
                with socket.socket(socket.AF_UNIX) as connection:
                    connection.connect(str(bridge))
                    wire = connection.makefile('rwb', buffering=0)

                    def read(address: int) -> int:
                        command = (f'R {address:x} 4 0' if
                                   0xc0000000 <= address < 0xc1000000
                                   else f'I {address:x}')
                        wire.write((command + '\n').encode('ascii'))
                        answer = wire.readline().strip()
                        if len(answer) != 8 or answer == b'ERR':
                            raise RuntimeError(f'{label}: read {address:x}: {answer!r}')
                        return int(answer, 16)

                    values = {key: read(address) for key, address in REGISTERS.items()}
                    context = values['board_context']
                    values['board_kind'] = (read(context + 0x14)
                                            if 0xc0000000 <= context <= 0xc0ffffe8
                                            else None)
                    wire.close()
            finally:
                process.terminate()
                process.wait(timeout=5)
    transcript = log.read_text(errors='replace')
    expected = ({
        'stock-early': f'stop cycle={cycles} reason=budget',
        'stock': 'checkpoint stock-runtime-entry cycle=48565709',
        'candidate': 'reason=self-loop ip=c0010030',
    })[label]
    terminal = re.search(r'stop cycle=(\d+) reason=self-loop ip=c0010030', transcript)
    if expected not in transcript or 'reason=cpu-fault' in transcript:
        raise AssertionError(f'{label}: expected emulator milestone absent')
    if label == 'candidate':
        report = re.search(r'^checkpoint native-report ((?:[0-9a-f]{8} ?)+)$',
                           transcript, re.MULTILINE)
        if not terminal or not report or int(report.group(1).split()[7], 16) != 0x50415353:
            raise AssertionError('candidate RTEMS PASS/park record absent')
    return {
        'image_sha256': hashlib.sha256(image_bytes).hexdigest(),
        'cycle_budget': cycles,
        'registers': {key: f'0x{value:08x}' if value is not None else None
                      for key, value in values.items()},
        'emulator_log': log.name,
        'milestone': expected,
        'terminal_cycle': int(terminal.group(1)) if terminal else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--emulator', required=True, type=Path)
    parser.add_argument('--stock', required=True, type=Path)
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    candidate = capture(args.emulator, args.candidate, 3000000, 'candidate',
                        args.output.parent)
    stock_early = capture(args.emulator, args.stock, candidate['terminal_cycle'],
                          'stock-early', args.output.parent)
    stock = capture(args.emulator, args.stock, 60000000, 'stock',
                    args.output.parent)
    result = {
        'scope': 'offline emulator with exploratory reset selector 11',
        'stock_at_candidate_park_cycle': stock_early,
        'stock': stock,
        'candidate': candidate,
    }
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(f'host_state=PASS stock={stock["emulator_log"]} '
          f'candidate={candidate["emulator_log"]}')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Offline host-side reproduction of a PCI configuration-retry stall.

Couples the i960 interpreter (EBCR retry model on) to the QEMU card model
(model-config-retry=on) and boots SeaBIOS to a marker boot sector. While the
i960 firmware has not cleared EBCR bit 2, every host configuration access to
the card is "retried": QEMU advances the i960 and asks again. A real host
bridge retries forever; here a bounded number of attempts stands in for that,
after which QEMU exits with status 66 and a STALL line.

Expected: stock firmware and release candidates let the host reach the boot
sector; images that never release (the one that froze the HP Z400, the
no-release control) stall the host before any option ROM could run.

All runs omit the x86 option ROM so that only the retry behaviour differs.
Offline only. SeaBIOS is not the HP 786G3 BIOS, and the QEMU device still
has a fixed PCI identity rather than the ATU values the i960 programmed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_romless_post import MARKER, boot_sector  # noqa: E402

STALL_EXIT = 66


def run(args, image, directory, label):
    socket = directory / f'{label}.sock'
    emu_log = directory / f'{label}-emu.log'
    debug = directory / f'{label}-debug.log'
    stderr = directory / f'{label}-qemu.log'
    disk = directory / 'boot.img'
    disk.write_bytes(boot_sector())
    emu_command = [str(args.emulator), str(image), '1000', '--board-id=11',
                   '--quiet-trace', ('--model-config-retry-low'
                                     if args.retry_strap_low else '--model-config-retry'),
                   f'--bridge-socket={socket}']
    qemu_command = [str(args.qemu), '-machine', 'pc,accel=tcg', '-m', '64',
                    '-display', 'none', '-serial', 'none', '-monitor', 'none',
                    '-no-reboot', '-boot', 'order=c', '-bios', str(args.bios),
                    '-device', 'accele160-pci-bridge,addr=05.0,multifunction=on',
                    '-device', f'accele160-probe,addr=05.1,bridge-socket={socket},'
                               f'model-config-retry=on,'
                               f'config-retry-limit={args.retry_limit}',
                    '-drive', f'file={disk},format=raw,if=ide',
                    '-chardev', f'file,id=romdebug,path={debug}',
                    '-device', 'isa-debugcon,iobase=0x402,chardev=romdebug']
    if args.qemu_data:
        qemu_command[1:1] = ['-L', str(args.qemu_data)]
    with emu_log.open('w') as emu_stream, stderr.open('w') as qemu_stream:
        emulator = subprocess.Popen(emu_command, stdin=subprocess.DEVNULL,
                                    stdout=emu_stream, stderr=subprocess.STDOUT)
        try:
            deadline = time.time() + 20
            while not socket.exists():
                if emulator.poll() is not None or time.time() > deadline:
                    raise RuntimeError('i960 emulator bridge did not start:\n' +
                                       emu_log.read_text()[-2000:])
                time.sleep(0.05)
            qemu = subprocess.Popen(qemu_command, stdin=subprocess.DEVNULL,
                                    stdout=subprocess.DEVNULL, stderr=qemu_stream)
            try:
                deadline = time.time() + args.seconds
                while time.time() < deadline and qemu.poll() is None:
                    if debug.exists() and MARKER in debug.read_bytes():
                        break
                    time.sleep(0.2)
            finally:
                if qemu.poll() is None:
                    qemu.terminate()
                qemu.communicate(timeout=10)
        finally:
            if emulator.poll() is None:
                emulator.terminate()
            emulator.communicate(timeout=10)
    qemu_text = stderr.read_text(errors='replace')
    lines = qemu_text.splitlines()
    retry = [line for line in lines if line.startswith('accele160 config-retry ')]
    emu_text = emu_log.read_text(errors='replace')
    return {
        'image': image.name,
        'image_sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
        'qemu_exit_code': qemu.returncode,
        'host_stalled': qemu.returncode == STALL_EXIT and
                        any(' STALL ' in line for line in retry),
        'retry_released_seen_by_host': any(' released ' in line for line in retry),
        'boot_sector_reached': debug.exists() and MARKER in debug.read_bytes(),
        'host_config_accesses_logged': sum(
            line.startswith(('accele160 config R ', 'accele160 config W '))
            for line in lines),
        'qemu_stderr_tail': qemu_text[-2000:],
        'emulator_tail': emu_text[-2000:],
        'config_retry_lines': retry,
        'i960_release_lines': [line for line in emu_text.splitlines()
                               if line.startswith('checkpoint config-retry ')],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--qemu', required=True, type=Path,
                        help='QEMU built with this branch\'s accele160.c')
    parser.add_argument('--qemu-data', type=Path, help='QEMU -L firmware directory')
    parser.add_argument('--bios', required=True, type=Path)
    parser.add_argument('--emulator', type=Path,
                        default=Path(__file__).resolve().parents[1] / 'build/accele160-emu')
    parser.add_argument('--must-boot', type=Path, action='append', default=[])
    parser.add_argument('--must-stall', type=Path, action='append', default=[])
    parser.add_argument('--seconds', type=float, default=120)
    parser.add_argument('--retry-limit', type=int, default=120,
                        help='retried attempts (1M i960 instructions each) before STALL')
    parser.add_argument('--retry-strap-low', action='store_true',
                        help='counterfactual: model RETRY pin low at reset; '
                             'the host must enumerate without any firmware release')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.retry_strap_low and args.must_stall:
        parser.error('--must-stall is incompatible with --retry-strap-low')
    if args.output.exists():
        raise FileExistsError(args.output)
    failures, results = [], []
    with tempfile.TemporaryDirectory(prefix='a160-retry-') as name:
        directory = Path(name)
        for index, (image, expect) in enumerate(
                [(p, 'boot') for p in args.must_boot] +
                [(p, 'stall') for p in args.must_stall]):
            result = run(args, image, directory, f'run{index}')
            result['expected'] = expect
            reasserted = any(' reasserted ' in line
                             for line in result['i960_release_lines'])
            if expect == 'boot':
                # The host side caches the release, so a later re-assertion
                # is only visible in the i960 log.
                if args.retry_strap_low:
                    ok = (result['boot_sector_reached'] and not result['host_stalled']
                          and result['host_config_accesses_logged'] > 0
                          and not result['i960_release_lines']
                          and any('ebcr=0x0008 retried-attempts=0' in line
                                  for line in result['config_retry_lines']))
                else:
                    ok = (result['retry_released_seen_by_host'] and not reasserted and
                          result['boot_sector_reached'] and not result['host_stalled'])
            else:
                ok = (result['host_stalled'] and not result['boot_sector_reached']
                      and not result['retry_released_seen_by_host'])
            result['ok'] = ok
            results.append(result)
            print(f"{image.name}: expected={expect} {'PASS' if ok else 'FAIL'} "
                  f"exit={result['qemu_exit_code']} "
                  f"boot_sector={int(result['boot_sector_reached'])} "
                  f"{result['config_retry_lines'][-1] if result['config_retry_lines'] else ''}")
            if not ok:
                failures.append(image.name)
    receipt = {
        'gate': 'accele160 offline host-side configuration-retry reproduction',
        'limits': 'SeaBIOS/QEMU, not the HP BIOS; EBCR reset strap assumed; '
                  'bounded retry stands in for an indefinite host retry; option '
                  'ROM omitted in every run; fixed QEMU PCI identity',
        'qemu_sha256': hashlib.sha256(args.qemu.read_bytes()).hexdigest(),
        'emulator_sha256': hashlib.sha256(args.emulator.read_bytes()).hexdigest(),
        'bios_sha256': hashlib.sha256(args.bios.read_bytes()).hexdigest(),
        'retry_limit': args.retry_limit, 'results': results,
        'retry_strap_low_assumed': args.retry_strap_low,
        'result': 'PASS' if not failures else 'FAIL', 'failures': failures,
        'physical_boot_tested': False, 'safe_to_flash': False,
    }
    args.output.write_text(json.dumps(receipt, indent=1) + '\n')
    print(f"config_retry_post={receipt['result']} (offline model only)")
    return 0 if not failures else 1


if __name__ == '__main__':
    sys.exit(main())

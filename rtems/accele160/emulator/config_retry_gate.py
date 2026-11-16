#!/usr/bin/env python3
"""Offline gate: does an image release 80303 PCI configuration retry like stock?

Intel 80303 mode 3 retries every host configuration cycle until the core
clears EBCR (0x1040) bit 2. An image that never clears it would stall host
PCI enumeration. This gate runs images in the i960 interpreter with the
opt-in retry model and checks, for a candidate:

  1. retry is released, with the stock EBCR value 0x48;
  2. it is released before the RTEMS payload is entered (stage two), so a
     later failure cannot hold the host in retry;
  3. the bridge/ATU register state at release equals stock's state at its
     own release, except for documented differences, and the messaging-unit
     masks equal what stock sets directly after its release;
  4. the PCI0 report record in the host-visible page is complete;
  5. the RTEMS diagnostic still reaches PASS.

It also re-checks the references: stock must release; every --must-hang image
(the image that froze the HP Z400, and the no-release control) must not.
Offline only. A pass says nothing about the physical RETRY strap, which is
inferred from stock firmware and Intel documentation, not measured.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pci_register_trace as trace  # noqa: E402

STOCK_RELEASE_IP = 'c0052e00'
STAGE2 = range(0xc000a000, 0xc0010000)
PASS = 0x50415353
PCI0 = 0x30494350


def run_candidate(emulator, image, cycles):
    with tempfile.TemporaryDirectory() as tmp:
        aperture = Path(tmp) / 'aperture.bin'
        result = trace.run(emulator, image, cycles,
                           extra=(f'--dump-aperture={aperture}',))
        page = aperture.read_bytes()
    result['pci0'] = list(struct.unpack_from('<8I', page, 0x1ee0))
    result['report'] = list(struct.unpack_from('<16I', page, 0x1f00))
    return result


def check_candidate(candidate, stock, hidden_rom):
    problems = []
    summary = candidate['summary']
    if not summary['released']:
        return ['configuration retry is never released: host enumeration would stall']
    if summary['ebcr'] != 0x48:
        problems.append(f"EBCR is {summary['ebcr']:#06x}, stock releases with 0x0048")
    if int(summary['release_ip'], 16) not in STAGE2:
        problems.append(f"release at ip {summary['release_ip']} is not in stage two")
    if any(event['event'] == 'reasserted' for event in candidate['events']):
        problems.append('configuration retry was set again after release')
    expected = dict(stock['state_at_release'])
    if hidden_rom:
        expected['1274'] = 0      # ERLR: stock's own no-ROM value
        expected['1278'] = None   # ERTVR is not written on that path
    actual = candidate['state_at_release']
    for key in sorted(expected):
        if actual.get(key) != expected[key]:
            problems.append(f'register {key}: candidate {actual.get(key)!r} '
                            f'stock {expected[key]!r}')
    # Stock masks the messaging unit right after its release; the candidate
    # must have the same values in place by the time it releases.
    if candidate['mu_state_at_release'] != stock['mu_state_after_stock_mu_init']:
        problems.append(f"messaging-unit setup at release {candidate['mu_state_at_release']}"
                        f" differs from stock {stock['mu_state_after_stock_mu_init']}")
    late = [w for w in candidate['writes']
            if w['origin'] == 'i960' and w['seq'] > candidate['release_seq']
            and w['addr'] < 0x1300]
    if late:
        problems.append(f'{len(late)} bridge/ATU writes after release; first at '
                        f"{late[0]['addr']:#06x}")
    pci0 = candidate['pci0']
    want_flags = 3 if hidden_rom else 2
    if (pci0[0] != PCI0 or pci0[1] != 0x0c or pci0[2] != 0x48 or pci0[3] != want_flags
            or pci0[4] != 0x00501069 or pci0[5] != 0x00541069
            or pci0[7] != candidate['release_seq']):
        problems.append('PCI0 report record mismatch: ' +
                        ' '.join(f'{word:08x}' for word in pci0))
    report = candidate['report']
    if report[0] != 0x32544753 or report[1] != 0x2000 or report[7] != PASS:
        problems.append('RTEMS diagnostic did not reach PASS: ' +
                        ' '.join(f'{word:08x}' for word in report[:8]))
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--emulator', type=Path,
                        default=Path(__file__).parent / 'build/accele160-emu')
    parser.add_argument('--stock', type=Path, required=True,
                        help="the candidate card's own stock 1 MiB image")
    parser.add_argument('--candidate', type=Path, action='append', default=[])
    parser.add_argument('--candidate-keeps-rom', type=Path, action='append', default=[],
                        help='candidate built without ACCELE160_PCI_HIDE_OPTION_ROM')
    parser.add_argument('--must-hang', type=Path, action='append', default=[],
                        help='reference image that must NOT release retry')
    parser.add_argument('--stock-cycles', type=int, default=80_000_000)
    parser.add_argument('--candidate-cycles', type=int, default=4_000_000)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)

    failures = []
    stock = trace.run(args.emulator, args.stock, args.stock_cycles)
    if (not stock['summary']['released'] or stock['summary']['ebcr'] != 0x48 or
            stock['summary']['release_ip'] != STOCK_RELEASE_IP):
        failures.append(f"stock reference did not release as expected: {stock['summary']}")
    receipt = {
        'gate': 'accele160 offline PCI configuration-retry release',
        'model_assumption': 'EBCR resets to 0x000c (Intel 80303 mode 3); '
                            'physical RETRY strap not measured',
        'emulator_sha256': hashlib.sha256(args.emulator.read_bytes()).hexdigest(),
        'stock': {key: stock[key] for key in
                  ('image_sha256', 'summary', 'release_seq', 'state_at_release',
                   'mu_state_after_stock_mu_init', 'stop')},
        'must_hang': [], 'candidates': [],
    }
    for image in args.must_hang:
        result = trace.run(args.emulator, image, args.candidate_cycles)
        hangs = not result['summary']['released']
        receipt['must_hang'].append({
            'image': image.name, 'image_sha256': result['image_sha256'],
            'summary': result['summary'], 'stop': result['stop'],
            'retry_never_released': hangs})
        print(f"must-hang {image.name}: retry_never_released={int(hangs)} "
              f"pci_reg_writes={result['summary']['pci_reg_writes']}")
        if not hangs:
            failures.append(f'{image.name} released retry but is a must-hang reference')
    for image, hidden in ([(p, True) for p in args.candidate] +
                          [(p, False) for p in args.candidate_keeps_rom]):
        result = run_candidate(args.emulator, image, args.candidate_cycles)
        problems = check_candidate(result, stock, hidden)
        receipt['candidates'].append({
            'image': image.name, 'image_sha256': result['image_sha256'],
            'option_rom_hidden': hidden, 'summary': result['summary'],
            'release_seq': result['release_seq'], 'events': result['events'],
            'state_at_release': result['state_at_release'],
            'mu_state_at_release': result['mu_state_at_release'],
            'pci0': [f'{word:08x}' for word in result['pci0']],
            'report': [f'{word:08x}' for word in result['report']],
            'stop': result['stop'], 'problems': problems,
            'stock_release_cycle': stock['summary']['release_cycle']})
        print(f"candidate {image.name}: {'PASS' if not problems else 'FAIL'} "
              f"release_cycle={result['summary']['release_cycle']} "
              f"release_ip={result['summary']['release_ip']}")
        failures += [f'{image.name}: {problem}' for problem in problems]
    receipt['result'] = 'PASS' if not failures else 'FAIL'
    receipt['failures'] = failures
    receipt['physical_boot_tested'] = False
    receipt['safe_to_flash'] = False
    args.output.write_text(json.dumps(receipt, indent=1) + '\n')
    for failure in failures:
        print('FAIL:', failure)
    print(f"config_retry_gate={receipt['result']} (offline model only)")
    return 0 if not failures else 1


if __name__ == '__main__':
    sys.exit(main())

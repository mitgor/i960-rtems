#!/usr/bin/env python3
"""Capture and compare 80303 bridge/ATU register writes in the offline i960 model.

Runs `accele160-emu --trace-pci-registers --model-config-retry` on a saved
1 MiB flash image and records every store into the host-facing register
blocks (bridge 0x1000, ATU 0x1200, messaging unit 0x1300), plus
whether and when EBCR (0x1040) bit 2, Configuration Cycle Retry, was cleared.
Offline only: no card, PCI device or flash is touched.

The values are what firmware wrote in the model. Registers the firmware
read-modify-writes start from modeled zero, not measured reset values.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

WRITE = re.compile(
    r'^checkpoint pci-reg-write seq=(\d+) cycle=(\d+) origin=(i960|host) '
    r'ip=([0-9a-f]{8}) addr=([0-9a-f]{4}) size=([124]) value=([0-9a-f]+)$')
RELEASE = re.compile(
    r'^checkpoint config-retry (released|reasserted) cycle=(\d+) '
    r'ip=([0-9a-f]{8}) ebcr=([0-9a-f]{4})$')
WIDE = re.compile(r'^checkpoint pci-reg-write-wide ')
SUMMARY = re.compile(
    r'^checkpoint config-retry-summary released=([01]) ebcr=([0-9a-f]{4}) '
    r'release-cycle=(\d+) release-ip=([0-9a-f]{8}) pci-reg-writes=(\d+)$')

# Registers compared between stock and native at the moment retry is released.
# (address, size, name). Names and addresses are from the register defines in
# Intel application note 273395-005 (80303 programming guide), section 4.
COMPARED = (
    (0x1200, 2, 'ATUVID'), (0x1202, 2, 'ATUDID'),
    (0x120a, 1, 'ATU subclass'), (0x120b, 1, 'ATU base class'),
    (0x120c, 1, 'ATUCLSR'), (0x120d, 1, 'ATULT'),
    (0x122c, 2, 'ASVIR'), (0x122e, 2, 'ASIR'),
    (0x1240, 4, 'PIALR'), (0x1244, 4, 'PIATVR'),
    (0x1248, 4, 'SIABAR'), (0x124c, 4, 'SIALR'), (0x1250, 4, 'SIATVR'),
    (0x1268, 4, 'SOMWVR'),
    (0x1274, 4, 'ERLR'), (0x1278, 4, 'ERTVR'),
    (0x1288, 4, 'ATUCR'), (0x1298, 2, 'SATUCMD'),
    (0x12bc, 4, 'PATUIMR'), (0x12c0, 4, 'SATUIMR'),
    (0x1004, 2, 'bridge PCMD'), (0x100c, 1, 'bridge CLSR'),
    (0x100d, 1, 'bridge PLTR'), (0x101a, 1, 'bridge SUBBNR'),
    (0x101b, 1, 'bridge SLTR'), (0x101c, 1, 'bridge IOBR'),
    (0x101d, 1, 'bridge IOLR'), (0x1020, 2, 'bridge MBR'),
    (0x1022, 2, 'bridge MLR'), (0x1024, 2, 'bridge PMBR'),
    (0x1026, 2, 'bridge PMLR'), (0x1034, 2, 'BSVIR'),
    (0x1036, 2, 'BSIR'), (0x103e, 2, 'bridge BCR'),
    (0x1040, 2, 'EBCR'), (0x1042, 2, 'SISR'), (0x104c, 4, 'SACR'),
    (0x1050, 4, 'PIRSR'), (0x1054, 1, 'SIOBR'), (0x1055, 1, 'SIOLR'),
    (0x1058, 2, 'SMBR'), (0x105a, 2, 'SMLR'), (0x105c, 2, 'SDER'),
)
# Messaging-unit setup. Stock performs these seven stores (routine c004e450)
# immediately after its release; the native routine performs them before.
MU_INIT = (
    (0x1310, 4, 'IMR0'), (0x1314, 4, 'IMR1'), (0x1318, 4, 'OMR0'),
    (0x131c, 4, 'OMR1'), (0x1324, 4, 'IISR (write-one-to-clear)'),
    (0x1328, 4, 'IIMR'), (0x1334, 4, 'OIMR'),
)
MU_INIT_STOCK_WRITES = 7
# Not compared, with the reason. Kept explicit so an omission is a decision.
EXCLUDED = {
    0x1206: 'ATUSR is write-one-to-clear status; the model stores the raw word',
    0x1044: 'PBISR is write-one-to-clear status; the zeros that stock\'s '
            'unaligned 32-bit SISR store puts there have no effect',
    0x1048: 'SBISR is write-one-to-clear status',
    0x12a8: 'SOCCAR is only the secondary-scan address selector',
}


def parse(text):
    """Return (writes, events, summary) from emulator stdout."""
    writes, events, summary = [], [], None
    for line in text.splitlines():
        if WIDE.match(line):
            raise RuntimeError('store wider than 4 bytes into a traced register '
                               'block; not modeled: ' + line)
        match = WRITE.match(line)
        if match:
            seq, cycle, origin, ip, addr, size, value = match.groups()
            writes.append({'seq': int(seq), 'cycle': int(cycle), 'origin': origin,
                           'ip': ip, 'addr': int(addr, 16), 'size': int(size),
                           'value': int(value, 16)})
            continue
        match = RELEASE.match(line)
        if match:
            kind, cycle, ip, ebcr = match.groups()
            events.append({'event': kind, 'cycle': int(cycle), 'ip': ip,
                           'ebcr': int(ebcr, 16)})
            continue
        match = SUMMARY.match(line)
        if match:
            released, ebcr, cycle, ip, count = match.groups()
            summary = {'released': released == '1', 'ebcr': int(ebcr, 16),
                       'release_cycle': int(cycle), 'release_ip': ip,
                       'pci_reg_writes': int(count)}
    return writes, events, summary


def state_at(writes, last_seq=None, initial=None):
    """Byte-wise register image after applying writes up to last_seq."""
    image = dict(initial or {})
    for write in writes:
        if last_seq is not None and write['seq'] > last_seq:
            break
        for index in range(write['size']):
            image[write['addr'] + index] = (write['value'] >> (8 * index)) & 0xff
    return image


def register(image, addr, size):
    """Little-endian register value; bytes never written read as None."""
    if any(addr + index not in image for index in range(size)):
        return None
    return sum(image[addr + index] << (8 * index) for index in range(size))


def release_seq(writes):
    """seq of the first i960 write that leaves EBCR bit 2 clear, else None."""
    for write in writes:
        if (write['origin'] == 'i960' and write['addr'] <= 0x1040 <
                write['addr'] + write['size']):
            low = (write['value'] >> (8 * (0x1040 - write['addr']))) & 0xff
            if not low & 4:
                return write['seq']
    return None


def compared_state(writes):
    seq = release_seq(writes)
    image = state_at(writes, seq, {0x1040: 0x0c, 0x1041: 0})
    return {f'{addr:04x}': register(image, addr, size)
            for addr, size, _name in COMPARED}


def mu_state(writes, after_release=0):
    """MU setup registers as written up to release (+ N following stores)."""
    seq = release_seq(writes)
    if seq is None:
        return None
    image = state_at(writes, seq + after_release)
    return {f'{addr:04x}': register(image, addr, size)
            for addr, size, _name in MU_INIT}


def run(emulator, image, cycles, board_id=11, extra=()):
    command = [str(emulator), str(image), str(cycles), f'--board-id={board_id}',
               '--quiet-trace', '--trace-pci-registers', '--model-config-retry',
               *extra]
    done = subprocess.run(command, text=True, capture_output=True, timeout=600)
    writes, events, summary = parse(done.stdout)
    if summary is None:
        raise RuntimeError('emulator printed no config-retry summary:\n' +
                           done.stdout[-2000:] + done.stderr[-2000:])
    stop = [line for line in done.stdout.splitlines() if line.startswith('stop ')]
    return {
        'image_sha256': hashlib.sha256(Path(image).read_bytes()).hexdigest(),
        'command': command[2:], 'returncode': done.returncode,
        'stop': stop[-1] if stop else None,
        'model': {
            'ebcr_reset_value': '0x000c (assumed Intel mode 3: RETRY strapped high, '
                                'bit 3 at its documented default)',
            'board_id': board_id,
            'note': 'offline interpreter; register reads use modeled values',
        },
        'summary': summary, 'events': events, 'writes': writes,
        'release_seq': release_seq(writes),
        'state_at_release': compared_state(writes),
        'mu_state_at_release': mu_state(writes),
        'mu_state_after_stock_mu_init': mu_state(writes, MU_INIT_STOCK_WRITES),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--emulator', type=Path,
                        default=Path(__file__).parent / 'build/accele160-emu')
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--cycles', type=int, default=80_000_000)
    parser.add_argument('--board-id', type=int, default=11)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    result = run(args.emulator, args.image, args.cycles, args.board_id)
    args.out.write_text(json.dumps(result, indent=1) + '\n')
    summary = result['summary']
    print(f"image={result['image_sha256']} released={int(summary['released'])} "
          f"ebcr={summary['ebcr']:04x} release_cycle={summary['release_cycle']} "
          f"release_ip={summary['release_ip']} writes={len(result['writes'])}")
    return 0


if __name__ == '__main__':
    sys.exit(main())

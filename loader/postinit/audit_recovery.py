#!/usr/bin/env python3
"""Offline, version-specific boot recovery extraction and partial vendor checks."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from build_image import inspect_stock


def sha(data):
    return hashlib.sha256(data).hexdigest()


def audit(stock, package):
    inspect_stock(stock)
    if len(package) < 522 or package[:8] != b'MIMGMYLX':
        raise ValueError('invalid MIMG header or truncated package')
    declared = struct.unpack_from('<I', package, 8)[0]
    if declared != len(package)-10:
        raise ValueError('container length mismatch')
    if package[13] != 2:
        raise ValueError('this audit only covers the type-2 firmware component')
    adapter = struct.unpack_from('<H', package, 0x58)[0] or 0x10
    if adapter != (0x10 & 0xfe) or adapter != (0x11 & 0xfe):
        raise ValueError('adapter ID fails recovered vendor comparison')
    desc = stock[0x79c00:0x79d60]
    if desc[:4] != b'XLYM' or desc[10] > 5:
        raise ValueError('unexpected descriptor')
    entries = []
    for i in range(desc[10]):
        pos = 0x20+i*0x40
        offset, length = struct.unpack_from('<II', desc, pos)
        entries.append(dict(type=desc[pos+8], offset=offset, length=length))
    firmware = [e for e in entries if e['type'] == 2]
    if len(firmware) != 1 or declared-512 != firmware[0]['length']:
        raise ValueError('firmware size does not match stock descriptor')
    monitor = stock[0x7d600:0x80000]
    return monitor, dict(
        analysis_only=True, hardware_validated=False, flash_ready=False,
        stock_sha256=sha(stock), package_sha256=sha(package),
        monitor_sha256=sha(monitor), monitor_length=len(monitor),
        monitor_flash_offset=0x7d600, monitor_ram_entry=0xc0010000,
        recovery_pci_id='1069:0011', staging_ram=0xc0140000,
        monitor_opcodes={'0x20':'read staging', '0x21':'upload staging',
                         '0x2b/1':'program lower 496 KiB',
                         '0x2b/2':'read descriptor', '0x2b/3':'upload descriptor'},
        descriptor_entries=entries,
        partial_vendor_checks={'magic':True, 'type_2':True,
                               'declared_length':True, 'descriptor_length':True,
                               'normal_and_recovery_adapter_comparison':True},
        vendor_acceptance_verified=False,
        outstanding=['physical serial trigger and pinout',
                     'cold-boot enumeration and read-only recovery transaction',
                     'complete vendor descriptor mutations and controller discovery',
                     'independent restoration test'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock', required=True)
    p.add_argument('--package', required=True)
    p.add_argument('--out-dir', required=True)
    a = p.parse_args()
    try:
        monitor, report = audit(Path(a.stock).read_bytes(), Path(a.package).read_bytes())
        dest = Path(a.out_dir)
        dest.mkdir(exist_ok=False)
        (dest/'recovery-monitor.bin').write_bytes(monitor)
        (dest/'audit.json').write_text(json.dumps(report, indent=2)+'\n')
    except (OSError, ValueError) as exc:
        p.error(str(exc))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

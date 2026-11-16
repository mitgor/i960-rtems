#!/usr/bin/env python3
"""Install the AcceleRAID PCI probe into an unpacked QEMU 6.2.0 source tree."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('qemu_source', type=Path)
    args = parser.parse_args()
    root = args.qemu_source.resolve()
    version = (root / 'VERSION').read_text().strip()
    if version != '6.2.0':
        raise ValueError(f'expected QEMU 6.2.0, got {version}')
    meson = root / 'hw/misc/meson.build'
    source = root / 'hw/misc/accele160.c'
    stanza = "softmmu_ss.add(when: 'CONFIG_PCI_TESTDEV', if_true: files('accele160.c'))"
    current = meson.read_text()
    if stanza not in current:
        anchor = "softmmu_ss.add(when: 'CONFIG_PCI_TESTDEV', if_true: files('pci-testdev.c'))"
        if current.count(anchor) != 1:
            raise ValueError('QEMU meson anchor changed')
        meson.write_text(current.replace(anchor, anchor + '\n' + stanza))
    payload = (Path(__file__).parent / 'accele160.c').read_bytes()
    if source.exists() and b'AcceleRAID 160 host-facing PCI probe model' not in source.read_bytes():
        raise ValueError(f'{source} already exists and is not this probe')
    source.write_bytes(payload)
    print(f'accele160_probe=installed qemu={version} source={source}')


if __name__ == '__main__':
    main()

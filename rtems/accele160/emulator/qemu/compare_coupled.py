#!/usr/bin/env python3
"""Compare archived stock/candidate QEMU and i960 observations.

This compares recorded observations, not physical BIOS outcomes. A matching
prefix is never promoted to a boot pass, especially when a trace was capped.
"""

import argparse
import json
from pathlib import Path
import re


ROM_STREAMS = (
    'first_config_accesses',
    'first_bar_accesses',
    'mailbox_bytes_hex',
    'mailbox_submissions',
    'extended_config_accesses',
    'first_rom_blocks',
)
EMU_EVENTS = (
    'checkpoint host-pci-command ',
    'checkpoint exploratory-host-doorbell ',
    'checkpoint bridge-step ',
    'checkpoint native-report ',
    'checkpoint cpu-interrupt-state ',
)


def first_difference(left, right):
    for index, (a, b) in enumerate(zip(left, right)):
        if a != b:
            return {'index': index, 'stock': a, 'candidate': b}
    if len(left) != len(right):
        index = min(len(left), len(right))
        return {
            'index': index,
            'stock': left[index] if index < len(left) else None,
            'candidate': right[index] if index < len(right) else None,
        }
    return None


def normalized_emu_events(path):
    events = []
    for line in path.read_text(errors='replace').splitlines():
        if line.startswith(EMU_EVENTS):
            events.append(line)
    return events


def steps(path):
    answer = []
    for line in path.read_text(errors='replace').splitlines():
        if line.startswith('checkpoint bridge-step '):
            answer.append(dict(re.findall(r'([\w-]+)=([0-9a-fA-F]+)', line)))
    return answer


def first_step_difference(stock_steps, candidate_steps):
    for index, (stock, candidate) in enumerate(zip(stock_steps, candidate_steps)):
        fields = {
            key: {'stock': stock.get(key), 'candidate': candidate.get(key)}
            for key in stock.keys() | candidate.keys()
            if stock.get(key) != candidate.get(key)
        }
        if fields:
            return {'index': index, 'fields': dict(sorted(fields.items()))}
    if len(stock_steps) != len(candidate_steps):
        return {'index': min(len(stock_steps), len(candidate_steps)),
                'fields': {'step_count': {'stock': len(stock_steps),
                                          'candidate': len(candidate_steps)}}}
    return None


def compare(stock_rom, candidate_rom, stock_emu, candidate_emu):
    stock = json.loads(stock_rom.read_text())
    candidate = json.loads(candidate_rom.read_text())
    streams = {}
    for name in ROM_STREAMS:
        a, b = stock.get(name, []), candidate.get(name, [])
        streams[name] = {
            'stock_observed': len(a),
            'candidate_observed': len(b),
            'first_difference': first_difference(a, b),
        }
    stable = ('option_rom_sha256', 'pci_identity', 'pci_revision',
              'option_rom_guest_base')
    identity = {name: {'stock': stock.get(name), 'candidate': candidate.get(name)}
                for name in stable}
    if stock['image_sha256'] == candidate['image_sha256']:
        raise ValueError('stock and candidate captures name the same flash image')
    a_events, b_events = normalized_emu_events(stock_emu), normalized_emu_events(candidate_emu)
    a_steps, b_steps = steps(stock_emu), steps(candidate_emu)
    differences = {
        'rom_streams': streams,
        'emulator_events': {
            'stock_observed': len(a_events),
            'candidate_observed': len(b_events),
            'first_difference': first_difference(a_events, b_events),
        },
        'bridge_step_fields': {
            'first_difference': first_step_difference(a_steps, b_steps),
            'stock': a_steps,
            'candidate': b_steps,
        },
    }
    limits = []
    if stock.get('bar_trace_limited') or candidate.get('bar_trace_limited'):
        limits.append('BAR trace capped: equality covers only the saved prefix')
    if stock.get('rom_blocks_sha256') != candidate.get('rom_blocks_sha256'):
        limits.append('ROM block digests differ; inspect scheduling and trace lengths')
    if not a_steps or not b_steps:
        limits.append('one or both i960 captures lack a bridge-step checkpoint')
    if not any('command-dispatch' in step and int(step['command-dispatch']) > 0
               for step in a_steps):
        limits.append('stock controller command completion is not demonstrated')
    limits.append('SeaBIOS/QEMU is not the HP Z400 BIOS or physical card timing')
    return {
        'gate': 'INCONCLUSIVE',
        'stock_image_sha256': stock['image_sha256'],
        'candidate_image_sha256': candidate['image_sha256'],
        'identity': identity,
        'differences': differences,
        'limits': limits,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock-rom', required=True, type=Path)
    parser.add_argument('--candidate-rom', required=True, type=Path)
    parser.add_argument('--stock-emu', required=True, type=Path)
    parser.add_argument('--candidate-emu', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = compare(args.stock_rom, args.candidate_rom,
                     args.stock_emu, args.candidate_emu)
    result = json.dumps(report, indent=2) + '\n'
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end='')


if __name__ == '__main__':
    main()

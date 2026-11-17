#!/usr/bin/env python3
"""Check a pinned stock image through ZIP1 expansion and runtime handoff."""
import hashlib
from pathlib import Path
import re
import subprocess
import sys

STOCK_SHAS = {
    '0a951782a7ccd1855746ffeb3a1b64563287bc56e0dce77d63b79c71ec3b502a': 'original',
    'fadd2b0f6ed9bb88d7c846edd235e5e222cbe3a990b694115c5fa66170e7a816': 'spare',
}
CRC = 'checkpoint loader-checksum computed=d93addd1 stored=d93addd1'
ENTRY = re.compile(r'checkpoint stock-runtime-entry cycle=(\d+) ip=c004cf70')


def main():
    stock = Path(sys.argv[1]).resolve()
    kind = STOCK_SHAS.get(hashlib.sha256(stock.read_bytes()).hexdigest())
    if kind is None:
        raise ValueError('expected a pinned original or spare stock flash image')
    binary = Path(__file__).parent / 'build/accele160-emu'
    run = subprocess.run([str(binary.resolve()), str(stock), '60000000',
                          '--board-id=11', '--quiet-trace'],
                         text=True, capture_output=True, timeout=90)
    lines = run.stdout.splitlines()
    if run.returncode not in (0, 1):
        raise RuntimeError(run.stderr or 'runner failed')
    if lines.count('checkpoint huffman-count generated=00000040 required=00000040') != 2:
        raise ValueError('stock ZIP1 Huffman tables did not validate')
    if CRC not in lines:
        raise ValueError('stock uncompressed CRC did not match')
    entries = [ENTRY.fullmatch(line) for line in lines]
    entries = [match for match in entries if match]
    if len(entries) != 1:
        raise ValueError('expected exactly one stock runtime handoff')
    terminal = next((line for line in reversed(lines) if line.startswith('stop ')), None)
    if terminal is None:
        raise ValueError('runner has no bounded terminal result')
    print(f'stock_loader=PASS image={kind} runtime_entry_cycle={entries[0].group(1)}')
    print(f'whole_card=INCONCLUSIVE {terminal}')


if __name__ == '__main__':
    main()

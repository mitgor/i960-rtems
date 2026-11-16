#!/usr/bin/env python3
"""Check a pinned candidate's bounded RTEMS scheduler run."""
import hashlib
from pathlib import Path
import subprocess
import sys

CANDIDATE_SHAS = {
    '3f97745c76bd2d5e71a5ee143c9c9fec86bdb6a9d4a4b1202093eb944767909c': 'original',
    '6f16d71310d75937b5f3961b1faae81eab3258a29371c8505d788c50c545e3bd': 'spare',
}
REPORT = ('checkpoint native-report 32544753 00002000 00003de0 cd5e027e '
          '00000040 00000000 00000001 50415353 00000000')
PARK = 'stop cycle=1608278 reason=self-loop ip=c0010030'


def main():
    candidate = Path(sys.argv[1]).resolve()
    kind = CANDIDATE_SHAS.get(hashlib.sha256(candidate.read_bytes()).hexdigest())
    if kind is None:
        raise ValueError('expected a pinned original or spare native-ROM candidate')
    binary = Path(__file__).parent / 'build/accele160-emu'
    run = subprocess.run([str(binary.resolve()), str(candidate), '3000000',
                          '--board-id=11', '--quiet-trace'],
                         text=True, capture_output=True, timeout=30)
    lines = run.stdout.splitlines()
    if run.returncode != 1 or lines.count(REPORT) != 1 or PARK not in lines:
        raise AssertionError(run.stdout + run.stderr)
    if 'checkpoint context-after-ret ip=c0013bf0 rip=c0013bf0 fp=c0018b80 pfp=00000000' not in lines:
        raise AssertionError('first RTEMS context restore was not observed')
    print(f'candidate_rtems=PASS image={kind} worker_count=64 done=1 park_code=0')
    print('whole_card=INCONCLUSIVE no host PCI/BIOS model')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Verify the curated artifact manifest, optionally checking Git index contents.

Use --update after intentionally changing artifacts. Normal invocation is read-only.
"""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / 'artifacts'
INVENTORY = ARTIFACTS / 'artifact-inventory.json'
SUMS = ARTIFACTS / 'SHA256SUMS'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def rows(tracked_only=False):
    # Parallel tasks may be preparing unrelated, untracked artifact directories.
    # An explicit index scope lets a batch inventory only the files it has staged.
    tracked = None
    if tracked_only:
        tracked = set(subprocess.check_output(
            ['git', 'ls-files', '-z', '--', 'artifacts'], cwd=ROOT
        ).decode().split('\0'))
    result = []
    for p in sorted(ARTIFACTS.rglob('*')):
        if not p.is_file() or p in (INVENTORY, SUMS):
            continue
        if p.name == '.DS_Store' or '__pycache__' in p.parts:
            continue
        if tracked is not None and p.relative_to(ROOT).as_posix() not in tracked:
            continue
        if p.is_symlink():
            raise ValueError(f'Unexpected artifact symlink: {p}')
        result.append(dict(path=p.relative_to(ROOT).as_posix(),
                           size=p.stat().st_size, sha256=digest(p)))
    return result


def indexed_rows(entries=None):
    """Hash staged blobs without reading unrelated dirty working-tree artifacts."""
    if entries is None:
        entries = subprocess.check_output(
            ['git', 'ls-files', '-s', '-z', '--', 'artifacts'], cwd=ROOT)
    selected = []
    for entry in entries.split(b'\0'):
        if not entry:
            continue
        meta, raw_path = entry.split(b'\t', 1)
        mode, oid, stage = meta.split()
        name = raw_path.decode()
        if stage != b'0' or mode not in (b'100644', b'100755'):
            raise ValueError('Unmerged/nonregular indexed artifact: ' + name)
        if name in ('artifacts/SHA256SUMS', 'artifacts/artifact-inventory.json'):
            continue
        if Path(name).name == '.DS_Store' or '__pycache__' in Path(name).parts:
            continue
        selected.append((name, oid))
    result, cache = [], {}
    with subprocess.Popen(['git', 'cat-file', '--batch'], cwd=ROOT,
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE) as proc:
        for name, oid in sorted(selected, key=lambda item: Path(item[0])):
            if oid not in cache:
                proc.stdin.write(oid + b'\n')
                proc.stdin.flush()
                header = proc.stdout.readline().split()
                if len(header) != 3 or header[:2] != [oid, b'blob']:
                    raise ValueError('Invalid Git blob response: ' + name)
                size = remaining = int(header[2])
                sha = hashlib.sha256()
                while remaining:
                    chunk = proc.stdout.read(min(remaining, 1024 * 1024))
                    if not chunk:
                        raise ValueError('Truncated Git blob: ' + name)
                    sha.update(chunk)
                    remaining -= len(chunk)
                if proc.stdout.read(1) != b'\n':
                    raise ValueError('Invalid Git blob boundary: ' + name)
                cache[oid] = (size, sha.hexdigest())
            size, checksum = cache[oid]
            result.append(dict(path=name, size=size, sha256=checksum))
        proc.stdin.close()
        if proc.wait():
            raise ValueError('git cat-file failed')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--update', action='store_true')
    parser.add_argument('--check-git', action='store_true')
    parser.add_argument('--tracked-only', action='store_true',
                        help='Scope inventory to Git-indexed artifact paths; stage new batch files first.')
    parser.add_argument('--index-bytes', action='store_true',
                        help='With --tracked-only, hash staged bytes rather than dirty working-tree files.')
    args = parser.parse_args()
    if args.index_bytes and not args.tracked_only:
        parser.error('--index-bytes requires --tracked-only')
    index_entries = subprocess.check_output(
        ['git', 'ls-files', '-s', '-z', '--', 'artifacts'], cwd=ROOT) if args.index_bytes else None
    actual = indexed_rows(index_entries) if args.index_bytes else rows(args.tracked_only)
    if args.index_bytes and index_entries != subprocess.check_output(
            ['git', 'ls-files', '-s', '-z', '--', 'artifacts'], cwd=ROOT):
        raise SystemExit('Artifact index changed during hashing; retry the audit.')
    if args.update:
        inventory = json.loads(INVENTORY.read_text())
        inventory['updated_date'] = date.today().isoformat()
        inventory['files'] = actual
        INVENTORY.write_text(json.dumps(inventory, indent=2) + '\n')
    expected = json.loads(INVENTORY.read_text())['files']
    if actual != expected:
        raise SystemExit('Artifact inventory differs; investigate before using --update.')
    sums = {r['path']: r['sha256'] for r in actual}
    sums[INVENTORY.relative_to(ROOT).as_posix()] = digest(INVENTORY)
    text = ''.join(f'{sums[name]}  {name}\n' for name in sorted(sums))
    if args.update:
        SUMS.write_text(text)
    if SUMS.read_text() != text:
        raise SystemExit('SHA256SUMS differs from verified inventory.')
    if args.check_git:
        # Check paths and blob bytes, so stale staged copies cannot pass.
        entries = subprocess.check_output(
            ['git', 'ls-files', '-s', '-z', '--', 'artifacts'], cwd=ROOT)
        if args.index_bytes and entries != index_entries:
            raise SystemExit('Artifact index changed during verification; retry the audit.')
        indexed = {}
        for entry in entries.split(b'\0'):
            if not entry:
                continue
            meta, path = entry.split(b'\t', 1)
            mode, oid, stage = meta.split()
            if stage != b'0':
                raise SystemExit('Unmerged artifact in Git index.')
            indexed[path.decode()] = oid.decode()
        names = sorted(set(sums) | {SUMS.relative_to(ROOT).as_posix()})
        missing = set(names) - set(indexed)
        if missing:
            raise SystemExit('Artifacts missing from Git index: ' + ', '.join(sorted(missing)))
        if args.index_bytes:
            # All other artifact bytes were just read from the index above.
            names = [INVENTORY.relative_to(ROOT).as_posix(), SUMS.relative_to(ROOT).as_posix()]
        hashes = subprocess.check_output(['git', 'hash-object', '--stdin-paths'],
            input=('\n'.join(names) + '\n').encode(), cwd=ROOT).decode().splitlines()
        stale = [name for name, oid in zip(names, hashes) if indexed[name] != oid]
        if stale:
            raise SystemExit('Git index differs from disk: ' + ', '.join(stale))
    print(f'Verified {len(sums)} SHA256 entries' +
          (' and matching Git index blobs.' if args.check_git else '.'))


if __name__ == '__main__':
    main()

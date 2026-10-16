> Historical milestone. Payloads and original relative links belong to Git snapshot `a8af272`. See [restoration instructions](../README.md#historical-evidence).

# Local temporary-file preservation and cleanup — 2026-10-16

Scope: the 315 top-level entries in `/private/tmp` whose names contain `i960`,
`doom` or `mylex`, as listed in `roots.json`. `/tmp` resolves to `/private/tmp`
on this Mac. Unrelated temporary files, the repository, the remote PC and its
running services are outside this cleanup. Existing unrelated working changes
were left untouched.

## Preservation audit

The immutable reference commit is recorded in `base-commit.txt`. `audit.py`
reads committed Git blob bytes and indexes their SHA256 digests. It also hashes
members of committed tar/ZIP archives, decompressed single-file gzip/xz payloads,
and all eight split candidate archives. On-disk outer archives and split parts
must match committed bytes before their contents are trusted. Archives are
streamed, not extracted into the filesystem. Content equality, not filename or
mtime similarity, establishes a match.

The index contains **113,152 distinct committed payloads**. Four old ZIP members
use unsupported compression and are explicitly listed in
`unsupported-zip-members.jsonl`; they do not count as member matches. An initial
indexing attempt stopped at that limitation, before any deletion; the completed
scan records it and preserves unmatched bytes conservatively.

The temporary inventory contains **170,884 regular files**:

- **167,784 files** match committed data, directly or inside archives.
- **3,100 files** do not have a proven byte match. Their **2,588 unique payloads**
  total **238,241,670 bytes (227.2 MiB)** before compression.
- All unmatched bytes are preserved, including reproducible build/research files
  and original archive wrappers. No subjective decision that a failed run or
  temporary script was disposable was needed.
- Directory definitions, symlink targets, file modes and mtimes are retained in
  `files.jsonl.gz`. Symlinks were not followed during inventory.

Notable previously unmatched material includes the original height/branch probe
archive, older checkpoint/control journals, temporary patch/analysis scripts,
research source repositories, Intel reference PDF and disassembly. Some may
represent alternate packaging of already saved evidence; exact unmatched bytes
are retained nonetheless.

`files.jsonl.gz` gives every original path, kind, size/hash and either a committed
source locator or a null `git_source` indicating a newly archived payload.
Locators use `git:COMMIT:path`, optionally `::member`, `::decompressed`, or
`::concatenated::member` for a split archive. `preflight.json` records original
allocated space (approximately 45 GiB); logical byte counts differ from allocated
blocks. The limited credential-marker scan found no matches; it is not a general
security certification.

## Recovering the previously missing files

The recovery archive stores deduplicated payloads as `sha256/HASH`. Its split
parts and complete archive checksum are in `recovery-parts.json`. Parts are at
most 80 MiB, suitable for ordinary Git blobs. The packer re-reads and verifies
every archived payload against the original inventory before accepting it.

To restore the 3,100 newly preserved files, maintaining their original relative
paths underneath a **new destination directory**:

```sh
python3 artifacts/tmp-cleanup-20261016/restore_missing.py /absolute/new/destination
```

This verifies every part, the concatenated archive and every recovered file.
It does not overwrite `/tmp`, and deliberately does not activate historical
absolute symlinks. Their definitions remain in the manifest. This helper restores
only previously missing bytes; the other files remain available at their
committed source locators and original experiment extraction scripts.

A complete trial restore is recorded in `recovery-restore.log` and independently
checked in `recovery-proof.json` before deletion.

## Deletion gate

Recovery evidence and scripts are committed before `cleanup.py --delete` runs.
The cleanup script checks the manifest, archive parts and scripts against that
commit, verifies all recovery payloads again, checks live open files/process
references, and re-hashes every temporary regular file. It requires unchanged
tree membership, kinds, modes, mtimes, link targets and file content. Changed,
in-use or special-file roots are retained and reported instead of removed.

Only the explicitly inventoried roots can be removed. After a final metadata and
activity check, each root is renamed into this task's private quarantine and
removed without following symlinks. `deletion.json` records successes, retained
roots, any incomplete quarantine and the recovery commit. Unrelated `/tmp`
entries and newly appearing project roots are never swept by a wildcard.

## Completed result

All **315 roots were removed** after re-hashing, with **zero retained/changed/in-use
roots** and no incomplete quarantine. No matching project temporary entries
remain. Their initial allocated footprint was **44.98 GiB**.
The deletion pass observed **45.09 GiB** more free space;
filesystem free-space changes can include background activity and APFS accounting.
The verified recovery bundle is **138.90 MiB compressed**, plus manifests/docs.
All 3,100 unmatched files were recovered and independently hash-checked before
the originals were deleted. Recovery was committed first as `97a1427c3dc258ba42ec6f78103e26d466ad2bdc`.

The audit's own temporary database, reconstructed recovery archive, trial-restore
tree and raw open-file listing were also removed after successful completion.
See [deletion record](deletion.json), [outcome](outcome.json) and
[preserved-file groups](preserved-summary.json). Unrelated local work and remote
services were not modified.

These are historical one-time audit scripts: do not rerun inventory/deletion in
this evidence directory, as their reports would replace this record. Use the
non-destructive `restore_missing.py` command above for recovery.

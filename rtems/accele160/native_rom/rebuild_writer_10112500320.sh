#!/usr/bin/env bash
# Offline-only exact rebuild for the October handler card. No PCI access.
set -euo pipefail
if [[ $# != 1 ]]; then
  echo "usage: $0 NEW_OUTPUT_DIR" >&2
  exit 2
fi
repo=$(cd "$(dirname "$0")/../../.." && pwd)
out=$1
bash "$repo/rtems/accele160/native_rom/rebuild_writer_offline.sh" "$out"
out=$(cd "$out" && pwd)
stock="$repo/artifacts/current/accele160-ram-admit-20261017/ram-admit/preflash-0/data.bin"
installed="$repo/host/accele160/ram_admit/candidate.bin"
python3 "$repo/rtems/accele160/native_rom/pack.py" \
  "$stock" "$out/stage2.bin" "$out/rtems.bin" \
  "$out/candidate-10112500320.bin" > "$out/pack-10112500320.json"
python3 - "$stock" "$installed" "$out/candidate-10112500320.bin" "$out/current-card-review.json" <<'PY'
import hashlib
import json
from pathlib import Path
import sys

stock_path, installed_path, image_path, review_path = map(Path, sys.argv[1:])
stock, installed, image = (p.read_bytes() for p in
                           (stock_path, installed_path, image_path))
digest = lambda data: hashlib.sha256(data).hexdigest()
expected = {
    "stock": "93faf91f553822665cd4125d90b1066370c4bca0da76af8336daf98bc2dae094",
    "installed": "1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd",
    "candidate": "b35b1e8312336532fae9175fdc3d0d0be7b80b14281434f42af1db294662c695",
}
for name, data in (("stock", stock), ("installed", installed),
                   ("candidate", image)):
    if len(data) != 1048576 or digest(data) != expected[name]:
        raise ValueError(f"{name} does not match the frozen card image")
if image[:0x40000] != installed[:0x40000] or image[0xc0000:] != installed[0xc0000:]:
    raise ValueError("candidate changes the installed image's protected regions")
if image[0xe0384:0xe038f] != b"10112500320":
    raise ValueError("candidate has another card's serial")
changed = [i for i, (before, after) in enumerate(zip(installed, image))
           if before != after]
record = {
    "serial": "10112500320",
    "stock_sha256": expected["stock"],
    "installed_sha256": expected["installed"],
    "candidate_sha256": expected["candidate"],
    "protected_regions_match_installed": True,
    "changed_bytes_from_installed": len(changed),
    "changed_64k_blocks_from_installed": sorted({i // 0x10000 for i in changed}),
    "hardware_tested": False,
    "safe_to_flash": False,
}
review_path.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
PY

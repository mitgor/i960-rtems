#!/usr/bin/env bash
# Rebuild the experimental writer from archived inputs. No card I/O.
set -euo pipefail
if [[ $# != 1 ]]; then
  echo "usage: $0 NEW_OUTPUT_DIR" >&2
  exit 2
fi
repo=$(cd "$(dirname "$0")/../../.." && pwd)
out=$1
if [[ -e $out ]]; then
  echo "output directory already exists: $out" >&2
  exit 2
fi
mkdir -p "$out"
out=$(cd "$out" && pwd)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
mkdir -p "$scratch/toolchain" "$scratch/rtems"
tar -xJf "$repo/artifacts/toolchain-20261011/linux-x86_64-installed.tar.xz" \
  -C "$scratch/toolchain"
tar -xJf "$repo/artifacts/rtems-20261011/final-net/generated-headers-libraries.tar.xz" \
  -C "$scratch/rtems"
tar -xzf "$repo/artifacts/rtems-20261011/sources/newlib-1.11.0.tar.gz" \
  -C "$scratch/rtems"
docker run --rm --platform linux/amd64 \
  -v "$repo:/work:ro" -v "$scratch:/scratch" \
  -w /work accele160-offline-python:22.04 bash -euo pipefail -c '
    mkdir -p /home/mit/i960
    ln -s /scratch/toolchain/tools /home/mit/i960/tools
    tc=/scratch/toolchain/tools/bin
    rt=/scratch/rtems/net
    flags=(-mrp -Os -fno-builtin -ffreestanding -D__rtems__ -DUSE_INLINES
      -I"$rt/include" -I/scratch/rtems/newlib-1.11.0/newlib/libc/include)
    "$tc/i960-coff-gcc" "${flags[@]}" -c /work/rtems/accele160/context.S -o "$rt/context.o"
    "$tc/i960-coff-gcc" "${flags[@]}" -c /work/rtems/accele160/libc.c -o "$rt/libc.o"
    ACCELE160_PCI_RELEASE=1 ACCELE160_PCI_HIDE_OPTION_ROM=1 \
    ACCELE160_OBSERVE_HOST_EVENTS=1 ACCELE160_UPDATER_STAGING=1 \
    ACCELE160_RAM_LOADER=1 ACCELE160_FLASH_WRITER_EXPERIMENTAL=1 \
      bash /work/rtems/accele160/native_rom/build.sh "$rt" "$tc" /scratch/build
  '
python3 "$repo/rtems/accele160/native_rom/pack.py" \
  "$repo/artifacts/current/accele160-guarded-20261016/rawflash-0/data.bin" \
  "$scratch/build/stage2.bin" "$scratch/build/rtems.bin" \
  "$out/candidate.bin" > "$out/pack-receipt.json"
cp "$scratch/build/stage2.bin" "$scratch/build/rtems.bin" \
   "$scratch/build/stage2.map" "$scratch/build/rtems.map" "$out/"
python3 - "$repo" "$out" <<'PY'
import hashlib
import json
from pathlib import Path
import subprocess
import sys
repo, p = map(Path, sys.argv[1:])
receipt = json.loads((p / "pack-receipt.json").read_text())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
for name, key in (("candidate.bin", "candidate_sha256"),
                  ("stage2.bin", "stage2_sha256"),
                  ("rtems.bin", "rtems_sha256")):
    digest = sha(p / name)
    if digest != receipt[key]:
        raise ValueError(f"{name} differs from pack receipt")
if receipt["safe_to_flash"] or receipt["physical_boot_tested"]:
    raise ValueError("offline build cannot be marked hardware qualified")
sources = [repo / "rtems/accele160/context.S", repo / "rtems/accele160/libc.c"]
for folder in ("rtems/accele160/native_rom", "rtems/accele160/ram_loader"):
    sources.extend(path for path in (repo / folder).iterdir()
                   if path.is_file() and path.suffix in (".c", ".h", ".S", ".ld"))
sources += [repo / "rtems/accele160/native_rom/build.sh",
            repo / "rtems/accele160/native_rom/pack.py",
            repo / "rtems/accele160/native_rom/rebuild_writer_offline.sh"]
archives = ["artifacts/toolchain-20261011/linux-x86_64-installed.tar.xz",
            "artifacts/rtems-20261011/final-net/generated-headers-libraries.tar.xz",
            "artifacts/rtems-20261011/sources/newlib-1.11.0.tar.gz",
            "artifacts/current/accele160-guarded-20261016/rawflash-0/data.bin"]
manifest = {"pack": receipt, "source_sha256": {
    str(path.relative_to(repo)): sha(path) for path in sorted(set(sources))},
    "archive_sha256": {name: sha(repo / name) for name in archives},
    "container_image": "accele160-offline-python:22.04",
    "container_image_id": subprocess.check_output(
        ["docker", "image", "inspect", "--format", "{{.Id}}",
         "accele160-offline-python:22.04"], text=True).strip(),
    "hardware_tested": False}
(p / "build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps(receipt, indent=2))
PY

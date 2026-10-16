#!/usr/bin/env python3
"""Offline, exact-image performance audit. Does not access a card or SSH.

Linear disassembly contains strings/data decoded as instructions. Only selected,
reviewed ranges are interpreted; byte matching is not a reachability proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import tarfile

ROOT = Path(__file__).resolve().parents[2]
FW = "21f6c1d898a533d7023a53893f03547ed61631016d1b247d3ecbb97b9403c195"
BOOT = "d10cca35861b66ef38c74de9b7409438b5a46ed3c3b238d5abfcc879d32bd85c"
RAW = "8afaebf954bbbf31bba42f1156c76237c3e632b071f6b400d3f17fbcd9d8baa5"
BUILD = "3e47178822b57a6b6c6a89b28d2003e7c3537c20720dbf4857c03af730121503"
DISASSEMBLY_HASHES = {
    "runtime": "240ed674b680a558bbddfdd88929e1c6e3da8213b271d9b71b5f37442c7a4bad",
    "bootstrap": "1ae4c9ee58f587bf624839e40b38cd5dc4356a21fc360fb933165d45d22d6d5f",
    "bootblock": "e50ec0ae3f89749e4cb44bf6a47e1cadc0031c4bcc2d341af2714523d57893a5",
}
PAGES_ARCHIVE = "5fa24676f84d6cd69b22c025014b47c0338477b29c09204cc8b3286b666bbe4f"
ROW = re.compile(r"^([0-9a-f]{8}):\s*((?:[0-9a-f]{2}\s+){3}[0-9a-f]{2})\s*(.*)$")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked_rows(text, blob, base):
    rows = {}
    for line in text.splitlines():
        m = ROW.match(line)
        if not m:
            continue
        pc = int(m[1], 16)
        offset = pc - base
        require(0 <= offset <= len(blob) - 4, f"out-of-image row {pc:08x}")
        require(bytes.fromhex(m[2]) == blob[offset:offset + 4], f"byte mismatch {pc:08x}")
        require(pc not in rows, f"duplicate row {pc:08x}")
        rows[pc] = (line, m[3].strip())
    require(bool(rows), "no disassembly rows")
    return rows


def decode_dram(values):
    dbcr, base, read, write, refresh, parity = values
    arrangement = (dbcr >> 3) & 31
    # Report field encodings, not physically fitted RAM or measured throughput.
    return {
        "registers_hex": [f"{v:08x}" for v in values],
        "enabled": bool(dbcr & 1),
        "arrangement_field": arrangement,
        "edo_two_banks": arrangement == 9,
        "bank_leaf_mib_encoding": [1, 4, 16, 64][(dbcr >> 1) & 3],
        "base_hex": f"{base:08x}",
        "read_fields": {"ras_to_cas": (read >> 16) & 3, "cas_width": (read >> 8) & 3, "extra_recovery": read & 3},
        "write_fields": {"ras_to_cas": (write >> 16) & 3, "cas_width": (write >> 8) & 3, "extra_recovery": write & 3},
        "refresh_enabled": not bool(refresh & (1 << 16)),
        "refresh_sclk_cycles": refresh & 1023,
        "parity_enabled": bool(parity & 1),
        "parity_odd": bool(parity & 2),
        "installed_capacity_from_encoding": False,
    }


def diagnostic_pages(records):
    pages = {}
    for record in records:
        require(len(record) == 160, "unexpected archived snapshot length")
        require(record[150] == 0x32484343, "unexpected decode-page magic")
        page = record[151]
        require(page not in pages, "duplicate decode page")
        pages[page] = record[152:160]
    require(3 in pages and 4 in pages, "missing DRAM/positive-control page")
    require(pages[4][:4] == [0xa5a5a5a5, 0x5a5a5a5a, 0xa5a5, 0x5a5a], "positive controls failed")
    return pages


def audit(root, out):
    vendor = root / "artifacts/vendor-fujitsu/4.07-0-29"
    snapshot = root / "artifacts/private-dumps/snapshot-fresh-20261010T125336Z"
    inputs = [
        ("runtime", vendor / "unpacked.bin", vendor / "unpacked.dis", 0xc0010000, FW),
        ("bootstrap", vendor / "Fgj40729.img.raw", vendor / "bootstrap.dis", 0xfefc8000, RAW),
        ("bootblock", snapshot / "bootblock.raw", snapshot / "bootblock.dis", 0xfeffc000, BOOT),
    ]
    decoded, identities = {}, {}
    for name, binary, disassembly, base, expected in inputs:
        blob = binary.read_bytes()
        require(sha(blob) == expected, f"wrong {name} image")
        dis_blob = disassembly.read_bytes()
        require(sha(dis_blob) == DISASSEMBLY_HASHES[name], f"wrong {name} disassembly")
        rows = checked_rows(dis_blob.decode(), blob, base)
        decoded[name] = rows
        identities[name] = {"sha256": expected, "disassembly_sha256": sha(dis_blob), "bytes": len(blob), "checked_rows": len(rows)}
    require((vendor / "unpacked.bin").read_bytes() == (snapshot / "firmware-unpacked.bin").read_bytes(), "installed runtime differs")
    ranges = [
        ("boot-memory-cache", "bootblock", 0xfeffc428, 0xfeffc514),
        ("bootstrap-cache-clear-copy", "bootstrap", 0xfefc80fc, 0xfefc81bc),
        ("board-internal-dispatch", "bootstrap", 0xfefcc1f0, 0xfefcc310),
        ("vendor-cpu-xor", "bootstrap", 0xfefcc540, 0xfefcc660),
        ("runtime-dram-sizing", "runtime", 0xc004fc40, 0xc004fdf0),
        ("vendor-fill-refresh-byte-copy", "runtime", 0xc004ca68, 0xc004cb04),
        ("vendor-dma-poll", "runtime", 0xc004c8b8, 0xc004c9a8),
        ("external-cache-submit", "runtime", 0xc004e940, 0xc004eaa0),
    ]
    out.mkdir(parents=True, exist_ok=True)
    for name, image, lo, hi in ranges:
        lines = [line for pc, (line, _) in decoded[image].items() if lo <= pc < hi]
        require(bool(lines), f"empty range {name}")
        (out / (name + ".txt")).write_text("\n".join(lines) + "\n")
    values = []
    for producer, store, expected, address in [
        (0xfeffc4c8, 0xfeffc4cc, 0xb43, 0x151c),
        (0xfeffc4d4, 0xfeffc4dc, 0xc0000000, 0x1520),
        (0xfeffc4e4, 0xfeffc4e8, 0, 0x1524),
        (0xfeffc4f0, 0xfeffc4f4, 0, 0x1528),
        (0xfeffc4fc, 0xfeffc500, 0xcc, 0x152c),
        (0xfeffc508, 0xfeffc50c, 1, 0x1530),
    ]:
        rows = decoded["bootblock"]
        require(rows[producer][1] == (f"mov\t{expected},g0" if expected <= 1 else f"lda\t0x{expected:x},g0"), "unexpected DRAM value producer")
        require(rows[store][1] == f"st\tg0,0x{address:x}", "unexpected DRAM store")
        values.append(expected)
    archive = root / "artifacts/rtems-residentnet-decode-20261011/residentnet-decode-v3.tar.xz"
    require(sha(archive.read_bytes()) == PAGES_ARCHIVE, "wrong register capture archive")
    with tarfile.open(archive) as t:
        member = "residentnet-decode-bounded3/cache-pages.json"
        page_blob = t.extractfile(member).read()
    pages = diagnostic_pages(json.loads(page_blob))
    (out / "archived-register-pages.json").write_text(json.dumps(pages, indent=2) + "\n")
    build_archive = root / "artifacts/doom-pingpong-20261015/build-evidence-v1.tar.gz"
    require(sha(build_archive.read_bytes()) == BUILD, "wrong accepted build archive")
    with tarfile.open(build_archive) as t:
        kernel = t.extractfile("build/residentnet/kernel.dis").read().decode()
        binary = t.extractfile("build/residentnet/kernel.bin").read()
    # Use the linked entry address from the disassembly, not a guessed load base.
    base_match = re.search(r"^([0-9a-f]{8}) <_start>:", kernel, re.M)
    require(base_match is not None, "kernel entry missing")
    kernel_rows = checked_rows(kernel, binary, int(base_match[1], 16))
    copy_lines = [line for pc, (line, _) in kernel_rows.items() if 0xc0f32ae0 <= pc < 0xc0f32b70]
    require(any("ldob\t" in line for line in copy_lines) and any("stob\t" in line for line in copy_lines), "accepted byte routines missing")
    (out / "accepted-kernel-memory-routines.txt").write_text("\n".join(copy_lines) + "\n")
    callsites = {}
    for target in (0xc004cac0, 0xc004ca68, 0xc004ca7c):
        callsites[f"{target:08x}"] = [f"{pc:08x}" for pc, (_, op) in decoded["runtime"].items() if re.match(rf"(?:call|bal)\s+0x{target:x}$", op)]
    source_paths = ["rtems/exclusive/runtime.c", "rtems/irq/libc.c", "rtems/residentnet/cache_probe.h", "rtems/residentnet/upload.c", "rtems/dma/README.md"]
    source_hashes = {p: sha((root / p).read_bytes()) for p in source_paths}
    result = {
        "scope": "DAC960PG i960RP, installed 4.07-0-29; not photographed PRO/100 board",
        "identities": identities,
        "boot_dram": decode_dram(values),
        "archived_20261011_live_dram": decode_dram(pages[3][:6]),
        "archived_dcache_status_hex": f"{pages[4][6]:08x}",
        "archived_dcache_enabled": bool(pages[4][6] & 1),
        "current_live_cache_templates_measured": False,
        "archived_pages_sha256": sha(page_blob),
        "archived_container_sha256": sha(archive.read_bytes()),
        "accepted_kernel_sha256": sha(binary),
        "accepted_kernel_checked_rows": len(kernel_rows),
        "accepted_build_archive_sha256": BUILD,
        "linear_direct_call_candidates_not_exhaustive": callsites,
        "current_source_hashes": source_hashes,
        "hardware_accessed": False,
        "speedup_measured_by_this_audit": False,
        "limitations": ["linear decode is not reachability", "old register captures are not current Doom state", "zero added waits are not zero bus latency", "no SRAM/DRAM timing or cache-policy writes", "no exact IRQ cost attribution"],
    }
    (out / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = audit(args.root, args.out)
    print(json.dumps({"byte_checked_rows": {k: v["checked_rows"] for k, v in result["identities"].items()}, "dcache_enabled_in_archive": result["archived_dcache_enabled"], "hardware_accessed": False}))

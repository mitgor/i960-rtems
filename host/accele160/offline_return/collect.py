#!/usr/bin/env python3
"""Collect AcceleRAID 160 host state; optionally repeat the guarded READIMAGE."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

SPARE = "0000:37:04.1"
ORIGINAL = "0000:37:09.1"
EXPECTED_IDS = ("0x1069", "0x0050", "0x1069", "0x0054")
STOCK_SHA = "0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943"
FLASH_BYTES = 1048576
READER = Path(__file__).resolve().parents[1] / "readimage/read_spare.py"


def read_text(path):
    try:
        return path.read_text(errors="replace").strip()
    except (OSError, UnicodeError):
        return None


def pci_snapshot(sysfs, bdf):
    device = sysfs / "bus/pci/devices" / bdf
    keys = ("vendor", "device", "subsystem_vendor", "subsystem_device",
            "revision", "class", "enable")
    data = {key: read_text(device / key) for key in keys}
    data["present"] = device.exists()
    driver_link = device / "driver"
    data["driver"] = driver_link.resolve().name if driver_link.is_symlink() else None
    data["block_paths"] = sorted(str(p.relative_to(device)) for p in
                                 device.glob("host*/target*/*/block/*"))
    return data


def capture_pci_static_files(sysfs, bdf, output):
    """Save sysfs PCI configuration and resource metadata without enable writes."""
    device = sysfs / "bus/pci/devices" / bdf
    result = {}
    for name in ("config", "resource"):
        source = device / name
        target = output / f"pci-{bdf}-{name}{'.bin' if name == 'config' else '.txt'}"
        try:
            if name == "config":
                with source.open("rb") as handle:
                    data = handle.read(256)
                target.write_bytes(data)
            else:
                data = source.read_bytes()
                target.write_bytes(data)
            result[name] = {"file": target.name, "bytes": len(data),
                            "sha256": hashlib.sha256(data).hexdigest()}
            if name == "config" and len(data) >= 0x34:
                command = int.from_bytes(data[4:6], "little")
                rom_bar = int.from_bytes(data[0x30:0x34], "little")
                result["pci_command_now"] = {
                    "raw": f"0x{command:04x}",
                    "memory_space_enabled": bool(command & 0x2),
                    "bus_master_enabled": bool(command & 0x4),
                }
                result["expansion_rom_bar_now"] = {
                    "raw": f"0x{rom_bar:08x}",
                    "decode_enabled": bool(rom_bar & 1),
                }
            if name == "resource":
                rows = data.decode("ascii", errors="replace").splitlines()
                result["rom_resource_row"] = rows[6] if len(rows) > 6 else None
        except OSError as exc:
            result[name] = {"error": str(exc)}
    return result


def command_capture(argv, output):
    try:
        result = subprocess.run(argv, capture_output=True, text=True,
                                errors="replace", timeout=30, check=False)
        output.write_text(result.stdout +
                          ("\n[stderr]\n" + result.stderr if result.stderr else ""))
        return {"argv": argv, "exit_code": result.returncode,
                "output_file": output.name}
    except (OSError, subprocess.TimeoutExpired) as exc:
        output.write_text(f"Unavailable: {exc}\n")
        return {"argv": argv, "error": str(exc), "output_file": output.name}


def validate_target(snapshot, sysfs):
    spare = snapshot["pci"][SPARE]
    original = snapshot["pci"][ORIGINAL]
    if tuple(spare[k] for k in EXPECTED_KEYS) != EXPECTED_IDS:
        raise RuntimeError("Slot 6 spare PCI identity changed; no READIMAGE")
    if tuple(original[k] for k in EXPECTED_KEYS) != EXPECTED_IDS:
        raise RuntimeError("Slot 5 original PCI identity changed; no READIMAGE")
    if spare["driver"] != "myrsread" or original["driver"] is not None:
        raise RuntimeError("expected spare-only myrsread binding is absent")
    if spare["block_paths"] or original["block_paths"]:
        raise RuntimeError("a controller exposes storage; no READIMAGE")
    if read_text(sysfs / "module/myrsread/parameters/read_bdf") != SPARE:
        raise RuntimeError("myrsread is not BDF-limited to Slot 6")


EXPECTED_KEYS = ("vendor", "device", "subsystem_vendor", "subsystem_device")


def verify_read(directory):
    data_path = directory / "data.bin"
    result = json.loads((directory / "result.json").read_text())
    data = data_path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if len(data) != FLASH_BYTES or result["bytes"] != FLASH_BYTES:
        raise RuntimeError(f"{directory}: incomplete flash read")
    if result["sha256"] != digest:
        raise RuntimeError(f"{directory}: result and data hash differ")
    status = dict(part.split("=", 1) for part in
                  (directory / "status.txt").read_text().split()
                  if "=" in part)
    for key, value in {"done": "1", "status": "0", "residual": "0",
                       "selector": "9", "length": str(FLASH_BYTES),
                       "guard_changes": "0", "released": "0"}.items():
        if status.get(key) != value:
            raise RuntimeError(f"{directory}: unsafe READIMAGE status {key}")
    return digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sysfs", type=Path, default=Path("/sys"),
                        help="test override; live runs use /sys")
    parser.add_argument("--execute-flash-reads", action="store_true",
                        help="explicitly run two guarded READIMAGE captures")
    parser.add_argument("--reader-module", type=Path,
                        help="previously tested rawreader.ko; required for reads")
    args = parser.parse_args()
    if args.execute_flash_reads and (args.reader_module is None or
                                     args.sysfs != Path("/sys")):
        parser.error("live reads require --reader-module and the real /sys")
    if args.reader_module and not args.execute_flash_reads:
        parser.error("--reader-module is only used with --execute-flash-reads")
    args.output.mkdir(parents=True, exist_ok=False)
    snapshot = {
        "boot_id": read_text(Path("/proc/sys/kernel/random/boot_id")),
        "uname": platform.uname()._asdict(),
        "pci": {bdf: pci_snapshot(args.sysfs, bdf) for bdf in
                ("0000:37:04.0", SPARE, "0000:37:09.0", ORIGINAL)},
        "readimage_executed": False,
        "bios_option_rom_setting_observable_from_linux": False,
    }
    snapshot["pci_static_files"] = {
        bdf: capture_pci_static_files(args.sysfs, bdf, args.output)
        for bdf in ("0000:37:04.0", SPARE, "0000:37:09.0", ORIGINAL)
    }
    commands = [
        (["lspci", "-Dnn"], "lspci-all.txt"),
        *[( ["lspci", "-Dvv", "-s", bdf], f"lspci-{bdf}.txt") for bdf in
          ("0000:37:04.0", SPARE, "0000:37:09.0", ORIGINAL)],
        (["dmesg"], "dmesg.txt"),
        (["dmidecode", "-s", "bios-version"], "bios-version.txt"),
    ]
    snapshot["commands"] = [command_capture(cmd, args.output / file)
                            for cmd, file in commands]
    plan = {
        "target_bdf": SPARE, "untouched_original_bdf": ORIGINAL,
        "stock_sha256": STOCK_SHA, "bytes_per_read": FLASH_BYTES,
        "reader": str(READER), "two_independent_reads_required": True,
        "required_preconditions": [
            "stock spare in Slot 6 and original in Slot 5",
            "both 1069:0050 subsystem 1069:0054; original unbound",
            "myrsread bound only to Slot 6 and read_bdf pinned to it",
            "neither card exposes storage",
            "reviewed driver and rawreader module hashes accepted by read_spare.py",
        ],
        "manual_bios_record": [
            "HP F10 Slot 6 Option ROM Download",
            "Mylex boot BIOS setting for each card",
            "SATA RAID Option ROM Download",
        ],
        "note": "Linux expansion-ROM decode state does not prove HP F10 setting.",
    }
    (args.output / "flash-read-plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    (args.output / "inventory.json").write_text(json.dumps(snapshot, indent=2) + "\n")
    if not args.execute_flash_reads:
        print(args.output / "inventory.json")
        return
    if os.geteuid() != 0:
        raise RuntimeError("guarded READIMAGE requires root")
    validate_target(snapshot, args.sysfs)
    digests = []
    for n in (0, 1):
        target = args.output / f"rawflash-{n}"
        subprocess.run([sys.executable, str(READER), "--module",
                        str(args.reader_module.resolve()), "--out", str(target)],
                       check=True)
        digest = verify_read(target)
        if digest != STOCK_SHA:
            raise RuntimeError(f"read {n} differs from pinned second-spare stock")
        digests.append(digest)
    if digests[0] != digests[1]:
        raise RuntimeError("two full flash reads differ")
    (args.output / "flash-read-verification.json").write_text(json.dumps({
        "gate": "PASS", "sha256": digests[0], "reads": 2,
        "card": SPARE, "reader_checked_peer_selection_before_and_after": True,
    }, indent=2) + "\n")
    snapshot["readimage_executed"] = True
    (args.output / "inventory.json").write_text(json.dumps(snapshot, indent=2) + "\n")
    print(args.output / "flash-read-verification.json")


if __name__ == "__main__":
    main()

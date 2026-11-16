#!/usr/bin/env python3
"""Offline review of a read-only AcceleRAID return-to-hardware inventory."""
import argparse
import hashlib
import json
from pathlib import Path

from collect import EXPECTED_IDS, EXPECTED_KEYS, ORIGINAL, SPARE


def review(directory):
    inventory = json.loads((directory / "inventory.json").read_text())
    findings = []
    pci = inventory.get("pci", {})
    for bdf in ("0000:37:04.0", SPARE, "0000:37:09.0", ORIGINAL):
        row = pci.get(bdf, {})
        if not row.get("present"):
            findings.append(f"{bdf}: missing PCI function")
        meta = inventory.get("pci_static_files", {}).get(bdf, {})
        for key in ("config", "resource"):
            record = meta.get(key, {})
            if "file" not in record:
                findings.append(f"{bdf}: {key} capture unavailable")
                continue
            expected_file = f"pci-{bdf}-{key}{'.bin' if key == 'config' else '.txt'}"
            if record["file"] != expected_file:
                findings.append(f"{bdf}: {key} capture filename changed")
                continue
            try:
                data = (directory / expected_file).read_bytes()
            except OSError as exc:
                findings.append(f"{bdf}: {key} capture unreadable: {exc}")
                continue
            if (len(data) != record.get("bytes") or
                    hashlib.sha256(data).hexdigest() != record.get("sha256")):
                findings.append(f"{bdf}: {key} capture changed after inventory")
            if key == "config" and len(data) < 64:
                findings.append(f"{bdf}: PCI config capture is shorter than 64 bytes")
            if key == "resource" and len(data.splitlines()) < 7:
                findings.append(f"{bdf}: ROM resource row is missing")
    for bdf in (SPARE, ORIGINAL):
        row = pci.get(bdf, {})
        if tuple(row.get(k) for k in EXPECTED_KEYS) != EXPECTED_IDS:
            findings.append(f"{bdf}: RAID PCI identity differs from pinned 1069:0050/1069:0054")
        config_file = inventory.get("pci_static_files", {}).get(bdf, {}).get("config", {}).get("file")
        if config_file == f"pci-{bdf}-config.bin" and (directory / config_file).exists():
            data = (directory / config_file).read_bytes()
            if len(data) >= 64 and tuple(int.from_bytes(data[i:i + 2], "little")
                                          for i in (0, 2, 0x2c, 0x2e)) != (0x1069, 0x0050, 0x1069, 0x0054):
                findings.append(f"{bdf}: raw PCI config identity differs from sysfs")
        if row.get("block_paths"):
            findings.append(f"{bdf}: storage is exposed")
    if inventory.get("readimage_executed"):
        findings.append("inventory includes READIMAGE; review its separate verification receipt")
    if not inventory.get("boot_id"):
        findings.append("boot ID missing")
    lspci = next((row for row in inventory.get("commands", [])
                  if row.get("output_file") == "lspci-all.txt"), None)
    if not lspci or lspci.get("exit_code") != 0:
        findings.append("full lspci inventory missing or failed")
    return {
        "gate": "PASS" if not findings else "REVIEW_REQUIRED",
        "boot_id": inventory.get("boot_id"),
        "spare_bdf": SPARE,
        "original_bdf": ORIGINAL,
        "findings": findings,
        "manual_slot_and_bios_photo_required": True,
        "mu_registers_observed": False,
        "option_rom_executed_during_post_observed": False,
        "readimage_approved_by_this_review": False,
        "native_firmware_cold_boot_tested": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = review(args.capture)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print("inventory_review=" + result["gate"])


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Read native-ROM progress through the 80303 PCI BAR; no PCI writes."""
import argparse
import hashlib
import json
import mmap
from pathlib import Path
import struct

VENDOR = 0x1069
DEVICE = 0x0050
SUBVENDOR = 0x1069
SUBDEVICE = 0x0054
BAR_BYTES = 0x2000
LOCAL_BASE = 0xc0000000
STATUS_BAR_OFFSET = 0x1f00
WORDS = 25
REPLY_WORDS = 28
DMA_WORDS = 30
TWO_REQUEST_WORDS = 33
HST1_WORDS = 20
HST0_WORDS = 16
LEGACY_WORDS = 9


def check_config(config, resource):
    if len(config) < 0x48:
        raise ValueError("short PCI configuration space")
    identity = struct.unpack_from("<4H", config, 0)
    vendor, device = identity[:2]
    subvendor, subdevice = struct.unpack_from("<2H", config, 0x2c)
    if (vendor, device, subvendor, subdevice) != (VENDOR, DEVICE, SUBVENDOR, SUBDEVICE):
        raise ValueError("unexpected card PCI identity")
    pialr, piatvr = struct.unpack_from("<2I", config, 0x40)
    if pialr != 0xffffe000 or piatvr != LOCAL_BASE:
        raise ValueError("inbound BAR mapping differs from the observed stock layout")
    lines = resource.splitlines()
    if not lines:
        raise ValueError("missing BAR resource")
    start, end, _flags = (int(x, 16) for x in lines[0].split()[:3])
    if end - start + 1 != BAR_BYTES:
        raise ValueError("BAR0 is not 8 KiB")
    return {"vendor": f"{vendor:04x}", "device": f"{device:04x}",
            "subvendor": f"{subvendor:04x}", "subdevice": f"{subdevice:04x}",
            "pialr": f"{pialr:08x}", "piatvr": f"{piatvr:08x}",
            "bar0_start": f"{start:x}"}


def decode(words):
    if len(words) not in (LEGACY_WORDS, HST0_WORDS, HST1_WORDS, WORDS,
                          REPLY_WORDS, DMA_WORDS, TWO_REQUEST_WORDS):
        raise ValueError("unsupported native-ROM status word count")
    result = {
        "stage2_entered": words[0] == 0x32544753,
        "stage2_state": f"0x{words[1]:08x}",
        "stage2_copy_ok": words[1] == 0x2000,
        "copied_bytes_or_fault_digest": words[2],
        "matching_fnv": f"0x{words[3]:08x}",
        "worker_count": words[4], "init_count": words[5],
        "worker_done": words[6],
        "rtems_result": ("PASS" if words[7] == 0x50415353 else
                         "FAIL" if words[7] == 0x4641494c else
                         "ENTERED" if words[7] == 0x5254454d else "UNKNOWN"),
        "park_code": f"0x{words[8]:08x}",
        "raw_words": [f"0x{x:08x}" for x in words],
    }
    if len(words) >= HST0_WORDS and words[9] == 0x30545348:
        flags = words[15]
        result["host_startup"] = {
            "bridge_pci_command": f"0x{words[10]:08x}",
            "raid_pci_command": f"0x{words[11]:08x}",
            "inbound_doorbell": f"0x{words[12]:08x}",
            "inbound_status": f"0x{words[13]:08x}",
            "inbound_mask": f"0x{words[14]:08x}",
            "bridge_pci_ready": bool(flags & 1),
            "raid_pci_ready": bool(flags & 2),
            "boot_doorbell_seen": bool(flags & 4),
            "raw_ready_flags": f"0x{flags:08x}",
        }
    else:
        result["host_startup"] = None
    if len(words) >= HST1_WORDS and words[19] == 0x31545348:
        sequence = words[16]
        if sequence & 1:
            raise ValueError("HST1 snapshot is being updated")
        result["host_monitor"] = {
            "sequence": sequence,
            "mailbox_pointer": f"0x{words[18]:08x}{words[17]:08x}",
        }
    else:
        result["host_monitor"] = None
    if len(words) >= WORDS and words[20] == 0x3058424d:
        result["mailbox_ingress"] = {
            "state": f"0x{words[21]:08x}",
            "command_id": words[22],
            "output_bus_address": f"0x{words[23]:08x}",
            "request_fnv32": f"0x{words[24]:08x}",
        }
    else:
        result["mailbox_ingress"] = None
    if len(words) >= REPLY_WORDS and words[25] == 0x304c5052:
        result["local_reply"] = {
            "state": f"0x{words[26]:08x}",
            "fnv32": f"0x{words[27]:08x}",
        }
    else:
        result["local_reply"] = None
    if len(words) >= DMA_WORDS and words[28] == 0x31414d44:
        result["dma1_reply"] = {"state": f"0x{words[29]:08x}"}
    else:
        result["dma1_reply"] = None
    if len(words) == TWO_REQUEST_WORDS and words[30] in (
            0x32514552, 0x33514552, 0x34514552, 0x35514552):
        result["request_sequence"] = {
            "limit": {0x32514552: 2, 0x33514552: 3,
                      0x34514552: 4, 0x35514552: 5}[words[30]],
            "completed_count": words[31],
            "last_ioctl": f"0x{words[32]:02x}",
        }
    else:
        result["request_sequence"] = None
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bdf", required=True, help="explicit PCI BDF of the test card")
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if "/" in a.bdf or ".." in a.bdf:
        raise ValueError("invalid BDF")
    dev = Path("/sys/bus/pci/devices") / a.bdf
    config = (dev / "config").read_bytes()
    identity = check_config(config, (dev / "resource").read_text())
    with (dev / "resource0").open("rb", buffering=0) as f:
        with mmap.mmap(f.fileno(), BAR_BYTES, access=mmap.ACCESS_READ) as bar:
            first = bar[STATUS_BAR_OFFSET:STATUS_BAR_OFFSET + WORDS * 4]
            second = bar[STATUS_BAR_OFFSET:STATUS_BAR_OFFSET + WORDS * 4]
    if first != second:
        raise ValueError("status changed during two reads; retry without claiming a result")
    record = {"bdf": a.bdf, "identity": identity,
              "snapshot_sha256": hashlib.sha256(first).hexdigest(),
              **decode(struct.unpack("<25I", first))}
    if a.out.exists():
        raise FileExistsError(a.out)
    a.out.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()

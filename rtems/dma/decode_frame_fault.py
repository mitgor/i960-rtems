#!/usr/bin/env python3
"""Decode failure-only DMA evidence; never substitutes for successful replay."""
import argparse
import json
import struct
from pathlib import Path

STAGES = {
    0: "no phase marker", 1: "source CRC started", 2: "source CRC complete",
    3: "descriptor published", 4: "bus master enable requested",
    5: "bus master enable read back", 6: "descriptor address read back",
    7: "channel enable read back; polling", 8: "poll loop exited",
    9: "channel disable requested", 10: "channel disable read back",
    11: "bus master disable read back", 12: "post-DMA CRC complete",
    13: "terminal publication pending or complete",
}

def decode(data):
    if len(data) != 400:
        raise ValueError("expected exactly 400 bytes")
    w = struct.unpack("<100I", data)
    if w[0] != 0x31464446 or not 0 < w[1] <= 65535:
        raise ValueError("invalid capture magic/epoch")
    if w[2] > 96 or w[3] > 4 or (w[3] == 0 and w[2] != 96):
        raise ValueError("invalid diagnostic completion")
    t = w[4:4+w[2]]
    result = dict(epoch=w[1], captured_words=w[2], diagnostic_rc=w[3],
                  accepted_transfer=False, words=[f"0x{x:08x}" for x in t])
    if len(t) < 2 or t[0] != 0x31464d4e or t[1] != w[1]:
        result["terminal_identity_verified"] = False
        return result
    result["terminal_identity_verified"] = True
    if len(t) >= 8:
        result.update(trap_kind=t[2], frame_pointer=f"0x{t[3]:08x}",
                      hardware_record=[f"0x{x:08x}" for x in t[4:8]])
    if len(t) >= 64 and t[48] == 0x31504548:
        result["heap"] = dict(ready=t[51], error=t[52], valid=t[59],
                              extra_guard_mask=t[62])
        result["isolation"] = dict(exception_owner_valid=t[16],
                                   scsi_verified=t[17], exception_guards_valid=t[18])
    if len(t) >= 88:
        d = t[64:]
        result["dma"] = dict(phase=d[1], generation=d[2], error=d[13],
             stage=d[16], stage_description=STAGES.get(d[16], "unknown"),
             poll_iteration=d[17], csr=f"0x{d[18]:08x}",
             dar=f"0x{d[19]:08x}", ndar=f"0x{d[20]:08x}",
             bcr=d[21], ccr=f"0x{d[22]:08x}", pci_command=f"0x{d[23]:04x}")
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    args = parser.parse_args()
    print(json.dumps(decode(args.capture.read_bytes()), indent=2))

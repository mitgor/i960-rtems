#!/usr/bin/env python3
"""Pin the reviewed no-erase FI1 identification payload and host launcher."""
from pathlib import Path
import hashlib
import json
import re
import sys

HERE = Path(__file__).resolve().parent
SHA = "400a269688b991ddfefc8fafef6d41c5b900d13f992da3b794131c85d63f6634"


def audit(disassembly: Path) -> dict:
    image = (HERE / "id-probe.bin").read_bytes()
    lines = disassembly.read_text().splitlines()
    instructions = [line.split("\t", 2)[2].strip() for line in lines
                    if re.match(r"^c071[0-9a-f]{4}:", line) and
                    line.count("\t") >= 2]
    assert len(image) == 200 and hashlib.sha256(image).hexdigest() == SHA
    assert instructions.count("stob\tr4,(r8)") == 3
    assert instructions.count("syncf") == 4
    assert instructions.count("lda\t0xff,r4") == 2
    assert instructions.count("lda\t0x90,r4") == 1
    assert sum(item.startswith("lda\tfef00000 ") and item.endswith(",r8")
               for item in instructions) == 1
    assert sum("c0710100" in item for item in instructions) == 1
    assert not any("e0500000" in item for item in instructions)
    assert not any(re.search(r"\b(?:erase|program|lock)\b", item, re.I)
                   for item in instructions)
    return {"payload_sha256": SHA, "bytes": len(image),
            "flash_command_values": ["0xff", "0x90", "0xff"],
            "flash_command_stores": 3, "board_gate_stores": 0,
            "erase_program_commands": 0, "result_record": "0xc0710100"}


if __name__ == "__main__":
    print(json.dumps(audit(Path(sys.argv[1])), indent=2))

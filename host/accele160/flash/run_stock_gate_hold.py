#!/usr/bin/env python3
"""One-shot stock-RAM VPP gate hold: no flash command, for a multimeter.

Sets board-control bit 3 as the stock writer does, holds it about 8 s, and
clears it. Same preflight, arguments and restore as run_stock_flash_id.py:
cold power cycle, two fresh same-boot full stock reads, one 0x8f call per boot.
Have the meter on the flash VPP pin before starting; the hold begins within a
second of launch.
"""

import run_stock_flash_id as base

PAYLOAD_SHA = "83d2a2bc04f23ca8489686f3f23fc23807f10dfd8b2d10c9bbb475acec73a7bb"
MAGIC = 0x31444847  # GHD1
POLLS = 16000000
GATE = 0x08
FIELDS = ("magic", "context", "shadow_before", "read_before", "read_held",
          "read_after", "shadow_after", "polls", "code")


def decode(words):
    record = dict(zip(FIELDS, words))
    held = (record["magic"] == MAGIC and record["code"] == 0 and
            record["polls"] == POLLS and
            not (record["shadow_before"] | record["shadow_after"]) & GATE)
    # True only if the latch showed bit 3 while set and not otherwise; the
    # native writer's gate check depends on this.
    reads_back = bool(held and record["read_held"] & GATE and
                      not (record["read_before"] | record["read_after"]) & GATE)
    return {"gate_hold": record, "held": held,
            "register_reads_back_bit3": reads_back}, held


if __name__ == "__main__":
    base.main(PAYLOAD_SHA, timeout=60, decode=decode, description=__doc__)

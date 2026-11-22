#!/usr/bin/env python3
"""Explicitly abandon an acknowledged UPD1 RAM staging session.

No flash command is sent. An unacknowledged command or partial flash-write
state is deliberately left untouched for investigation.
"""
import argparse
import fcntl
import json
from pathlib import Path

from stage_native_update import NativeStage, PEER, TARGET
from card_select import require_unbound_or_absent, select


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--live", action="store_true", required=True)
    args = parser.parse_args()
    if args.receipt.exists():
        raise FileExistsError(args.receipt)
    with open("/run/lock/i960-loadrun.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        card = select(TARGET, "accele160")
        peer = require_unbound_or_absent(PEER, "accele160")
        if card["driver"] is not None or peer["present"]:
            raise RuntimeError("single unbound Slot 5 card required")
        with NativeStage(TARGET, require_idle=False) as stage:
            before = {"sequence": stage.sequence,
                      "state": stage.read_word(8),
                      "next_chunk": stage.read_word(9)}
            stage.abort()
            after = {"sequence": stage.sequence,
                     "state": stage.read_word(8),
                     "next_chunk": stage.read_word(9)}
    args.receipt.write_text(json.dumps({"mode": "live-ram-session-aborted",
        "card": card, "before": before, "after": after,
        "flash_programmed": False}, indent=2) + "\n")
    print(args.receipt)


if __name__ == "__main__":
    main()

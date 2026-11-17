#!/usr/bin/env python3
"""Run two full flash images through the same bounded controller model.

This is a fail-closed diagnostic. A common early trace is not a boot pass.
"""
import argparse
import subprocess
import sys
from pathlib import Path


def run(binary: Path, image: Path, cycles: int, strict: bool,
        board_id: int | None) -> tuple[list[str], str]:
    command = [str(binary), str(image), str(cycles)]
    if strict:
        command.append("--strict")
    if board_id is not None:
        command.append(f"--board-id={board_id}")
    result = subprocess.run(
        command,
        text=True, capture_output=True, timeout=45, check=False,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(f"{image}: runner failed: {result.stderr.strip()}")
    lines = result.stdout.splitlines()
    if not lines or not lines[-1].startswith("stop "):
        raise RuntimeError(f"{image}: no bounded terminal result")
    return lines, lines[-1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stock", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--cycles", type=int, default=1500000)
    parser.add_argument("--explore", action="store_true",
                        help="continue past unmodeled peripheral accesses for diagnostic traces")
    parser.add_argument("--board-id", type=int,
                        help="hypothetical low-five-bit board selector, exploratory only")
    parser.add_argument("--binary", type=Path,
                        default=Path(__file__).parent / "build/accele160-emu")
    args = parser.parse_args()
    if not 1 <= args.cycles <= 10000000:
        parser.error("cycles must be 1..10000000")
    if args.board_id is not None and (not args.explore or not 0 <= args.board_id <= 31):
        parser.error("board-id requires --explore and a value from 0..31")
    stock, stock_stop = run(args.binary.resolve(), args.stock.resolve(), args.cycles,
                            not args.explore, args.board_id)
    candidate, candidate_stop = run(args.binary.resolve(), args.candidate.resolve(),
                                    args.cycles, not args.explore, args.board_id)
    common = 0
    for a, b in zip(stock, candidate):
        if a != b:
            break
        common += 1
    print(f"common_lines={common}")
    print(f"stock: {stock_stop}")
    print(f"candidate: {candidate_stop}")
    for label, lines in (("stock", stock), ("candidate", candidate)):
        for line in lines:
            if line.startswith("audit "):
                print(f"{label}: {line}")
    if common < min(len(stock), len(candidate)):
        print(f"first_stock: {stock[common]}")
        print(f"first_candidate: {candidate[common]}")
    print("gate=INCONCLUSIVE: stock has not reached validated runtime and host POST checkpoints")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"gate=ERROR: {exc}", file=sys.stderr)
        sys.exit(2)

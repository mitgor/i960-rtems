#!/usr/bin/env python3
"""Prove that the package gate rejects a one-byte card-descriptor mutation."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("candidate", "stage2", "rtems", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError(a.output)
    verifier = Path(__file__).with_name("verify_diagnostic_package.py")
    with tempfile.TemporaryDirectory(prefix="accele160-package-negative-") as tmp:
        tmpdir = Path(tmp)
        base = [sys.executable, str(verifier), "--stage2", str(a.stage2.resolve()),
                "--rtems", str(a.rtems.resolve())]
        baseline = subprocess.run(base + ["--candidate", str(a.candidate.resolve()),
                            "--output", str(tmpdir / "baseline.json")],
                            capture_output=True, text=True)
        if baseline.returncode or not (tmpdir / "baseline.json").exists():
            raise AssertionError("unmodified candidate failed package baseline")
        original = a.candidate.read_bytes()
        changed = bytearray(original)
        changed[0xe0008] ^= 1
        mutated = tmpdir / "mutated.bin"
        mutated.write_bytes(changed)
        rejected = subprocess.run(base + ["--candidate", str(mutated),
                            "--output", str(tmpdir / "mutated-receipt.json")],
                            capture_output=True, text=True)
        if (rejected.returncode == 0 or
                (tmpdir / "mutated-receipt.json").exists() or
                "candidate is not byte-for-byte pack.build output" not in rejected.stderr):
            raise AssertionError("descriptor mutation was not rejected as expected")
    result = {"gate": "PASS", "candidate_sha256": sha(original),
              "mutation_offset": "0xe0008", "mutated_sha256": sha(changed),
              "mutated_candidate_rejected": True,
              "rejection": "candidate is not byte-for-byte pack.build output",
              "physical_card_tested": False, "safe_to_flash": False}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    print("diagnostic_package_negative=PASS descriptor_mutation_rejected=True")


if __name__ == "__main__":
    main()

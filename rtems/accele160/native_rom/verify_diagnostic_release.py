#!/usr/bin/env python3
"""Check saved passive/service diagnostic package and i960 marker evidence."""

import argparse
import hashlib
import json
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text())


def marker_order(observation, require_rtem):
    marks = [(entry["cycles"], entry["marker"], entry["stage2"],
              entry["stage2_result"], entry["worker_count"], entry["done"])
             for entry in observation["checkpoints"]]
    if any(stage2 != "32544753" for _, _, stage2, _, _, _ in marks):
        raise AssertionError("stage-two marker missing")
    if not any(marker == "00000000" and stage2_result == "00000000"
               for _, marker, _, stage2_result, _, _ in marks):
        raise AssertionError("pre-entry stage-two checkpoint missing")
    selected = []
    expected_markers = ["30544e45", "31544e45"]
    if require_rtem:
        expected_markers.append("5254454d")
    expected_markers.append("50415353")
    for expected in expected_markers:
        match = next((row for row in marks if row[1] == expected and
                      (not selected or row[0] > selected[-1][0])), None)
        if match is None:
            raise AssertionError("entry/RTEMS/PASS marker order missing")
        selected.append(match)
    if selected[-1][4:] != (64, 1) or any(row[3] != "00002000" for row in selected):
        raise AssertionError("scheduler result or stage-two status differs")
    return [{"cycles": cycle, "marker": marker} for cycle, marker, *_ in selected]


def package(path, image):
    receipt = load(path)
    if (receipt["gate"] != "PASS" or receipt["candidate_sha256"] != sha(image.read_bytes())
            or receipt["packer"]["candidate_sha256"] != receipt["candidate_sha256"]
            or receipt["safe_to_flash"] or receipt["physical_card_tested"]):
        raise AssertionError(f"{path}: package identity mismatch")
    for source, expected in receipt["source_sha256"].items():
        if sha(Path(source).read_bytes()) != expected:
            raise AssertionError(f"{path}: source changed: {source}")
    return receipt["candidate_sha256"]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("passive-image", "service-image", "control-image", "passive-package",
                 "service-package", "direct-emulator", "service-valid",
                 "service-invalid", "service-coupled", "coupled-tools",
                 "emulator", "qemu", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError(a.output)
    passive_sha = package(a.passive_package, a.passive_image)
    service_sha = package(a.service_package, a.service_image)
    direct = load(a.direct_emulator)
    if (direct["gate"] != "PASS" or direct["emulator_sha256"] != sha(a.emulator.read_bytes())
            or direct["safe_to_flash"] or direct["physical_card_tested"]):
        raise AssertionError("direct emulator identity mismatch")
    observations = direct["observations"]
    if (observations["passive"]["image_sha256"] != passive_sha or
            observations["service"]["image_sha256"] != service_sha or
            any(entry["marker"] in ("30544e45", "31544e45")
                for entry in observations["old_service"]["checkpoints"])):
        raise AssertionError("marker image/control mismatch")
    passive_markers = marker_order(observations["passive"], True)
    service_markers = marker_order(observations["service"], True)
    valid, invalid = load(a.service_valid), load(a.service_invalid)
    for record, expected in ((valid, "observed-next"),
                             (invalid, "observed-next-invalid")):
        if (record["gate"] != "PASS" or record["image_sha256"] != service_sha
                or record["sixth_state"] != expected or record["safe_to_flash"]
                or record["physical_card_tested"]):
            raise AssertionError("service direct valid/malformed mismatch")
    coupled = load(a.service_coupled)
    tools = load(a.coupled_tools)
    expected = [
        ("slot0", 1004, "a3f72f98e18667d7c80eebac996b77f465bce5d5024a8b3ec3c70d2a285572f8",
         "01000000ecffffff"),
        ("slot1", 128, "67dc9bba5de17ef407a77f5e3382a7d89fcc4e7f7b4f287d7e682baece59ff32",
         "0200000000000000"),
        ("slot2", 512, "9e17de7358c0c4cb07a8a7a511c00157a17a38656412e778b69a80ca6b501a41",
         "0100000000000000"),
        ("slot3", 1004, "a3f72f98e18667d7c80eebac996b77f465bce5d5024a8b3ec3c70d2a285572f8",
         "01000000ecffffff")]
    service = coupled["service"]
    control = coupled["control"]
    actual = [(x["slot"], x["bytes"], x["sha256"], x["status_hex"])
              for x in service["mirrored"]]
    if (coupled["gate"] != "PASS" or service["image_sha256"] != service_sha
            or control["image_sha256"] != sha(a.control_image.read_bytes())
            or actual != expected or control["mirrored"] != service["mirrored"]
            or not service["slot4_observed"] or service["slot4_completed"]
            or not service["linux_reset_requested"] or service["myrs_probe_complete"]
            or coupled["physical_card_tested"] or coupled["safe_to_flash"]
            or tools["gate"] != "PASS" or tools["repeat_image_sha256"] != service_sha
            or tools["emulator_sha256"] != direct["emulator_sha256"]
            or tools["qemu_sha256"] != sha(a.qemu.read_bytes())
            or not tools["native_slot4_observed"] or tools["native_slot4_completed"]
            or tools["linux_probe_completed"] or tools["physical_card_tested"]
            or tools["safe_to_flash"]):
        raise AssertionError("service coupled guest evidence mismatch")
    result = {"gate": "PASS", "scope": "saved package, marker and direct i960 receipts",
              "passive_image_sha256": passive_sha,
              "service_image_sha256": service_sha,
              "emulator_sha256": direct["emulator_sha256"],
              "direct_emulator_receipt_sha256": sha(a.direct_emulator.read_bytes()),
              "passive_marker_sequence": passive_markers,
              "service_marker_sequence": service_markers,
              "old_service_entry_markers_absent": True,
              "service_direct_valid": True,
              "service_direct_malformed_rejected": True,
              "service_coupled_guest_pass": True,
              "service_slot4_still_unanswered": True,
              "coupled_pair_receipt_sha256": sha(a.service_coupled.read_bytes()),
              "qemu_sha256": tools["qemu_sha256"],
              "physical_card_tested": False, "safe_to_flash": False}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    print("diagnostic_release=PASS markers_and_direct=True")


if __name__ == "__main__":
    main()

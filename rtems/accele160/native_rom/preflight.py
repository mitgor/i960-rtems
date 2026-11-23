#!/usr/bin/env python3
"""Read-only native-ROM staging gate for an exact stock AcceleRAID spare."""
import argparse
import hashlib
import json
from pathlib import Path

FLASH_SIZE = 1048576
STOCK_SHA = "0a951782a7ccd1855746ffeb3a1b64563287bc56e0dce77d63b79c71ec3b502a"
SPARE_STOCK_SHA = "fadd2b0f6ed9bb88d7c846edd235e5e222cbe3a990b694115c5fa66170e7a816"
IMAGE_SHA = "3f97745c76bd2d5e71a5ee143c9c9fec86bdb6a9d4a4b1202093eb944767909c"
SPARE_IMAGE_SHA = "6f16d71310d75937b5f3961b1faae81eab3258a29371c8505d788c50c545e3bd"
SECOND_SPARE_STOCK_SHA = "0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943"
SECOND_SPARE_ROMLESS_SHA = "33f7a5585c41850690ee0fa05a56382c626e75cd17c8e5185a764f57f741f221"
SECOND_SPARE_PCI_RELEASE_SHA = "a29ed071522e8f34b6e0d6d18b8e7c5a57d9f1ae149a60bedc1aad0d2b02d8b3"
SLOT5_LIVE_STOCK_SHA = "1ee91ea1c172069dd0c98ec68fdf7ebae45e7477466f90b94e36e160f20f3f65"
SLOT5_LIVE_PCI_RELEASE_SHA = "4cdfbf29ea7fddb8b667bc3eddd7efa43e95d160df4fcbd51070a974c00edc5b"
RESTORED_SLOT5_UPDATER_SHA = "17804234a6198963753674e4c6b074777a95c7fbab717e5d914d5376ad54dc29"
ORIGINAL_RAM_LOADER_SHA = "44ee92f0cd7280dfd52a416a733c39513242aa98f54124f16c30a1b3c101b19e"
SECOND_SPARE_RAM_LOADER_SHA = "461076e18d2c2ae2583f8b3ffbd7f92e2524ed01b60c2519ce50eeac5f37f4b3"
SECOND_SPARE_WRITER_SHA = "50a4d7da197fa2beb2b9f7836f2c06237822ef03c0aee2b9034f2e2a0c79ca64"
SECOND_SPARE_OCTOBER_HANDLER_SHA = "ce3e632c80df475d4fa372cad61255c73b5438aad76c2022308889c10c5c9af4"
SECOND_SPARE_CORRECTED_WRITER_SHA = "a56b4a1b84a8ef452be094ecc803c9f26d449c066eb023ad895c78828b9e1e68"
OCTOBER_CARD_INSTALLED_SHA = "1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd"
OCTOBER_CARD_CORRECTED_WRITER_SHA = "b35b1e8312336532fae9175fdc3d0d0be7b80b14281434f42af1db294662c695"
PAIRS = {
    "0000:37:09.1": ((STOCK_SHA, IMAGE_SHA),
                      (SECOND_SPARE_STOCK_SHA, SECOND_SPARE_PCI_RELEASE_SHA),
                      (SLOT5_LIVE_STOCK_SHA, SLOT5_LIVE_PCI_RELEASE_SHA),
                      (SPARE_STOCK_SHA, RESTORED_SLOT5_UPDATER_SHA),
                      (STOCK_SHA, ORIGINAL_RAM_LOADER_SHA),
                      (SECOND_SPARE_STOCK_SHA, SECOND_SPARE_RAM_LOADER_SHA),
                      (SECOND_SPARE_STOCK_SHA, SECOND_SPARE_WRITER_SHA),
                      (SECOND_SPARE_STOCK_SHA, SECOND_SPARE_OCTOBER_HANDLER_SHA),
                      (SECOND_SPARE_STOCK_SHA, SECOND_SPARE_CORRECTED_WRITER_SHA),
                      (OCTOBER_CARD_INSTALLED_SHA, OCTOBER_CARD_CORRECTED_WRITER_SHA)),
    "0000:37:04.1": ((SPARE_STOCK_SHA, SPARE_IMAGE_SHA),
                      (SECOND_SPARE_STOCK_SHA, SECOND_SPARE_ROMLESS_SHA),
                      (SECOND_SPARE_STOCK_SHA, SECOND_SPARE_PCI_RELEASE_SHA)),
}
IDS = [0x1069, 0x0050, 0x1069, 0x0054]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fields(path):
    return dict(item.split("=", 1) for item in path.read_text().split())


def verify_pair(candidate, read_dirs, bdf, current_boot):
    if bdf not in PAIRS:
        raise ValueError("unreviewed card BDF")
    matches = [(stock, image) for stock, image in PAIRS[bdf]
               if image == sha(candidate)]
    if len(candidate) != FLASH_SIZE or len(matches) != 1:
        raise ValueError("native-ROM candidate identity")
    expected_stock, expected_image = matches[0]
    if len(read_dirs) != 2 or read_dirs[0].resolve() == read_dirs[1].resolve():
        raise ValueError("two independent full-flash reads required")
    module_hashes = []
    card_identity = None
    for index, directory in enumerate(read_dirs):
        request = json.loads((directory / "request.json").read_text())
        result = json.loads((directory / "result.json").read_text())
        status = fields(directory / "status.txt")
        data = (directory / "data.bin").read_bytes()
        card = request.get("card")
        if (request.get("boot_id") != current_boot or request.get("selector") != 9
                or request.get("length") != FLASH_SIZE or
                not isinstance(card, dict) or card.get("bdf") != bdf or
                card.get("ids") != IDS or card.get("driver") != "myrsread" or
                result.get("card_after") != card or
                result.get("bytes") != FLASH_SIZE or
                result.get("sha256") != expected_stock or len(data) != FLASH_SIZE or
                sha(data) != expected_stock or
                ("original_card" in request and
                 result.get("original_after") != request["original_card"]) or
                any(status.get(k) != v for k, v in {
                    "done": "1", "status": "0", "residual": "0",
                    "selector": "9", "length": str(FLASH_SIZE),
                    "released": "0", "guard_changes": "0"}.items()) or
                not isinstance(request.get("module_sha256"), str) or
                len(request["module_sha256"]) != 64):
            raise ValueError(f"read {index} is not an accepted stock spare capture")
        if card_identity is not None and card != card_identity:
            raise ValueError("card identity changed between reads")
        card_identity = card
        module_hashes.append(request.get("module_sha256"))
    if module_hashes[0] != module_hashes[1]:
        raise ValueError("reader module changed between stock reads")
    return {"bdf": bdf, "boot_id": current_boot, "card": card_identity,
            "candidate_sha256": expected_image, "stock_sha256": expected_stock,
            "stock_reads": [str(p) for p in read_dirs],
            "reader_module_sha256": module_hashes,
            "read_only_preflight": True, "storeimage_issued": False,
            "flashimage_issued": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--read0", type=Path, required=True)
    p.add_argument("--read1", type=Path, required=True)
    p.add_argument("--bdf", required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if "/" in a.bdf or ".." in a.bdf:
        raise ValueError("invalid BDF")
    boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    receipt = verify_pair(a.candidate.read_bytes(), (a.read0, a.read1), a.bdf, boot)
    if a.out.exists():
        raise FileExistsError(a.out)
    a.out.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()

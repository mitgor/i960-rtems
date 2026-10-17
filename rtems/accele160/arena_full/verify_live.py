#!/usr/bin/env python3
"""Replay compact upper-bank captures without accessing either card."""
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "artifacts/current/accele160-fullbank-20261017"
FW = "1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd"
IMAGES = {
    "arena": "25bdc7df178a14dc39ec2a277e972fea7eb53df4ee5e2d897e4d5982da3279d9",
    "census": "b329045e3a1d54516ee0a75c3cf978b45353a3458cc8848da5163be16dae5558",
    "pages": "7facfbc4fd92fa4e03a454f00a90fd612a628900ad92f469995021b4bcec90ac",
    "fullbank": "ba5c265aa24d524362be0c23b42ceb74df2daead340ef11af3ebb9dfba85a1e1",
    "persistent": "752215d534c8c4d5998f5cdb8edb1d03929905dc480cc54bd110e47fa6f21304",
}
PAGES = ("01f91f4c8c3cbc6f5b34104d1877cc51ca1e69048c223ed724daceacfb89f096",
         "50ec5e43497cf521b443ee749dccdc529e228e88edbf9b4b5082a31aa5541420")


def need(ok, msg):
    if not ok:
        raise ValueError(msg)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fnv(data):
    h = 0x811c9dc5
    for byte in data:
        h = ((h ^ byte) * 0x01000193) & 0xffffffff
    return h


def flash(path, boot=None):
    d = json.loads((path / "result.json").read_text())
    r = json.loads((path / "request.json").read_text())
    status = (path / "status.txt").read_text().strip()
    need(d["bytes"] == r["length"] == 1048576 and d["sha256"] == FW,
         "complete flash identity")
    need(status.startswith("done=1 status=0 residual=0 selector=9 length=1048576")
         and "guard_changes=0" in status, "guarded flash status")
    need(r["card"]["bdf"] == "0000:37:09.1" and
         r["card"]["driver"] == "myrsread" and
         d["old_after"]["driver"] is None, "card identity")
    if boot is not None:
        need(r["boot_id"] == boot, "same-boot flash")
    return r["boot_id"]


def words(data, off, count):
    return struct.unpack_from("<" + "I" * count, data, off)


def verify(root=ART):
    for stage, expected in IMAGES.items():
        build = root / stage / "build/image.bin"
        if stage == "persistent" and not build.exists():
            continue
        need(sha(build.read_bytes()) == expected, stage + " image")
    boot = json.loads((root / "fullbank/live-0/preflight.json").read_text())["boot_id"]
    for stage in ("arena", "census", "pages", "fullbank"):
        for index in (0, 1):
            flash(root / stage / f"post-{index}", boot)
    odd = json.loads((root / "arena/odd-survey/survey.json").read_text())
    need(odd["boot_id"] == boot and len(odd["pages"]) == 1024 and
         all(x["nonzero_bytes"] == 0 for x in odd["pages"]), "odd-page census")
    for stage in ("census", "pages"):
        run = root / stage / "live-0"
        need(json.loads((run / "preflight.json").read_text())["boot_id"] == boot,
             stage + " boot")
        for mode in ("stop", "timeout"):
            page = (run / mode / "page-after.bin").read_bytes()
            census = words(page, 0xb00, 16)
            need(census[0:4] == (0x31534e43, 2048, 2, 53) and
                 census[4:6] == (0xc0ffa038, 0xc0ffe05c) and
                 census[7:9] == (2, 0) and census[14] == 0,
                 stage + " complete-word census")
            bitmap = (run / mode / "bitmap.bin").read_bytes()
            nonzero = [i for i in range(2048) if bitmap[i // 8] & (1 << (i % 8))]
            need(nonzero == [2042, 2046], stage + " bitmap")
            if stage == "pages":
                for i in range(2):
                    need(sha((run / mode / f"nonzero-{i}.bin").read_bytes()) == PAGES[i],
                         "firmware-populated page " + str(i))
    live = root / "fullbank/live-0"
    base = (live / "page-before.bin").read_bytes()
    need((live / "page-restored.bin").read_bytes() == base,
         "final loader page")
    need((live / "owner-after.bin").read_bytes()[0x2a0:0xaa0] ==
         (live / "owner-before.bin").read_bytes()[0x2a0:0xaa0],
         "final 512 count/owner records")
    reports = []
    for mode in ("stop", "timeout"):
        run = live / mode
        page = (run / "page-after.bin").read_bytes()
        bank = words(page, 0xb00, 16)
        need(bank[:4] == (0x314b4e42, 0, 53, 0x800000) and
             bank[4] == bank[5] == bank[6] and
             bank[7:11] == (2048, 0, 2048, 0) and
             bank[11:14] == (0xfefecffb, 0, 0) and
             bank[14] == bank[15], mode + " whole-bank pattern/alias report")
        need((run / "upper-after.bin").read_bytes() ==
             (live / "upper-before.bin").read_bytes() and
             (run / "stock-after.bin").read_bytes() ==
             (live / "stock-before.bin").read_bytes(), mode + " stock restore")
        for i in range(2):
            copy = (run / f"saved-even-{i}.bin").read_bytes()
            need(len(copy) == 4096 and sha(copy) == PAGES[i] and
                 fnv(copy) == (0x8abad2db, 0xd6b6317a)[i],
                 mode + " saved diagnostic page")
        reports.append(bank)
    need(reports[0][11] == reports[1][11], "cross-path bank hash")
    persistent = root / "persistent/live-0/result.json"
    if persistent.exists():
        result = json.loads(persistent.read_text())
        page = (persistent.parent / "persist/quiescent-page.bin").read_bytes()
        report = words(page, 0xb40, 8)
        need(result["boot_id"] == boot and result["image_sha256"] == IMAGES["persistent"]
             and result["arena_bytes"] == 8388608 and result["odd_pages_checked"] == 1024
             and result["heartbeat_after"] > result["heartbeat_before"]
             and result["grant_retained"] and result["release"] == "reboot-only",
             "persistent host result")
        need(report[:4] == (0x314d5241, 2048, 0x833aedc5, 0) and
             report[5:7] == (0x45495551, 0) and
             words(page, 0xa40, 8)[3:8] ==
             (0x504f5453, 0x59444152, 0x214b4341, 0x161610d1, 1),
             "persistent STOP and quiescence")
        need("started=1 done=0" in
             (persistent.parent / "persist/admit-pending-status.txt").read_text(),
             "firmware callback retained")
        post_boot = flash(root / "persistent/post-reset-0")
        need(post_boot != boot, "reset must change boot ID")
        flash(root / "persistent/post-reset-1", post_boot)
    return dict(boot_id=boot, reversible_paths=2,
                persistent_replayed=persistent.exists(),
                bank_pages=2048, nonzero_words=53)


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))

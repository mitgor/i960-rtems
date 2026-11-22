#!/usr/bin/env python3
"""Exercise compiled UPD1 receive/seal firmware in the i960 interpreter."""
import argparse
import hashlib
import json
from pathlib import Path
import socket
import struct
import subprocess
import tempfile
import time

MAGIC = 0x31445055
CONTROL = 0xc0801000
DATA = 0xc0803000
BUFFER = 0xc0900000


def fnv(data):
    value = 2166136261
    for byte in data:
        value = ((value ^ byte) * 16777619) & 0xffffffff
    return value


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--emulator", type=Path, required=True)
    p.add_argument("--image", type=Path, required=True)
    p.add_argument("--target", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--apply-model", action="store_true",
                   help="execute compiled APPLY against the opt-in S3 model")
    p.add_argument("--fault", choices=("gate-stuck-off", "low-vpp", "wrong-id",
                                      "locked-block", "program-stuck"),
                   help="inject one S3 model fault during compiled APPLY")
    a = p.parse_args()
    if a.fault and not a.apply_model:
        p.error("--fault requires --apply-model")
    if a.output.exists():
        raise FileExistsError(a.output)
    image, target = a.image.read_bytes(), a.target.read_bytes()
    if len(image) != 0x100000 or len(target) != 0x100000:
        raise ValueError("both images must be 1 MiB")
    if image[:0x40000] != target[:0x40000] or image[0xc0000:] != target[0xc0000:]:
        raise ValueError("target changes a protected region")
    base_sha, target_sha = hashlib.sha256(image).digest(), hashlib.sha256(target).digest()
    with tempfile.TemporaryDirectory(prefix="accele160-upd1-") as temporary:
        sock = Path(temporary) / "bridge.sock"
        log = a.output.with_suffix(".emu.log")
        with log.open("w") as output:
            command_line = [str(a.emulator.resolve()), str(a.image.resolve()),
                "4000000", "--board-id=11", "--quiet-trace", "--model-config-retry",
                f"--bridge-socket={sock}"]
            if a.apply_model:
                command_line.append("--model-s3-flash")
                if a.fault:
                    command_line.append(f"--model-s3-fault={a.fault}")
            process = subprocess.Popen(command_line, stdout=output,
                                       stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 30
                while not sock.exists():
                    if process.poll() is not None:
                        raise RuntimeError("emulator exited before bridge")
                    if time.monotonic() >= deadline:
                        raise TimeoutError("emulator bridge did not appear")
                    time.sleep(0.05)
                with socket.socket(socket.AF_UNIX) as connection:
                    connection.connect(str(sock))
                    wire = connection.makefile("rwb", buffering=0)

                    def command(line):
                        wire.write((line + "\n").encode())
                        reply = wire.readline().strip()
                        if len(reply) != 8 or reply == b"ERR":
                            raise RuntimeError(f"{line[:80]}: {reply!r}")
                        return int(reply, 16)

                    def read(address):
                        return command(f"R {address:08x} 4 0")

                    def write(address, value):
                        command(f"W {address:08x} 4 {value:08x}")

                    def bulk(address, value):
                        if len(value) != 64:
                            raise ValueError("B writes exactly 64 bytes")
                        command(f"B {address:08x} {value.hex()}")

                    def load_page(page):
                        for pos in range(0, 4096, 64):
                            bulk(DATA + pos, page[pos:pos + 64])

                    def submit(sequence, opcode, index=0, length=0, digest=0,
                               budget=200000000):
                        write(CONTROL + 12, opcode)
                        write(CONTROL + 16, index)
                        write(CONTROL + 20, length)
                        write(CONTROL + 24, digest)
                        write(CONTROL + 4, sequence)
                        cycles = 0
                        while read(CONTROL + 8) != sequence:
                            if cycles >= budget:
                                raise TimeoutError(f"UPD1 opcode {opcode} seq {sequence} unacknowledged")
                            step = min(1000000, budget - cycles)
                            command(f"S {step}")
                            cycles += step
                        return {"status": read(CONTROL + 28),
                                "state": read(CONTROL + 32),
                                "next_chunk": read(CONTROL + 36),
                                "cycles": cycles}

                    if read(0xc0001f1c) != 0x50415353:
                        raise AssertionError("RTEMS PASS not reached")
                    if read(CONTROL) != MAGIC or read(CONTROL + 40) != 2:
                        raise AssertionError("UPD1 service did not initialize")
                    results = {"before_begin": submit(1, 2, 0, 4096, 0)}
                    if results["before_begin"]["status"] != 2:
                        raise AssertionError("chunk before begin was accepted")
                    for offset, digest in ((128, base_sha), (160, target_sha)):
                        for pos in range(0, 32, 4):
                            write(CONTROL + offset + pos,
                                  struct.unpack_from("<I", digest, pos)[0])
                    results["begin"] = submit(2, 1)
                    if (results["begin"]["status"], results["begin"]["state"]) != (0, 1):
                        raise AssertionError(f"begin failed: {results['begin']}")
                    print(f"UPD1 begin acknowledged after {results['begin']['cycles']} cycles", flush=True)
                    load_page(target[4096:8192])
                    results["out_of_order"] = submit(3, 2, 1, 4096,
                        fnv(target[4096:8192]))
                    if results["out_of_order"]["status"] != 3:
                        raise AssertionError("out-of-order chunk was accepted")
                    load_page(target[:4096])
                    results["bad_chunk_hash"] = submit(4, 2, 0, 4096, 0)
                    if results["bad_chunk_hash"]["status"] != 4:
                        raise AssertionError("bad chunk digest was accepted")
                    corrupt = bytearray(target[:4096]); corrupt[0] ^= 1
                    load_page(corrupt)
                    results["protected_change"] = submit(5, 2, 0, 4096, fnv(corrupt))
                    if results["protected_change"]["status"] != 6:
                        raise AssertionError("protected change was accepted")
                    total_chunk_cycles = 0
                    for index in range(256):
                        page = target[index * 4096:(index + 1) * 4096]
                        load_page(page)
                        response = submit(index + 6, 2, index, 4096, fnv(page),
                                          budget=5000000)
                        if (response["status"], response["state"],
                                response["next_chunk"]) != (0, 1, index + 1):
                            raise AssertionError(f"chunk {index} failed: {response}")
                        total_chunk_cycles += response["cycles"]
                        if index in (63, 127, 191, 255):
                            print(f"UPD1 accepted {index + 1}/256 chunks", flush=True)
                    results["seal"] = submit(262, 3, budget=600000000)
                    if (results["seal"]["status"], results["seal"]["state"],
                            results["seal"]["next_chunk"]) != (0, 2, 256):
                        raise AssertionError(f"seal failed: {results['seal']}")
                    differing = next(i for i in range(0x40000, 0xc0000)
                                     if image[i] != target[i])
                    aligned = differing & ~3
                    staged_word = read(BUFFER + aligned)
                    expected_word = struct.unpack_from("<I", target, aligned)[0]
                    if staged_word != expected_word:
                        raise AssertionError("staged DRAM word differs from target")
                    if a.apply_model:
                        if read(CONTROL + 44) & 1 != 1:
                            raise AssertionError("compiled writer capability absent")
                        results["apply"] = submit(263, 5, budget=1000000000)
                        flash_word = read(0xfef00000 + aligned)
                        gate = read(0xe0500000)
                        writer_result = read(CONTROL + 48)
                        s3_status = read(CONTROL + 52)
                        s3_offset = read(CONTROL + 56)
                        if a.fault:
                            expected_fault = {
                                "gate-stuck-off": (5, 0xa8),
                                "low-vpp": (5, 0xa8),
                                "wrong-id": (2, 0),
                                "locked-block": (3, 0),
                                "program-stuck": (7, 0x80),
                            }[a.fault]
                            if (results["apply"]["status"],
                                    results["apply"]["state"],
                                    results["apply"]["next_chunk"]) != (9, 4, 256):
                                raise AssertionError(f"fault did not latch: {results['apply']}")
                            if (writer_result, s3_status) != expected_fault or \
                                    s3_offset != (differing & ~0xffff) or gate & 8:
                                raise AssertionError("fault diagnostics or gate differ: "
                                    f"{writer_result}, {s3_status:#x}, "
                                    f"{s3_offset:#x}, gate={gate:#x}")
                            if flash_word != struct.unpack_from("<I", image, aligned)[0]:
                                raise AssertionError("fault changed target probe byte")
                            results["abort_after_failure"] = submit(264, 4)
                            results["apply_after_failure"] = submit(265, 5)
                            for key in ("abort_after_failure", "apply_after_failure"):
                                if (results[key]["status"], results[key]["state"]) != (2, 4):
                                    raise AssertionError(f"{key} escaped failure latch")
                        else:
                            if (results["apply"]["status"], results["apply"]["state"],
                                    results["apply"]["next_chunk"]) != (0, 3, 256):
                                raise AssertionError(f"apply failed: {results['apply']}; "
                                    f"gate={gate:08x}; writer_result={writer_result:08x}; "
                                    f"s3_status={s3_status:08x}; s3_offset={s3_offset:08x}")
                            if flash_word != expected_word or gate & 8:
                                raise AssertionError("modeled flash readback or gate restore failed")
                            if (writer_result, s3_status, s3_offset) != \
                                    (0, 0x80, differing & ~0xffff):
                                raise AssertionError("writer diagnostic words disagree: "
                                    f"{writer_result}, {s3_status:#x}, {s3_offset:#x}")
                    else:
                        results["abort"] = submit(263, 4)
                        if (results["abort"]["status"], results["abort"]["state"],
                                results["abort"]["next_chunk"]) != (0, 0, 0):
                            raise AssertionError(f"abort failed: {results['abort']}")
                    receipt = {"gate": "native-updater-interpreter-protocol-v2",
                        "protocol_version": 2,
                        "image_sha256": base_sha.hex(), "target_sha256": target_sha.hex(),
                        "rtems_pass": True, "updater_magic": f"{MAGIC:08x}",
                        "results": results, "accepted_chunks": 256,
                        "chunk_cycles": total_chunk_cycles,
                        "sample_flash_offset": differing,
                        "sample_staged_word": f"{staged_word:08x}",
                        "fault": a.fault,
                        "writer_result": writer_result if a.apply_model else None,
                        "s3_status": s3_status if a.apply_model else None,
                        "s3_offset": s3_offset if a.apply_model else None,
                        "flash_programmed": False,
                        "simulated_flash_programmed": a.apply_model and not a.fault,
                        "result": "PASS"}
                    a.output.write_text(json.dumps(receipt, indent=2) + "\n")
                    print(a.output)
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


if __name__ == "__main__":
    main()

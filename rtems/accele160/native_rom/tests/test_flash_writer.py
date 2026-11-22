"""Exercise the C flash command writer against the independent S3 model."""

import ctypes
import hashlib
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from s3_model import S3Flash  # noqa: E402

BLOCK = 0x10000
FIRST = 0x40000
READ = ctypes.CFUNCTYPE(ctypes.c_ubyte, ctypes.c_uint, ctypes.c_void_p)
WRITE = ctypes.CFUNCTYPE(None, ctypes.c_uint, ctypes.c_ubyte, ctypes.c_void_p)


class IO(ctypes.Structure):
    _fields_ = [("read8", READ), ("write8", WRITE), ("context", ctypes.c_void_p),
                ("max_status_polls", ctypes.c_uint), ("last_status", ctypes.c_uint),
                ("failed_offset", ctypes.c_uint)]


class WriterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        so = pathlib.Path(cls.temp.name) / "flash_writer.so"
        subprocess.run(["cc", "-std=c99", "-Wall", "-Wextra", "-Werror", "-shared",
                        "-fPIC", str(ROOT / "flash_writer.c"), "-o", str(so)], check=True)
        cls.lib = ctypes.CDLL(str(so))
        cls.lib.accele160_s3_probe.argtypes = [ctypes.POINTER(IO)]
        cls.lib.accele160_s3_probe.restype = ctypes.c_int
        cls.lib.accele160_s3_write_block.argtypes = [ctypes.c_uint,
            ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint, ctypes.c_void_p]
        cls.lib.accele160_s3_write_block.restype = ctypes.c_int

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.chip = S3Flash()
        self.chip.vpp_enabled = True
        self.writes = []

        def read(address, _):
            if self.chip.pending:
                self.chip.tick()
            return self.chip.read(address)

        def write(address, value, _):
            self.writes.append((address, value))
            self.chip.write(address, value)

        self.read_callback = READ(read)
        self.write_callback = WRITE(write)
        self.io = IO(self.read_callback, self.write_callback, None, 4, 0, 0)

    def program(self, offset, data):
        buf = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
        return self.lib.accele160_s3_write_block(offset, buf, len(data), ctypes.byref(self.io))

    def test_probe_restores_array_mode(self):
        self.assertEqual(self.lib.accele160_s3_probe(ctypes.byref(self.io)), 0)
        self.assertEqual(self.chip.mode, "array")
        self.assertEqual(self.writes, [(0, 0x90), (0, 0xff)])

    def test_erase_program_and_verify_block(self):
        self.chip.array[FIRST:FIRST + BLOCK] = b"\x00" * BLOCK
        data = bytearray(b"\xff" * BLOCK)
        data[0] = 0x12
        data[123] = 0x34
        data[-1] = 0x56
        self.assertEqual(self.program(FIRST, data), 0)
        self.assertEqual(self.chip.array[FIRST:FIRST + BLOCK], data)
        self.assertEqual(self.chip.mode, "array")
        self.assertEqual(self.io.last_status & 0x80, 0x80)

    def test_protected_offsets_and_length_never_write(self):
        data = b"\x00" * BLOCK
        for offset, payload in ((0, data), (0xc0000, data),
                                (FIRST + 1, data), (FIRST, data[:-1])):
            self.writes.clear()
            self.assertEqual(self.program(offset, payload), 1)
            self.assertEqual(self.writes, [])

    def test_locked_block_fails_before_erase(self):
        self.chip.block_locked[FIRST // BLOCK] = True
        self.assertEqual(self.program(FIRST, b"\x00" * BLOCK), 3)
        self.assertEqual(self.chip.mode, "array")
        self.assertNotIn((FIRST, 0x20), self.writes)

    def test_master_lock_fails_before_erase(self):
        self.chip.master_locked = True
        self.assertEqual(self.program(FIRST, b"\x00" * BLOCK), 3)
        self.assertNotIn((FIRST, 0x20), self.writes)

    def test_low_vpp_reports_status_without_programming(self):
        self.chip.vpp_enabled = False
        self.assertEqual(self.program(FIRST, b"\x00" * BLOCK), 5)
        self.assertEqual(self.io.last_status & 0x08, 0x08)
        self.assertEqual(self.chip.array[FIRST], 0xff)
        self.assertEqual(self.chip.mode, "array")

    def test_wrong_identity_fails_before_erase(self):
        original = self.chip.read
        self.chip.read = lambda address: 0x00 if self.chip.mode == "id" and address == 1 else original(address)
        self.assertEqual(self.program(FIRST, b"\x00" * BLOCK), 2)
        self.assertNotIn((FIRST, 0x20), self.writes)

    def test_status_timeout_is_bounded(self):
        def read_without_progress(address, _):
            return self.chip.read(address)
        self.read_callback = READ(read_without_progress)
        self.io.read8 = self.read_callback
        self.io.max_status_polls = 2
        self.assertEqual(self.program(FIRST, b"\x00" * BLOCK), 4)
        self.assertEqual(self.io.failed_offset, FIRST)
        self.assertIsNotNone(self.chip.pending)

    def test_erase_readback_detects_corruption(self):
        self.chip.array[FIRST] = 0x00
        original_tick = self.chip.tick

        def tick_with_stuck_bit():
            original_tick()
            self.chip.array[FIRST + 10] = 0x00

        self.chip.tick = tick_with_stuck_bit
        self.assertEqual(self.program(FIRST, b"\x00" * BLOCK), 6)
        self.assertEqual(self.io.failed_offset, FIRST + 10)

    def test_program_readback_detects_corruption(self):
        original_tick = self.chip.tick

        def tick_with_stuck_bit():
            op = self.chip.pending
            original_tick()
            if op and op.kind == "program":
                self.chip.array[op.address] = 0xff

        self.chip.tick = tick_with_stuck_bit
        data = bytearray(b"\xff" * BLOCK)
        data[7] = 0x30
        self.assertEqual(self.program(FIRST, data), 7)
        self.assertEqual(self.io.failed_offset, FIRST + 7)

    @unittest.skipUnless(os.environ.get("ACCELE160_REPLAY_FULL_IMAGE") == "1",
                         "run explicitly for the 1 MiB candidate replay")
    def test_full_stock_to_native_image(self):
        project = ROOT.parents[2]
        base = (project / "artifacts/current/accele160-guarded-20261016/"
                "rawflash-0/data.bin").read_bytes()
        target = (project / "artifacts/current/accele160-ram-loader-20261120/"
                  "native-ram-loader-original.bin").read_bytes()
        self.assertEqual(hashlib.sha256(base).hexdigest(),
                         "0a951782a7ccd1855746ffeb3a1b64563287bc56e0dce77d63b79c71ec3b502a")
        self.assertEqual(hashlib.sha256(target).hexdigest(),
                         "44ee92f0cd7280dfd52a416a733c39513242aa98f54124f16c30a1b3c101b19e")
        self.assertEqual(base[:FIRST], target[:FIRST])
        self.assertEqual(base[0xc0000:], target[0xc0000:])
        self.chip = S3Flash(base)
        self.chip.vpp_enabled = True
        changed = []
        for offset in range(FIRST, 0xc0000, BLOCK):
            if base[offset:offset + BLOCK] != target[offset:offset + BLOCK]:
                changed.append(offset)
                self.assertEqual(self.program(offset, target[offset:offset + BLOCK]), 0)
        self.assertTrue(changed)
        self.assertEqual(bytes(self.chip.array), target)


if __name__ == "__main__":
    unittest.main()

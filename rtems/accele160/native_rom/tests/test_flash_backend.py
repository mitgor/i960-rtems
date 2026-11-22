"""Check the stock-derived board gate around the C S3 writer."""
import ctypes
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
FLASH_READ = ctypes.CFUNCTYPE(ctypes.c_ubyte, ctypes.c_uint)
FLASH_WRITE = ctypes.CFUNCTYPE(None, ctypes.c_uint, ctypes.c_ubyte)
GATE_READ = ctypes.CFUNCTYPE(ctypes.c_ubyte)
GATE_WRITE = ctypes.CFUNCTYPE(None, ctypes.c_ubyte)


class BackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        so = pathlib.Path(cls.temp.name) / "backend.so"
        subprocess.run(["cc", "-std=c99", "-Wall", "-Wextra", "-Werror",
                        "-DACCELE160_FLASH_BACKEND_TEST", "-shared", "-fPIC",
                        str(ROOT / "flash_writer.c"), str(ROOT / "flash_backend.c"),
                        "-o", str(so)], check=True)
        cls.lib = ctypes.CDLL(str(so))
        cls.lib.accele160_flash_backend_set_test_io.argtypes = [
            FLASH_READ, FLASH_WRITE, GATE_READ, GATE_WRITE]
        cls.lib.accele160_flash_backend_write_block.argtypes = [
            ctypes.c_uint, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint,
            ctypes.c_void_p]
        cls.lib.accele160_flash_backend_write_block.restype = ctypes.c_int

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.chip = S3Flash()
        # Split port, as stock uses it: reads are input pins, writes a latch.
        self.inputs = 0x03
        self.latch = 0
        self.gate_writes = []
        self.flash_writes = []
        self.connect_vpp = True
        self.gate_stuck_off = False

        def flash_read(address):
            if self.chip.pending:
                self.chip.tick()
            return self.chip.read(address)

        def flash_write(address, value):
            self.flash_writes.append((address, value))
            self.chip.write(address, value)

        def gate_read():
            return self.inputs

        def gate_write(value):
            self.gate_writes.append(value)
            self.latch = value & ~8 if self.gate_stuck_off else value
            if self.connect_vpp:
                self.chip.vpp_enabled = bool(self.latch & 8)

        self.callbacks = (FLASH_READ(flash_read), FLASH_WRITE(flash_write),
                          GATE_READ(gate_read), GATE_WRITE(gate_write))
        self.lib.accele160_flash_backend_set_test_io(*self.callbacks)

    def program(self, offset=FIRST, data=None):
        if data is None:
            data = b"\x00" + b"\xff" * (BLOCK - 1)
        buf = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
        return self.lib.accele160_flash_backend_write_block(
            offset, buf, len(data), None)

    def test_gate_is_stock_constants_and_needs_no_readback(self):
        self.assertEqual(self.program(), 0)
        self.assertEqual(self.gate_writes, [0x08, 0x00])
        self.assertFalse(self.chip.vpp_enabled)
        self.assertEqual(self.chip.array[FIRST], 0)

    def test_missing_vpp_fails_in_chip_status_before_any_erase(self):
        for fault in ("connect_vpp", "gate_stuck_off"):
            self.setUp()
            setattr(self, fault, fault == "gate_stuck_off")
            self.assertEqual(self.program(), 5)
            self.assertEqual(self.gate_writes, [0x08, 0x00])
            self.assertEqual(self.chip.array[FIRST], 0xff)

    def test_protected_offset_does_not_touch_gate(self):
        self.assertEqual(self.program(offset=0), 1)
        self.assertEqual(self.gate_writes, [])
        self.assertEqual(self.flash_writes, [])


if __name__ == "__main__":
    unittest.main()

"""Run the actual RAM1 ID payload logic against the independent S3 model."""
import ctypes
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "native_rom"))
from s3_model import S3Flash  # noqa: E402

READ = ctypes.CFUNCTYPE(ctypes.c_ubyte, ctypes.c_uint)
WRITE = ctypes.CFUNCTYPE(None, ctypes.c_uint, ctypes.c_ubyte)


class IdentifyPayloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        so = pathlib.Path(cls.temp.name) / "identify.so"
        subprocess.run(["cc", "-std=c99", "-Wall", "-Wextra", "-Werror",
                        "-DACCELE160_FLASH_IDENTIFY_TEST", "-shared", "-fPIC",
                        str(ROOT / "flash_identify_payload.c"), "-o", str(so)],
                       check=True)
        cls.lib = ctypes.CDLL(str(so))
        cls.lib.flash_identify_set_io.argtypes = [READ, WRITE]
        cls.lib.accele160_flash_identify_main.argtypes = [ctypes.POINTER(ctypes.c_uint)]
        cls.lib.accele160_flash_identify_main.restype = ctypes.c_uint

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.chip = S3Flash()
        self.writes = []
        self.read_cb = READ(lambda address: self.chip.read(address))

        def write(address, value):
            self.writes.append((address, value))
            self.chip.write(address, value)

        self.write_cb = WRITE(write)
        self.lib.flash_identify_set_io(self.read_cb, self.write_cb)
        self.control = (ctypes.c_uint * 40)()

    def test_unlocked_s3_restores_array(self):
        self.assertEqual(self.lib.accele160_flash_identify_main(self.control), 0)
        self.assertEqual(list(self.control[13:18]), [0x31444953, 0x89, 0xa6, 0, 0])
        self.assertEqual(self.writes, [(0, 0xff), (0, 0x90), (0, 0xff)])
        self.assertEqual(self.chip.mode, "array")
        self.assertEqual(self.chip.array, b"\xff" * 0x100000)

    def test_locked_block_reports_mask(self):
        self.chip.block_locked[6] = True
        self.assertEqual(self.lib.accele160_flash_identify_main(self.control), 2)
        self.assertEqual(self.control[17], 1 << 6)
        self.assertEqual(self.chip.mode, "array")

    def test_first_and_last_block_locks_are_visible(self):
        self.chip.block_locked[0] = True
        self.chip.block_locked[15] = True
        self.assertEqual(self.lib.accele160_flash_identify_main(self.control), 2)
        self.assertEqual(self.control[17], (1 << 0) | (1 << 15))
        self.assertEqual(self.chip.mode, "array")

    def test_wrong_device_reports_failure(self):
        original = self.chip.read
        self.read_cb = READ(lambda address:
                            0xa5 if self.chip.mode == "id" and address == 1
                            else original(address))
        self.lib.flash_identify_set_io(self.read_cb, self.write_cb)
        self.assertEqual(self.lib.accele160_flash_identify_main(self.control), 2)
        self.assertEqual(self.control[15], 0xa5)
        self.assertEqual(self.chip.mode, "array")


if __name__ == "__main__":
    unittest.main()

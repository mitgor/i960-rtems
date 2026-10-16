import json
from pathlib import Path
import struct
import tempfile
import unittest

from verify_live import verify, CANDIDATE_SHA, MODULE_SHA, SESSION_SHA


class ReplayTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        card = {"driver": "myrsread"}
        old = {"driver": None}
        (self.path / "preflight.json").write_text(json.dumps(dict(
            candidate_sha256=CANDIDATE_SHA, module_sha256=MODULE_SHA,
            session_sha256=SESSION_SHA, card=card, old_card=old)))
        (self.path / "result.json").write_text(json.dumps(dict(
            returncode=0, card_after=card, old_after=old,
            command=dict(done="1", status="0", residual="0", released="1"))))
        (self.path / "page-before.bin").write_bytes(b"\xff" * 4096)
        after = bytearray(b"\xff" * 4096)
        struct.pack_into("<4I", after, 0x820, 0x4f4c4c41, 0x16161031,
                         0xc0618000, 0x40000)
        (self.path / "page-after-call.bin").write_bytes(after)
        (self.path / "table-before.bin").write_bytes(b"\x00" * 4096)
        (self.path / "table-after.bin").write_bytes(b"\x00" * 4096)

    def tearDown(self):
        self.temp.cleanup()

    def test_valid_capture(self):
        self.assertEqual(verify(self.path)["pointer"], "0xc0618000")

    def test_adjacent_firmware_word_is_not_allocator_metadata(self):
        after = bytearray((self.path / "table-after.bin").read_bytes())
        after[0xaa0] ^= 1
        (self.path / "table-after.bin").write_bytes(after)
        self.assertEqual(verify(self.path)["adjacent_table_page_changed_bytes"], 1)

    def test_tampered_result_or_table_fails(self):
        for file, offset in (("page-after-call.bin", 0x700),
                             ("page-after-call.bin", 0x824),
                             ("table-after.bin", 0x2a0)):
            with self.subTest(file=file, offset=offset):
                path = self.path / file
                original = path.read_bytes()
                modified = bytearray(original); modified[offset] ^= 1
                path.write_bytes(modified)
                with self.assertRaises(ValueError):
                    verify(self.path)
                path.write_bytes(original)


if __name__ == "__main__":
    unittest.main()

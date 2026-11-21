import hashlib
import pathlib
import struct
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_stock_flash_id as base  # noqa: E402
import run_stock_gate_hold as hold  # noqa: E402

IMAGE = (HERE / "stock_gate_hold.bin").read_bytes()
WORDS = struct.unpack("<%dI" % (len(IMAGE) // 4), IMAGE)
GOOD = (hold.MAGIC, 0xC04B0000, 0x40, 0, 0x48, 0, 0x40, hold.POLLS, 0)


class GateHoldTests(unittest.TestCase):
    def test_committed_payload_is_the_pinned_one(self):
        self.assertEqual(hashlib.sha256(IMAGE).hexdigest(), hold.PAYLOAD_SHA)
        self.assertEqual(IMAGE[:8], bytes.fromhex("0030808c00f800c0"))
        self.assertEqual(IMAGE[0x14:0x18], bytes.fromhex("00500484"))
        self.assertEqual(WORDS[0x7C // 4], hold.POLLS)

    def test_payload_cannot_address_flash(self):
        # i960 opcodes sit in the top byte; 0xfe there can only be a literal
        # in the flash aperture. Both byte stores go through r8 = e0500000.
        self.assertFalse([w for w in WORDS if w >> 24 == 0xFE])
        self.assertEqual([w for w in WORDS if w >> 24 == 0x82],
                         [0x823A1000, 0x823A1000])
        self.assertEqual(WORDS.count(0xE0500000), 1)

    def test_decode(self):
        record, held = hold.decode(GOOD)
        self.assertTrue(held and record["register_reads_back_bit3"])
        write_only = GOOD[:4] + (0,) + GOOD[5:]
        record, held = hold.decode(write_only)
        self.assertTrue(held)
        self.assertFalse(record["register_reads_back_bit3"])
        for bad in ((0,) + GOOD[1:],                 # no record
                    GOOD[:8] + (2,),                  # gate was busy
                    GOOD[:7] + (hold.POLLS - 1, 0),   # hold cut short
                    GOOD[:6] + (0x48,) + GOOD[7:]):   # shadow left set
            self.assertFalse(hold.decode(bad)[1])

    def test_flash_id_decode_unchanged(self):
        ok = (base.MAGIC, 0x89, 0xA6, 0, 0, 0x50, 0, 0, 0)
        self.assertTrue(base.decode_flash_id(ok)[1])
        self.assertFalse(base.decode_flash_id(ok[:4] + (1,) + ok[5:])[1])


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path
import struct
import build_image as b

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT/'artifacts'
class ImageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock=(ART/'private-dumps/snapshot-fresh-20261010T125336Z/image-window-0.bin').read_bytes()
        cls.unpacked=(ART/'private-dumps/snapshot-fresh-20261010T125336Z/firmware-unpacked.bin').read_bytes()
        cls.code=(ART/'postinit-preflight-20261010/loader.bin').read_bytes()
    def test_candidate_matches_saved_and_preserves_boot(self):
        image,m=b.build(self.stock,self.code,self.unpacked)
        self.assertEqual(image,(ART/'postinit-preflight-20261010/experimental-full-rom.bin').read_bytes())
        self.assertEqual(image[0x7c000:],self.stock[0x7c000:])
        self.assertEqual(image[0x30000:0x60000],self.stock[0x30000:0x60000])
        self.assertEqual(b.word(image,b.META+8),0xfefe0000)
        self.assertEqual(b.word(image,b.META+0x7c),b.checksum(image[b.META:b.META+0x7c]))
        self.assertFalse(m['flash_ready'])
    def test_wrong_donor_and_truncated_dump(self):
        for offset in (0,0x30000,0x67f60,0x7ff40):
            bad=bytearray(self.stock);bad[offset]^=1
            with self.assertRaises(ValueError): b.build(bad,self.code,self.unpacked)
        with self.assertRaises(ValueError):b.build(self.stock[:-1],self.code,self.unpacked)
    def test_invalid_code_lengths(self):
        for code in (b'',b'abc',bytes(4100)):
            with self.assertRaises(ValueError):b.build(self.stock,code,self.unpacked)
    def test_wrong_runtime_reference(self):
        bad=bytearray(self.unpacked);bad[b.HOOK-0xc0010000]^=1
        with self.assertRaises(ValueError):b.build(self.stock,self.code,bad)
    def test_boot_metadata_describes_real_copy_and_handoff(self):
        w=struct.unpack_from('<9I',self.stock,b.META)
        self.assertEqual(w,(1,0xc000c460,0xc004a2e0,0x6000,0x1000,0xc000a000,0xf694b003,0x7000,0xc0010000))
        self.assertEqual(b.checksum(self.stock[0x31000:0x37000]),w[6])
if __name__=='__main__':unittest.main()

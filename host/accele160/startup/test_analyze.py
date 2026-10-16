import struct
import unittest
from pathlib import Path
from analyze import analyze

ROOT = Path(__file__).resolve().parents[3]
FLASH = ROOT/'artifacts/current/accele160-guarded-20261016/rawflash-0/data.bin'

class StartupTests(unittest.TestCase):
    def test_stock_contract(self):
        r=analyze(FLASH.read_bytes())
        self.assertTrue(r['accepted_stock'])
        self.assertEqual(r['reset_entry'],0xfeffc000)
        self.assertEqual(r['loader']['entry'],0xc000c590)
        self.assertEqual(r['runtime']['entry'],0xc004cf70)
        self.assertEqual(r['runtime']['end_exclusive'],0xc00b77ac)

    def test_trailer_tamper(self):
        b=bytearray(FLASH.read_bytes());b[0xbff64]^=4
        with self.assertRaisesRegex(ValueError,'trailer checksum'): analyze(b)

    def test_loader_tamper(self):
        b=bytearray(FLASH.read_bytes());b[0x41000]^=1
        with self.assertRaisesRegex(ValueError,'loader checksum'): analyze(b)

    def test_descriptor_overflow(self):
        b=bytearray(FLASH.read_bytes());struct.pack_into('<I',b,0xe0024,0xffffffff)
        with self.assertRaisesRegex(ValueError,'region bounds'): analyze(b)

    def test_reset_tamper(self):
        b=bytearray(FLASH.read_bytes());b[0xfff40]^=4
        with self.assertRaisesRegex(ValueError,'IBR checksum'): analyze(b)

if __name__=='__main__':unittest.main()

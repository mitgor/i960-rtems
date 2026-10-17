#!/usr/bin/env python3
"""Memory-map admission checks for the AcceleRAID RTEMS flat image."""
import unittest
from manifest import BASE, PAGE, STAGING, build

class ManifestTests(unittest.TestCase):
    def test_exact_extent_and_hash(self):
        image=b'\x01'*100
        padded,meta=build(image,{'_start':BASE,'__bss_start':BASE+16,'__bss_end':BASE+100})
        self.assertEqual(len(padded),PAGE)
        self.assertEqual(meta['pages'],1)
        self.assertEqual(meta['free_payload_pages'],126)
    def test_wrong_entry_rejected(self):
        with self.assertRaises(ValueError):build(b'\0'*32,{'_start':BASE+4,'__bss_start':BASE,'__bss_end':BASE+32})
    def test_bss_beyond_upload_rejected(self):
        with self.assertRaises(ValueError):build(b'\0'*32,{'_start':BASE,'__bss_start':BASE,'__bss_end':BASE+33})
    def test_staging_overlap_rejected(self):
        with self.assertRaises(ValueError):build(b'\0'*(STAGING-BASE+1),{'_start':BASE,'__bss_start':BASE,'__bss_end':BASE+32})

if __name__=='__main__':unittest.main()

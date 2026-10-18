"""A modified bundle must be rejected before PCI or module access."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from launch import verify


class BundleTests(unittest.TestCase):
    def test_pin_and_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp).resolve();data=p/'image.bin';data.write_bytes(b'kernel')
            (p/'bundle.json').write_text(json.dumps(dict(schema=1,card_profile='accele160',
                files={'image.bin':hashlib.sha256(data.read_bytes()).hexdigest()})))
            self.assertEqual(verify(p)['card_profile'],'accele160')
            data.write_bytes(b'changed')
            with self.assertRaises(ValueError):verify(p)

    def test_other_card_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'bundle.json').write_text(json.dumps(
                dict(schema=1,card_profile='dac960pg',files={})))
            with self.assertRaises(ValueError):verify(p)


if __name__=='__main__':unittest.main()

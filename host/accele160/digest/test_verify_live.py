import json
from pathlib import Path
import shutil
import struct
import tempfile
import unittest
from verify_live import fnv, verify

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'artifacts/current/accele160-pagecopy-20261016/live/two-page'


class DigestReplayTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'capture'
        shutil.copytree(BASE,self.path)
        before=(self.path/'page-before.bin').read_bytes()
        reserved=(self.path/'page-reserved.bin').read_bytes()
        images=[]
        for index in (0,1):
            pattern=bytes(((i*53+0x96+index)^(i>>3))&0xff for i in range(4096))
            (self.path/f'staging-{index}-readback.bin').write_bytes(pattern)
            page=bytearray(reserved)
            digest=fnv(pattern)
            for offset in (0x820,0x860):
                struct.pack_into('<4I',page,offset,0x59504f43,0x16161061,index,digest)
            (self.path/f'copy-{index}-page.bin').write_bytes(page)
            (self.path/f'copy-{index}-status.txt').write_text('started=1 done=1 status=0 residual=0 released=0\n')
            images.append(pattern)
        whole=fnv(b''.join(images))
        page=bytearray(reserved)
        page[0x820:0x830]=before[0x820:0x830]
        for offset in (0x830,0x870):
            struct.pack_into('<4I',page,offset,0x48534148,0x16161071,2,whole)
        (self.path/'digest-page.bin').write_bytes(page)
        (self.path/'digest-status.txt').write_text('started=1 done=1 status=0 residual=0 released=0\n')
        result=json.loads((self.path/'result.json').read_text())
        result['indexes']=[0,1]
        result['whole_digest']=f'0x{whole:08x}'
        (self.path/'result.json').write_text(json.dumps(result))
    def tearDown(self):self.temp.cleanup()
    def test_good_and_tampered(self):
        self.assertTrue(verify(self.path)['digest_passed'])
        for name,offset in [('digest-page.bin',0x83c),('digest-page.bin',0x880),
                            ('copy-1-page.bin',0x82c),('staging-1-readback.bin',33),
                            ('table-after.bin',0x9a0)]:
            with self.subTest(name=name,offset=offset):
                file=self.path/name;original=file.read_bytes();altered=bytearray(original)
                altered[offset]^=1;file.write_bytes(altered)
                with self.assertRaises(ValueError):verify(self.path)
                file.write_bytes(original)

if __name__=='__main__':unittest.main()

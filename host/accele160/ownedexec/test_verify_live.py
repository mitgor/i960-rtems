import json
from pathlib import Path
import shutil
import struct
import tempfile
import unittest
from verify_live import PROBE, fnv, verify
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'artifacts/current/accele160-digest-20261017/live/digest-live'

class OwnedExecReplayTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'capture'
        shutil.copytree(BASE,self.path)
        before=(self.path/'page-before.bin').read_bytes()
        reserved=(self.path/'page-reserved.bin').read_bytes()
        ptr=struct.unpack_from('<I',reserved,0x828)[0]
        image=[]
        for index in (0,1):
            pattern=bytes(((i*53+0x96+index)^(i>>3))&0xff for i in range(4096))
            if index==0:pattern=PROBE+pattern[80:]
            image.append(pattern)
            (self.path/f'staging-{index}-readback.bin').write_bytes(pattern)
            page=bytearray(reserved)
            for off in (0x820,0x860):
                struct.pack_into('<4I',page,off,0x59504f43,0x16161061,index,fnv(pattern))
            (self.path/f'copy-{index}-page.bin').write_bytes(page)
        whole=fnv(b''.join(image))
        d=bytearray(reserved)
        d[0x820:0x830]=before[0x820:0x830]
        for off in (0x830,0x870):struct.pack_into('<4I',d,off,0x48534148,0x16161071,2,whole)
        (self.path/'digest-page.bin').write_bytes(d)
        e=bytearray(reserved)
        e[0x820:0x830]=before[0x820:0x830]
        struct.pack_into('<4I',e,0x800,0x444f4e45,0x16161081,496,0x16161081^0x96016001)
        struct.pack_into('<4I',e,0x830,0x214e5552,0x16161081,ptr,whole)
        struct.pack_into('<4I',e,0x880,0x43455845,0x16161081,2,whole)
        (self.path/'ownedexec-page.bin').write_bytes(e)
        (self.path/'ownedexec-status.txt').write_text('started=1 done=1 status=0 residual=0 released=0\n')
        host=json.loads((self.path/'result.json').read_text())
        host['whole_digest']=f'0x{whole:08x}'
        host['executed_exact_probe']=True
        host['probe_sha256']='5d86878199ddcdd7f7ea950699a8e047f4189eb264c1dcff860ee6f83e0e740c'
        (self.path/'result.json').write_text(json.dumps(host))
    def tearDown(self):self.temp.cleanup()
    def test_normal_and_tampered(self):
        self.assertTrue(verify(self.path)['normal_return'])
        for name,offset in [('staging-0-readback.bin',3),('digest-page.bin',0x83c),
                            ('ownedexec-page.bin',0x808),('ownedexec-page.bin',0x838),
                            ('ownedexec-page.bin',0x900),('table-after.bin',0x9a0)]:
            with self.subTest(name=name,offset=offset):
                p=self.path/name;b=bytearray(p.read_bytes());b[offset]^=1;p.write_bytes(b)
                with self.assertRaises(ValueError):verify(self.path)
                b[offset]^=1;p.write_bytes(b)
if __name__=='__main__':unittest.main()

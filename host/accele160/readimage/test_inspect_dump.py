import shutil,subprocess,tempfile,unittest
from pathlib import Path
from inspect_dump import inspect
ROOT=Path(__file__).resolve().parents[3]
FIXTURE=ROOT/'artifacts/current/accele160-readimage-20261016/fresh'
class DumpTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.p=Path(self.tmp.name)/'capture';shutil.copytree(FIXTURE,self.p)
 def test_accepted_components(self):
  result=inspect(self.p)
  self.assertEqual(result['cpu_mhz'],100)
  self.assertTrue(result['images']['firmware']['embedded']['crc_passed'])
  self.assertFalse(result['complete_physical_flash_dump'])
 def test_one_copy_tampered(self):
  p=self.p/'firmware-full-0/data.bin';b=bytearray(p.read_bytes());b[0]^=1;p.write_bytes(b)
  with self.assertRaises(ValueError):inspect(self.p)
 def test_both_compressed_copies_tampered(self):
  for i in (0,1):
   p=self.p/f'firmware-full-{i}/data.bin';b=bytearray(p.read_bytes());b[0x7100]^=128;p.write_bytes(b)
  with self.assertRaises((ValueError,subprocess.CalledProcessError)):inspect(self.p)
 def test_nonzero_residual_rejected(self):
  (self.p/'bios-full-0/status.txt').write_text('done=1 status=0 residual=28672\n')
  with self.assertRaises(ValueError):inspect(self.p)
if __name__=='__main__':unittest.main()

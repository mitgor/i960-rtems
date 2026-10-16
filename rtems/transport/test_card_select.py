"""Identity gate tests; no PCI access or module loading."""
import tempfile
import unittest
from pathlib import Path
from card_select import select,PROFILES

class SelectionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name);self.bdf='0000:37:09.1';self.p=self.root/self.bdf;self.p.mkdir()
  for name,value in zip(('vendor','device','subsystem_vendor','subsystem_device'),PROFILES['accele160']):
   (self.p/name).write_text(hex(value))
 def test_exact_new_card(self):
  self.assertIsNone(select(self.bdf,'accele160',self.root)['driver'])
 def test_old_runtime_rejects_new_card(self):
  with self.assertRaises(ValueError):select(self.bdf,'dac960pg',self.root)
 def test_no_default_or_short_bdf(self):
  for bdf in (None,'','37:09.1'):
   with self.assertRaises(ValueError):select(bdf,'accele160',self.root)
 def test_wrong_subsystem(self):
  (self.p/'subsystem_device').write_text('0x0050')
  with self.assertRaises(ValueError):select(self.bdf,'accele160',self.root)
 def test_binding_required(self):
  with self.assertRaises(ValueError):select(self.bdf,'accele160',self.root,driver='myrs')
  target=self.root/'myrs';target.mkdir();(self.p/'driver').symlink_to(target)
  self.assertEqual(select(self.bdf,'accele160',self.root,driver='myrs')['driver'],'myrs')
 def test_missing_device(self):
  with self.assertRaises(FileNotFoundError):select('0000:37:04.1','dac960pg',self.root)

if __name__=='__main__':unittest.main()

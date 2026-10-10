import hashlib
from pathlib import Path
import tempfile
import unittest
import zlib
from build_probe import ROOT, build

class ProbeTests(unittest.TestCase):
    def test_live_and_programming_plan(self):
        import json
        from validate_live import validate
        from program_plan import make_plan
        base=ROOT/'artifacts/programming-preflight-20261010'
        self.assertEqual(validate(),json.loads((base/'validation.json').read_text()))
        self.assertEqual(make_plan(),json.loads((base/'program-plan.json').read_text()))

    def test_cpu_crc_algorithm(self):
        data=(ROOT/'artifacts/romhook-20261010/candidate-full-rom.bin').read_bytes()
        crc=0xffffffff
        for b in data:
            crc ^= b
            for _ in range(8):
                bit=crc&1
                crc >>= 1
                if bit: crc ^= 0xedb88320
        self.assertEqual(crc^0xffffffff,0x2012d01f)
        self.assertEqual(crc^0xffffffff,zlib.crc32(data))
        stock=(ROOT/'artifacts/private-dumps/snapshot-fresh-20261010T125336Z/image-window-0.bin').read_bytes()
        self.assertNotEqual(zlib.crc32(stock),0x2012d01f)

    def test_generated_probe_and_bounds(self):
        code=ROOT/'artifacts/programming-preflight-20261010/build/probe.bin'
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'build'
            build(code,out)
            header=(out/'rom_exec.h').read_text()
            self.assertIn('#define EXEC_REGION_SIZE 128u',header)
            self.assertIn('#define EXEC_FLASH_SIZE 128u',header)
            self.assertLessEqual(0xc0fac100+128,0xc0fac180)
            self.assertLessEqual(0xc0fac180+128,0xc0fad000)
            source=(out/'dac960dump.c').read_text()
            self.assertIn('if (!stage_check) return -EINVAL;',source)
            self.assertIn('opcode != 0x1c && opcode != 0x20 && opcode != 0x21 && opcode != 0x6f',source)
            self.assertIn('if (d->pending || d->exec_dirty) goto done;', (out/'stage_rehearsal.h').read_text())
            bad=Path(tmp)/'bad.bin';bad.write_bytes(bytes(128))
            with self.assertRaises(AssertionError): build(bad,out)

if __name__=='__main__': unittest.main()

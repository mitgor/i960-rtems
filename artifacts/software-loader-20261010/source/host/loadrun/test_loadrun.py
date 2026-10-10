from pathlib import Path
import subprocess,tempfile,unittest
from build import build,ROOT,HERE

class LoadRunTests(unittest.TestCase):
    def test_transaction_and_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'build';build(out)
            source=(HERE/'transaction.h').read_text()
            (out/'transaction_under_test.h').write_text('static int load_chunks'+source.split('static int load_chunks',1)[1])
            binary=Path(tmp)/'test'
            subprocess.run(['cc','-O1','-std=c99','-Wall','-Wextra','-Werror','-Wno-unused-function','-fsanitize=address,undefined','-I',str(out),str(HERE/'test_transaction.c'),'-o',str(binary)],check=True)
            subprocess.run([str(binary),str(ROOT/'artifacts/romhook-20261010/candidate-full-rom.bin')],check=True)
            with self.assertRaises(ValueError):build(out)

class CliTests(unittest.TestCase):
    def test_payload_bounds_and_clean_gate(self):
        from loadrun import validate_payload, clean
        for size, entry in [(0,0),(3,0),(65540,0),(4,4),(8,1)]:
            with self.assertRaises(ValueError): validate_payload(bytes(size),entry)
        validate_payload(bytes(65536),65532)
        log='experiment-result=0 pending=0; exported\n'+''.join(n+'-dirty=0\n' for n in ('scratch','exec','stage'))
        self.assertTrue(clean(log))
        for bad in [log.replace('pending=0','pending=1'),log.replace('exec-dirty=0','exec-dirty=1'),log.replace('stage-dirty=0','')]:
            self.assertFalse(clean(bad))
    def test_live_captures(self):
        from loadrun import verify
        base=ROOT/'artifacts/software-loader-20261010'
        for name, binary, value in [('run-fibonacci-10','demo.bin',55),('run-fibonacci-20','demo.bin',6765),('run-mix','mix.bin',0x8c2f3b20)]:
            self.assertEqual(verify(base/name,(base/'target'/binary).read_bytes()),value)

if __name__=='__main__':unittest.main()

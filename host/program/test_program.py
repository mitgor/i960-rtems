from pathlib import Path
import subprocess,tempfile,unittest
from build import build,ROOT,HERE

class ProgramTests(unittest.TestCase):
    def test_actual_programming_and_postboot(self):
        import json
        from validate_programmed import validate
        self.assertEqual(validate(True),json.loads((ROOT/'artifacts/programmed-rom-20261010/validation.json').read_text()))

    def test_postboot_builder_matches_tested_module_sources(self):
        from build_postboot import build as build_postboot
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'postboot';build_postboot(out)
            archived=ROOT/'artifacts/programmed-rom-20261010/postboot-build'
            for p in out.iterdir():
                self.assertEqual(p.read_bytes(),(archived/p.name).read_bytes(),p.name)
            source=(out/'dac960dump.c').read_text()
            self.assertIn('if (opcode == 0x21) return -EPERM;',source)
            self.assertIn('if (opcode == 0x6f && (!d->boot_verified || count || offset))',source)

    def test_archived_rehearsal(self):
        import json
        from validate_rehearsal import validate
        self.assertEqual(validate(),json.loads((ROOT/'artifacts/one-shot-harness-20261010/validation.json').read_text()))

    def test_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            binary=Path(tmp)/'test'
            subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(HERE/'test_one_shot.c'),'-o',str(binary)],check=True)
            subprocess.run([str(binary)],check=True)

    def test_generated_transaction(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'build';build(out)
            with self.assertRaises(ValueError): build(out)
            src=(out/'stage_rehearsal.h').read_text()
            body='static int stage_read_pair'+src.split('static int stage_read_pair',1)[1]
            body=body.replace('#include "program_kernel.h"','')
            (out/'transaction_under_test.h').write_text(body)
            kernel=(out/'program_kernel.h').read_text()
            (out/'program_flow_under_test.h').write_text('static int run_program_once'+kernel.split('static int run_program_once',1)[1])
            binary=Path(tmp)/'test'
            subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-Wno-unused-function','-fsanitize=address,undefined','-I',str(out),str(HERE/'test_transaction.c'),'-o',str(binary)],check=True)
            subprocess.run([str(binary),str(ROOT/'artifacts/private-dumps/snapshot-fresh-20261010T125336Z/image-window-0.bin'),str(ROOT/'artifacts/romhook-20261010/candidate-full-rom.bin')],check=True)
            c=(out/'dac960dump.c').read_text()
            self.assertIn('if (d->program.submitted && opcode != 0x20 && opcode != 0x1c) return -EPERM;',c)
            self.assertIn('if (program_enable || d->pending',c)
            self.assertIn('schedule_work(&d->program_work)',c)
            self.assertNotIn('module_put',c)
            self.assertIn('if (d->program.submitted) goto done;',src)

if __name__=='__main__':unittest.main()

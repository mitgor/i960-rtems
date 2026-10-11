#!/usr/bin/env python3
"""Native sanitizer checks of generated baseline and optimized validation."""
import importlib.util,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('transfer_builder',HERE/'build.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory(prefix='i960-transfer-test-') as d:
 d=Path(d);m.build(d/'module')
 (d/'baseline.h').write_text((d/'module/buffer_io.h').read_text())
 subprocess.run(['cc','-O2','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(d),'-I'+str(HERE),str(HERE/'test_validate.c'),'-o',str(d/'test')],check=True)
 subprocess.run([str(d/'test')],check=True)
with tempfile.TemporaryDirectory(prefix='i960-count-test-') as d:
 d=Path(d)
 subprocess.run(['cc','-O2','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(HERE),str(HERE/'test_count.c'),'-o',str(d/'test')],check=True)
 subprocess.run([str(d/'test')],check=True)
# Run inherited command-boundary failure/timeout and immutable-corruption sweep
# against both generated transaction variants, including periodic/full close.
for fast,detail in [(False,True),(True,True),(True,False)]:
 with tempfile.TemporaryDirectory(prefix='i960-transfer-fault-') as d:
  d=Path(d);m.build(d/'module',fast,detail)
  root=m.ROOT
  source=(root/'host/loadrun/test_transaction.c').read_text().split('static int one(')[0]
  source=source.replace('    struct firmware *payload;','    bool ready,runner_uncertain,output_valid;u32 sequence,steps,output_length;\n    struct firmware *payload;')
  source=source.replace('card[BIO_IMAGE_SIZE+4]^=1','card[BIO_IMAGE_SIZE+4]=original[BIO_IMAGE_SIZE+4]^1')
  source=source.replace('static bool buffer_io;','static bool buffer_io=true;')
  (d/'buffer_demo.c').write_text((root/'loader/runtime/buffer_demo.c').read_text())
  (d/'test.c').write_text(source+(root/'host/session/test_session_main.c').read_text())
  helpers=(d/'module/stage_rehearsal.h').read_text()
  (d/'module/transaction_under_test.h').write_text(helpers[helpers.index('static int load_chunks'):])
  subprocess.run(['cc','-O2','-Wall','-Wextra','-Wno-unused-function','-fsanitize=address,undefined','-g','-I'+str(d/'module'),'-I'+str(d),str(d/'test.c'),'-o',str(d/'test')],check=True)
  subprocess.run([str(d/'test'),str(root/'artifacts/romhook-20261010/candidate-full-rom.bin')],check=True)

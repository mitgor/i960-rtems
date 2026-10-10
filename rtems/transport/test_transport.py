#!/usr/bin/env python3
"""Fault-inject actual session transaction with the existing simulated transport."""
import importlib.util,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('session_build',HERE/'build.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as t:
    t=Path(t);m.build(t/'module')
    baseline=(ROOT/'host/loadrun/test_transaction.c').read_text().split('static int one(')[0]
    baseline=baseline.replace('    struct firmware *payload;','    bool ready,runner_uncertain,output_valid;u32 sequence,steps,output_length;\n    struct firmware *payload;')
    baseline=baseline.replace('card[BIO_IMAGE_SIZE+4]^=1','card[BIO_IMAGE_SIZE+4]=original[BIO_IMAGE_SIZE+4]^1')
    baseline=baseline.replace('static bool buffer_io;','static bool buffer_io=true;')
    (t/'buffer_demo.c').write_text((ROOT/'loader/runtime/buffer_demo.c').read_text())
    (t/'test.c').write_text(baseline+(ROOT/'host/session/test_session_main.c').read_text())
    helpers=(t/'module/stage_rehearsal.h').read_text()
    (t/'module/transaction_under_test.h').write_text(helpers[helpers.index('static int load_chunks'):])
    subprocess.run(['cc','-Wall','-Wextra','-Wno-unused-function','-fsanitize=address,undefined','-g','-I'+str(t/'module'),'-I'+str(t),str(t/'test.c'),'-o',str(t/'test')],check=True)
    subprocess.run([str(t/'test'),str(ROOT/'artifacts/romhook-20261010/candidate-full-rom.bin')],check=True)

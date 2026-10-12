#!/usr/bin/env python3
"""Check the generated host verifier protects the relocated loader code."""
import importlib.util,subprocess,tempfile
from pathlib import Path
r=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('resident_builder',r/'build_transport.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
header=m.protect_upload_header((r.parent/'transport/buffer_io.h').read_text())
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'buffer_io.h').write_text(header)
 (p/'test.c').write_text(r'''
#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "buffer_io.h"
static unsigned char before[524288],after[524288];
int main(void){unsigned int i;bio_put(before+BIO_OFFSET,BIO_MAGIC);bio_put(before+BIO_OFFSET+4,1);bio_put(before+BIO_OFFSET+8,1);bio_put(before+BIO_OFFSET+16,8192);bio_put(before+BIO_OFFSET+20,BIO_PENDING);
 memcpy(after,before,sizeof(before));bio_put(after+BIO_OFFSET+20,0);bio_put(after+BIO_OFFSET+28,1);
 assert(bio_response_valid(before,after,sizeof(before)));after[0x20010]^=1;assert(bio_response_valid(before,after,sizeof(before)));
 for(i=0x68000;i<0x70000;i+=257){after[i]^=1;assert(!bio_response_valid(before,after,sizeof(before)));after[i]^=1;}
 after[0x6ffff]^=1;assert(!bio_response_valid(before,after,sizeof(before)));
 puts("PASS generated host bootstrap verifier: mutable BSS accepted; sampled upper code reservation bytes and guard boundary protected");}
''')
 subprocess.run(['cc','-O2',str(p/'test.c'),'-o',str(p/'test')],check=True);subprocess.run([str(p/'test')],check=True)

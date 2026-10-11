#!/usr/bin/env python3
"""Opt-in, reversible suppression of one stock upload diagnostic string."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('transfer',HERE.parent/'transfer/build.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
replace=base.replace

def build(out,quiet=False,detail=True):
 base.build(out,True,detail)
 if quiet:
  fw=(ROOT/'artifacts/vendor-fujitsu/4.07-0-29/unpacked.bin').read_bytes()
  assert hashlib.sha256(fw).hexdigest()=='21f6c1d898a533d7023a53893f03547ed61631016d1b247d3ecbb97b9403c195'
  boot=(ROOT/'artifacts/vendor-fujitsu/4.07-0-29/Fgj40729.img.raw').read_bytes()
  # These bytes are copied fefc9000 -> c000a000 during bootstrap.
  arrays={'quiet_original':fw[0x3cec0:0x3cf10],'quiet_printf':boot[0x12a0:0x13a0],'quiet_uart':boot[0x1120:0x1188]}
  assert arrays['quiet_original'][:16]==b'\nOff%X Siz%X\0\0\0\0'
  header=''.join('static const u8 '+name+'[]={'+','.join('0x%02x'%x for x in data)+'};\n' for name,data in arrays.items())
  (out/'quiet_data.h').write_text('#ifndef QUIET_DATA_H\n#define QUIET_DATA_H\n'+header+'#endif\n')
  (out/'quiet_policy.h').write_text((HERE/'policy.h').read_text())
  p=out/'dac960rtems.c';s=p.read_text()
  s=replace(s,'#include "rom_exec.h"','#include "rom_exec.h"\n#include "quiet_policy.h"')
  s=replace(s,'    bool output_valid;','    bool output_valid;\n    bool quiet_armed,quiet_dirty;')
  s=replace(s,'!load_upload_allowed(count,offset,d->payload->size,d->runtime_verified,d->load_armed)', '!load_upload_allowed(count,offset,d->payload->size,d->runtime_verified,d->load_armed) &&\n         !quiet_write_allowed(count,offset,d->runtime_verified,d->quiet_armed)')
  s=replace(s,'if (opcode == 0x20 && !sp_allowed', 'if (opcode == 0x20 && !quiet_read_allowed(count,offset,d->runtime_verified,d->quiet_armed) && !sp_allowed')
  s=s.replace('d->pending || d->exec_dirty || d->stage_dirty','d->pending || d->exec_dirty || d->stage_dirty || d->quiet_dirty')
  p.write_text(s)
  p=out/'stage_rehearsal.h';s=p.read_text()
  s=replace(s,'/* Persistent BIO1', '#include "quiet_data.h"\n'+(HERE/'transaction.h').read_text()+'\n/* Persistent BIO1')
  s=replace(s,'    if(d->exec_dirty) {','    if(d->quiet_dirty) {rc=quiet_end(d);if(rc) return rc;}\n    if(d->exec_dirty) {')
  s=replace(s,'    d->ready=true;','    rc=quiet_begin(d);if(rc) return rc;\n    d->ready=true;')
  s=replace(s,'    /* Consume sequence before submission:', '    rc=quiet_check(d);if(rc) return rc;\n    /* Consume sequence before submission:')
  s=replace(s,'d->load_armed=false;d->ready=false;', 'd->load_armed=false;d->ready=false;d->quiet_armed=false;')
  p.write_text(s)
 (out/'upload-build.json').write_text(json.dumps(dict(quiet=quiet,command_profile=detail),indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--quiet',action='store_true');p.add_argument('--coarse',action='store_true');a=p.parse_args();build(a.out,a.quiet,not a.coarse)

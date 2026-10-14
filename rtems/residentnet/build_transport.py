#!/usr/bin/env python3
import argparse,importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('exclusive_builder',HERE.parent/'exclusive/build_transport.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def protect_upload_header(s,engine=False):
 return m.replace(s,'if(i>=0x20010u && i<0x6fff0u) continue;',
                  'if(i>=0x20010u && i<'+('0x60000u' if engine else '0x68000u')+') continue;')
def build(out,payload):
 m.build(out,payload)
 p=out/'dac960auto.c';s=p.read_text();s=m.replace(s,'static const struct file_operations session_fops=',(HERE/'host.h').read_text()+'\nstatic const struct file_operations session_fops=');s=m.replace(s,'.unlocked_ioctl=monitor_ioctl,','.unlocked_ioctl=resident_ioctl,')
 metadata=payload.parent/'build.json'
 flags=json.loads(metadata.read_text())['flags'] if metadata.exists() else []
 if any(f.startswith('-DI960_OWNED_MIB=') for f in flags):
  s='#define I960_LARGE_CONTROL 1\n'+s
 if '-DI960_HEAP_SHARED' in flags:
  s=m.replace(s,'else{token=0x90000000u;reply=0x95000000u;}', 'else{token=w[2]?0x96000000u:0x90000000u;reply=w[2]?0x97000000u:0x95000000u;}')
  s=m.replace(s,'epoch=w[1];mutex_lock(&d->session_lock);', 'if(w[0]==7&&w[2]>1)return -EINVAL;epoch=w[1];mutex_lock(&d->session_lock);')
 if any(f.startswith('-DI960_OWNED_MIB=') for f in flags):
  s=m.replace(s,'if(w[0]==7&&w[2]>1)', 'if(w[0]==7&&w[2]>2)')
  s=m.replace(s,'else{token=w[2]?0x96000000u:0x90000000u;reply=w[2]?0x97000000u:0x95000000u;}', 'else{token=w[2]==2?0x98000000u:w[2]?0x96000000u:0x90000000u;reply=w[2]==2?0x99000000u:w[2]?0x97000000u:0x95000000u;}')
 if '-DI960_DOOM_PLAY' in flags:s='#define I960_DOOM_PLAY 1\n'+s
 if '-DI960_DOOM_ENGINE' in flags:s='#define I960_DOOM_ENGINE 1\n'+s
 if '-DI960_DOOM_RUNTIME' in flags:s='#define I960_DOOM_RUNTIME 1\n'+s
 if '-DI960_DOOM_CHECKPOINT_BARRIERS' in flags:s='#define I960_DOOM_CHECKPOINT_BARRIERS 1\n'+s
 if '-DI960_DOOM_CHECKPOINTS' in flags:s='#define I960_DOOM_CHECKPOINTS 1\n'+s
 if '-DI960_DOOM_OWNED' in flags:s='#define I960_DOOM_OWNED 1\n'+s
 if '-DI960_RESIDENT_UPLOAD' in flags:
  header=out/'buffer_io.h';header.write_text(protect_upload_header(header.read_text(),'-DI960_DOOM_ENGINE' in flags))
  s=m.replace(s,'static const struct file_operations session_fops=',(HERE/'upload_host.h').read_text()+'\nstatic const struct file_operations session_fops=')
  s=m.replace(s,'.unlocked_ioctl=resident_ioctl,','.unlocked_ioctl=upload_ioctl,')
 if '-DI960_FAULT_TEST=3' in flags:
  s=m.replace(s,'mu_resident;', 'mu_resident,mu_nmi_injected;')
  s=m.replace(s,'static const struct file_operations session_fops=',(HERE/'nmi_test_host.h').read_text()+'\nstatic const struct file_operations session_fops=')
  s=m.replace(s,'.unlocked_ioctl=resident_ioctl,','.unlocked_ioctl=nmi_test_ioctl,')
 p.write_text(s)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--payload',type=Path,required=True);a=p.parse_args();build(a.out,a.payload)

#!/usr/bin/env python3
import argparse,importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('exclusive_builder',HERE.parent/'exclusive/build_transport.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def build(out,payload):
 m.build(out,payload)
 p=out/'dac960auto.c';s=p.read_text();s=m.replace(s,'static const struct file_operations session_fops=',(HERE/'host.h').read_text()+'\nstatic const struct file_operations session_fops=');s=m.replace(s,'.unlocked_ioctl=monitor_ioctl,','.unlocked_ioctl=resident_ioctl,')
 metadata=payload.parent/'build.json'
 flags=json.loads(metadata.read_text())['flags'] if metadata.exists() else []
 if '-DI960_FAULT_TEST=3' in flags:
  s=m.replace(s,'mu_resident;', 'mu_resident,mu_nmi_injected;')
  s=m.replace(s,'static const struct file_operations session_fops=',(HERE/'nmi_test_host.h').read_text()+'\nstatic const struct file_operations session_fops=')
  s=m.replace(s,'.unlocked_ioctl=resident_ioctl,','.unlocked_ioctl=nmi_test_ioctl,')
 p.write_text(s)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--payload',type=Path,required=True);a=p.parse_args();build(a.out,a.payload)

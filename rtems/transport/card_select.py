"""Explicit PCI identity gate; selecting a card never binds or changes it."""
import re
from pathlib import Path
PROFILES={'dac960pg':(0x1069,0x0010,0x1069,0x0010),
          'accele160':(0x1069,0x0050,0x1069,0x0054)}
def select(bdf,profile,root=Path('/sys/bus/pci/devices'),driver=None):
 if not isinstance(bdf,str) or not re.fullmatch(r'[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]',bdf):
  raise ValueError('explicit canonical --bdf is required; no default/auto-selection')
 if profile not in PROFILES:raise ValueError('unknown card profile')
 p=root/bdf
 ids=tuple(int((p/n).read_text().strip(),16) for n in ('vendor','device','subsystem_vendor','subsystem_device'))
 if ids!=PROFILES[profile]:raise ValueError(f'{bdf}: identity {ids} does not match {profile}')
 bound=(p/'driver').resolve().name if (p/'driver').is_symlink() else None
 if driver is not None and bound!=driver:raise ValueError(f'{bdf}: expected driver {driver}, found {bound}')
 return dict(bdf=bdf,profile=profile,ids=list(ids),driver=bound)
if __name__=='__main__':
 import argparse,json
 p=argparse.ArgumentParser();p.add_argument('--bdf',required=True);p.add_argument('--profile',choices=PROFILES,required=True);a=p.parse_args()
 print(json.dumps(select(a.bdf,a.profile),indent=2))

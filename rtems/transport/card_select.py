"""Explicit PCI identity gate; selecting a card never binds or changes it."""
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from card_profiles import pci_ids
PROFILES={name:pci_ids(name) for name in ('dac960pg','accele160')}
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
def require_unbound_or_absent(bdf,profile,root=Path('/sys/bus/pci/devices')):
 """Protect an explicitly named peer without requiring it to be installed.

 The target selector remains strict. Missing identity files, dangling sysfs
 links, a wrong device at the peer BDF, or a bound peer still fail closed.
 """
 if not isinstance(bdf,str) or not re.fullmatch(r'[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]',bdf):
  raise ValueError('explicit canonical peer BDF required')
 if profile not in PROFILES:raise ValueError('unknown peer card profile')
 if not root.is_dir():raise FileNotFoundError(root)
 p=root/bdf
 if not p.exists() and not p.is_symlink():
  return dict(bdf=bdf,profile=profile,present=False,ids=None,driver=None)
 identity=select(bdf,profile,root)
 if identity['driver'] is not None:raise ValueError(f'{bdf}: peer card unexpectedly bound')
 return identity

if __name__=='__main__':
 import argparse,json
 p=argparse.ArgumentParser();p.add_argument('--bdf',required=True);p.add_argument('--profile',choices=PROFILES,required=True);a=p.parse_args()
 print(json.dumps(select(a.bdf,a.profile),indent=2))

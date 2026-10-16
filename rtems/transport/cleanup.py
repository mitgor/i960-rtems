#!/usr/bin/env python3
"""Explicit cleanup after host client SIGKILL, using its project-owned journal.

Never force-unloads an uncertain card. Run as root with the prior output folder.
"""
import argparse,fcntl,json,subprocess
from pathlib import Path
from run import DBG,capture,verify_close
from card_select import select
from relay import IFACE

def main():
 p=argparse.ArgumentParser();p.add_argument('--bdf',required=True);p.add_argument('output',type=Path);p.add_argument('--autonomous',action='store_true');a=p.parse_args()
 dbg=Path('/sys/kernel/debug/dac960auto') if a.autonomous else DBG
 lock=open('/run/lock/i960-loadrun.lock','w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 identity=select(a.bdf,'dac960pg')
 request=json.loads((a.output/'request.json').read_text())
 if request.get('card',{}).get('bdf')!=a.bdf:raise SystemExit('Journal does not identify selected card; no cleanup performed')
 module='dac960auto' if a.autonomous else 'dac960rtems'
 if identity['driver'] not in (None,module):raise SystemExit('Selected card has another driver')
 if Path('/sys/module',module).exists() and Path('/sys/module',module,'parameters/bdf').read_text().strip()!=a.bdf:raise SystemExit('Loaded module belongs to another card')
 if Path('/sys/class/net',IFACE).exists():raise SystemExit('TUN is still owned; stop the client normally before cleanup')
 from ipv6_gateway import cleanup as cleanup6
 cleanup6(a.output)
 # Exact commands are restricted to this project's routing rule shapes.
 j=json.loads((a.output/'gateway-journal.json').read_text());allowed=[]
 for cmd in j['undo']:
  allowed_fixed=[
   ['iptables','-t','filter','-D','FORWARD','-o',IFACE,'-j','DROP'],
   ['iptables','-t','filter','-D','FORWARD','-o',IFACE,'-d','10.196.0.2','-m','conntrack','--ctstate','ESTABLISHED,RELATED','-j','ACCEPT']]
  valid=cmd in allowed_fixed
  if len(cmd)==13 and cmd[:10]==['iptables','-t','filter','-D','FORWARD','-i',IFACE,'-s','10.196.0.2','-o'] and cmd[11:]==['-j','ACCEPT']:
   valid=bool(__import__('re').fullmatch(r'[a-zA-Z0-9_.:-]{1,15}',cmd[10]))
  if len(cmd)==11 and cmd[:8]==['iptables','-t','nat','-D','POSTROUTING','-s','10.196.0.2/32','-o'] and cmd[9:]==['-j','MASQUERADE']:
   valid=bool(__import__('re').fullmatch(r'[a-zA-Z0-9_.:-]{1,15}',cmd[8]))
  if not valid:raise ValueError('unexpected rule in project journal')
  allowed.append(cmd)
 for cmd in reversed(allowed):
  check=cmd[:];check[3]='-C'
  if subprocess.run(check,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:subprocess.run(cmd,check=True)
 if j['original_forwarding'] is not None:
  current=Path('/proc/sys/net/ipv4/ip_forward')
  if current.read_text().strip()=='1':current.write_text(j['original_forwarding'])
 if dbg.exists():
  log=(dbg/'result.txt').read_text()
  if 'SESSION CLOSE rc=0 pending=0 exec-dirty=0 stage-dirty=0' not in log:raise SystemExit('Card state uncertain; module retained, inspect debugfs. No forced unload.')
  if a.autonomous and 'AUTONOMOUS STOP verified before any RAM restoration' not in log:raise SystemExit('No verified autonomous stop; module retained')
  out=a.output/'after-kill-close';capture(out,dbg);verify_close(out)
  subprocess.run(['rmmod','dac960auto' if a.autonomous else 'dac960rtems'],check=True)
 (a.output/'manual-cleanup.json').write_text(json.dumps(dict(clean=True,driver_bound=Path('/sys/bus/pci/devices',a.bdf,'driver').exists(),ip_forward=Path('/proc/sys/net/ipv4/ip_forward').read_text().strip()),indent=2)+'\n')
 print('Project firewall rules removed; verified RAM restoration; module unloaded if present.')
if __name__=='__main__':main()

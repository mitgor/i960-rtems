#!/usr/bin/env python3
"""Start the bounded broker after proving its old process/socket are gone.
Never adopts or restarts the hardware owner. A stale Unix socket is not a DMA
resource; only that dead listener name is removed.
"""
import argparse,subprocess,socket,stat,os
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args()
r=subprocess.run(['systemctl','show','-p','MainPID','--value','i960-combined'],capture_output=True,text=True)
if r.stdout.strip() not in ('','0'):raise SystemExit('broker still has a process')
path=Path('/run/i960-combined.sock')
if path.exists():
 st=path.lstat()
 if not stat.S_ISSOCK(st.st_mode) or st.st_uid!=os.geteuid():raise SystemExit('unexpected socket ownership/type')
 with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
  s.settimeout(.3)
  try:s.connect(str(path))
  except ConnectionRefusedError:path.unlink()
  else:raise SystemExit('a listener still owns the socket')
subprocess.run(['systemd-run','--unit=i960-combined','--collect','/usr/bin/python3',str(a.root/'broker.py'),'--journal',str(a.root/'broker.jsonl')],check=True)

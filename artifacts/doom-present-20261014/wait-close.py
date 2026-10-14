#!/usr/bin/env python3
"""Wait for a bounded card test, then replay/archive it. Never reboot or unload."""
import subprocess,sys,time
from pathlib import Path
capture=sys.argv[1];assert capture in ('compare','repeat')
deadline=time.monotonic()+3600
while time.monotonic()<deadline:
 log=Path(capture+'.log').read_text()
 if 'Resident network tests passed; module retained until reboot.' in log:
  subprocess.run(['bash','close.sh',capture],check=True);break
 if (Path(capture)/'error.txt').exists():raise RuntimeError((Path(capture)/'error.txt').read_text())
 time.sleep(10)
else:raise TimeoutError('test did not complete; resources left untouched')

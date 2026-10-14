from pathlib import Path
import subprocess,time
for attempt in range(180):
 if Path('live/error.txt').exists():raise SystemExit(Path('live/error.txt').read_text())
 if 'Resident network tests passed; module retained until reboot.' in Path('live.log').read_text():
  subprocess.run(['bash','close.sh'],check=True);break
 time.sleep(10)
else:raise SystemExit('No close within 30 minutes; leave ownership untouched')

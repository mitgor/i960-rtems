import json,hashlib,subprocess,urllib.request,time
from pathlib import Path
p=Path('/home/mit/i960-doom-stream-20261018');cfg=json.loads((p/'gateway-manifest.json').read_text())
for n,h in cfg.items():assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n
state=json.loads(Path('/run/i960-doom-control.json').read_text());pid=int(subprocess.check_output(['systemctl','show','-p','MainPID','--value','i960-doom'],text=True))
assert state['pid']==pid and state['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip() and state['port']==8087
subprocess.run(['systemd-run','--unit=i960-doom-stream','--collect','--setenv=PYTHONPATH='+str(p/'vendor'),'/usr/bin/python3',str(p/'source/gateway.py'),'--port','8088','--journal',str(p/'transport.jsonl')],check=True)
for _ in range(40):
 try:
  with urllib.request.urlopen('http://127.0.0.1:8088/status',timeout=1) as r:status=json.load(r)
  break
 except OSError:time.sleep(.2)
else:raise RuntimeError('gateway not ready')
Path('/home/mit/i960-packet-dma-20261019/gateway-restored.json').write_text(json.dumps(dict(owner_pid=pid,status=status),indent=2)+'\n')
print('Existing manifest-verified browser gateway restored; hardware owner unchanged')

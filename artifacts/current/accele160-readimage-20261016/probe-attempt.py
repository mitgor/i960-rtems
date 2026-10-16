import sys,json,time
from pathlib import Path
sys.path.insert(0,'/home/mit/i960-accele160-20261016/project/rtems/transport')
from card_select import select
import subprocess
out=Path('/home/mit/i960-accele160-20261016/readimage-evidence');out.mkdir(exist_ok=False)
new='0000:37:09.1';old='0000:37:04.1'
assert select(old,'dac960pg')['driver'] is None
identity=select(new,'accele160',driver='myrs');dev=Path('/sys/bus/pci/devices')/new
assert not list(dev.glob('host*/target*/*/block/*'))
(out/'before.json').write_text(json.dumps(identity))
(dev/'driver/unbind').write_text(new)
subprocess.run(['insmod','/home/mit/i960-accele160-20261016/readimage-module/myrsread.ko','read_bdf='+new],check=True)
select(new,'accele160',driver='myrsread')
hosts=list(dev.glob('host*/scsi_host/host*'));assert len(hosts)==1
host=hosts[0]
(out/'controller.bin').write_bytes(bytes.fromhex((host/'stock_controller').read_text()))
for i in range(2):
 attr=host/'stock_descriptor';attr.write_text('descriptor')
 deadline=time.monotonic()+10
 while True:
  s=attr.read_text()
  if s.startswith('state=2') or time.monotonic()>deadline:break
  time.sleep(.1)
 (out/f'read-{i}.txt').write_text(s)
 print(s[:100],flush=True)
 if not s.startswith('state=2'):raise RuntimeError('Pending DMA retained; do not unload or unbind')
 if len(s.splitlines())>1:(out/f'descriptor-{i}.bin').write_bytes(bytes.fromhex(s.splitlines()[1]))
 attr.write_text('clear')
assert select(old,'dac960pg')['driver'] is None
(out/'after.json').write_text(json.dumps(select(new,'accele160')))
print(str(out))

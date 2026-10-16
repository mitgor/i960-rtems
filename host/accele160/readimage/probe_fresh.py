import argparse,fcntl,hashlib,sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'rtems/transport'))
from card_select import select
import subprocess
p=argparse.ArgumentParser();p.add_argument('--bdf',required=True);p.add_argument('--module',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
lock=open('/run/lock/i960-loadrun.lock','w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
out=a.out;out.mkdir(exist_ok=False)
new=a.bdf;old='0000:37:04.1'
assert select(old,'dac960pg')['driver'] is None
identity=select(new,'accele160');assert identity['driver'] is None;dev=Path('/sys/bus/pci/devices')/new
assert not list(dev.glob('host*/target*/*/block/*'))
(out/'before.json').write_text(json.dumps(dict(card=identity,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),module_sha256=hashlib.sha256(a.module.read_bytes()).hexdigest())))
subprocess.run(['insmod',str(a.module),'read_bdf='+new],check=True)
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
 if s.splitlines()[0]!='state=2 status=0 residual=0':raise RuntimeError('Firmware read failed; evidence saved')
assert select(old,'dac960pg')['driver'] is None
(out/'after.json').write_text(json.dumps(select(new,'accele160')))
data=(out/'descriptor-0.bin').read_bytes()
assert len(data)==1024 and data[:4]==bytes.fromhex('584c594d'),'invalid descriptor'
assert data==(out/'descriptor-1.bin').read_bytes(),'descriptor reads differ'
(out/'accepted.json').write_text(json.dumps(dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),full_flash_dump=False)))
print(str(out))

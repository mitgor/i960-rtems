#!/usr/bin/env python3
"""Repeat guarded stock timer/vector observations on current op-13 firmware."""
import argparse,fcntl,hashlib,json,mmap,struct,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'host/accele160/inventory_gate'))
import run_inventory as inventory
sys.path.insert(0,str(ROOT/'host/accele160/vector_gate'))
import run_vector as vector
sys.path.insert(0,str(ROOT/'rtems/transport'))
from card_select import select

BDF,OLD='0000:37:09.1','0000:37:04.1'
FIRMWARE='1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
HANDLER='8d8c79c3b8c206608ef7221000991c0d75eb101ce06581fedc2a74522648ad34'
DEVICE=Path('/sys/bus/pci/devices')/BDF
DEBUG=Path('/sys/kernel/debug')
def sha(b):return hashlib.sha256(b).hexdigest()
def need(ok,msg):
    if not ok:raise RuntimeError(msg)
def save(p,obj):p.write_text(json.dumps(obj,indent=2)+'\n')
def fields(path):return dict(x.split('=',1) for x in path.read_text().split())
def verify_read(path,boot,card,old):
    req=json.loads((path/'request.json').read_text())
    result=json.loads((path/'result.json').read_text())
    state=fields(path/'status.txt')
    data=(path/'data.bin').read_bytes()
    need(req['boot_id']==boot and req['selector']==9 and
         req['length']==len(data)==1048576 and
         sha(data)==result['sha256']==FIRMWARE and
         result['card_after']==card and result['old_after']==old and
         all(state.get(k)=='0' for k in ('status','residual','guard_changes')),
         f'full flash audit {path}')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ('inventory_module','vector_module','handler','firmware',
              'readback0','readback1','out'):
        ap.add_argument('--'+n.replace('_','-'),type=Path,required=True)
    a=ap.parse_args()
    lock=open('/run/lock/i960-loadrun.lock','w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    need(sha(a.firmware.read_bytes())==FIRMWARE and
         sha(a.handler.read_bytes())==HANDLER,'current firmware/handler')
    for n,mod in (('inventory',inventory),('vector',vector)):
        path=getattr(a,n+'_module')
        need(sha(path.read_bytes())==mod.MODULE_SHA and
             not (DEBUG/('accele-'+n)).exists() and
             not Path('/sys/module/'+n+'_command').exists(),
             n+' module preflight')
    card=select(BDF,'accele160',driver='myrsread')
    old=select(OLD,'dac960pg')
    need(old['driver'] is None and
         not list(DEVICE.glob('host*/target*/*/block/*')),'card ownership')
    host,=DEVICE.glob('host*/scsi_host/host*')
    need((host/'stock_descriptor').read_text().startswith('state=0 '),
         'stock descriptor')
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    for p in (a.readback0,a.readback1):verify_read(p,boot,card,old)
    a.out.mkdir(parents=True,exist_ok=False)
    save(a.out/'preflight.json',dict(boot_id=boot,card=card,old=old,
         firmware_sha256=FIRMWARE,handler_sha256=HANDLER,
         inventory_module_sha256=inventory.MODULE_SHA,
         vector_module_sha256=vector.MODULE_SHA))
    cfg=(DEVICE/'config').open('r+b',buffering=0)
    res=(DEVICE/'resource0').open('r+b',buffering=0)
    bar=mmap.mmap(res.fileno(),8192)
    cfg.seek(0x44);original=struct.unpack('<I',cfg.read(4))[0]
    need(original==0xc0000000,'PIATVR unexpected')
    def translate(addr):
        cfg.seek(0x44);cfg.write(struct.pack('<I',addr));cfg.seek(0x44)
        need(struct.unpack('<I',cfg.read(4))[0]==addr,'PIATVR readback')
    def snap(addr):translate(addr);return bytes(bar[4096:8192])
    def write(addr,off,data):
        translate(addr);bar[4096+off:4096+off+len(data)]=data
        need(bytes(bar[4096+off:4096+off+len(data)])==data,'PCI writeback')
    try:
        before=snap(0xc000e000)
        owner=snap(0xc0384000)
        (a.out/'page-before.bin').write_bytes(before)
        (a.out/'owner-before.bin').write_bytes(owner)
        tail=a.handler.read_bytes()[0xf000-0xe1d8:]
        need(before==tail+b'\xff'*(4096-len(tail)),'handler tail/page')
        results={}
        for n,mod in (('inventory',inventory),('vector',vector)):
            module=getattr(a,n+'_module')
            folder=DEBUG/('accele-'+n)
            first,last=mod.FIRST,mod.LAST
            translate(original)
            subprocess.run(['insmod',str(module),'bdf='+BDF],check=True)
            need(fields(folder/'status').get('started')=='0',n+' started')
            (folder/'start').write_text('probe\n')
            deadline=time.monotonic()+5
            while time.monotonic()<deadline:
                s=fields(folder/'status')
                if s.get('done')=='1':break
                time.sleep(.01)
            (a.out/(n+'-status.txt')).write_text((folder/'status').read_text())
            need(s.get('done')=='1' and s.get('status')=='0' and
                 s.get('residual')=='0',n+' uncertain; retain module')
            page=snap(0xc000e000)
            (a.out/(n+'-page.bin')).write_bytes(page)
            need(page[:first]==before[:first] and page[last:]==before[last:],
                 n+' report bounds')
            now=snap(0xc0384000)
            (a.out/(n+'-owner.bin')).write_bytes(now)
            need(now[0x2a0:0xaa0]==owner[0x2a0:0xaa0],n+' owner changed')
            decoded=mod.decode(page)
            write(0xc000e000,first,before[first:last])
            need(snap(0xc000e000)==before,n+' page restore')
            translate(original)
            (folder/'release').write_text('release\n')
            need(fields(folder/'status').get('released')=='1',n+' release')
            subprocess.run(['rmmod',n+'_command'],check=True)
            results[n]=decoded
        save(a.out/'result.json',dict(boot_id=boot,observations=results,
             card_after=select(BDF,'accele160'),old_after=select(OLD,'dac960pg'),
             owner_restored=True,page_restored=True))
        print(json.dumps(results,indent=2))
    finally:
        translate(original);bar.close();res.close();cfg.close()
if __name__=='__main__':main()

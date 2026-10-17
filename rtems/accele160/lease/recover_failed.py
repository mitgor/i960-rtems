#!/usr/bin/env python3
"""Release a completed RTEMS lease test after preserving evidence."""
import fcntl,json,mmap,struct,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'host/accele160/lease_probe'))
from run_lease import BDF,OLD,PAGE,DEVICE,DEBUG,need,fields,sha
sys.path.insert(0,str(ROOT/'rtems/transport'))
from card_select import select

out=Path(sys.argv[1]);out.mkdir(exist_ok=True)
lock=open('/run/lock/i960-loadrun.lock','w')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
need(select(BDF,'accele160',driver='myrsread')['driver']=='myrsread' and
     select(OLD,'dac960pg')['driver'] is None,'card identity')
root=out.parent
before=(root/'page-before.bin').read_bytes()
reserved=(root/'page-reserved.bin').read_bytes()
owner=(root/'owner-before.bin').read_bytes()
owned=(root/'owner-reserved.bin').read_bytes()
stage_before=(root/'stage-before.bin').read_bytes()
state=fields(DEBUG/'accele-ram-admit/status')
need(state.get('done')=='1' and state.get('status') in ('0','2'),
     'not a completed admission')
cfg=(DEVICE/'config').open('r+b',buffering=0)
res=(DEVICE/'resource0').open('r+b',buffering=0)
bar=mmap.mmap(res.fileno(),2*PAGE)
cfg.seek(0x44);original=struct.unpack('<I',cfg.read(4))[0]
need(original==0xc0000000,'unexpected PIATVR')
def translate(addr):
    cfg.seek(0x44);cfg.write(struct.pack('<I',addr));cfg.seek(0x44)
    need(struct.unpack('<I',cfg.read(4))[0]==addr,'PIATVR readback')
def snap(addr):translate(addr);return bytes(bar[PAGE:2*PAGE])
def write(addr,off,data):
    translate(addr);bar[PAGE+off:PAGE+off+len(data)]=data
    need(bytes(bar[PAGE+off:PAGE+off+len(data)])==data,'PCI writeback')
try:
    ptr=struct.unpack_from('<I',reserved,0x828)[0]
    need(ptr==0xc0710000,'grant pointer')
    page=snap(0xc000e000)
    (out/'failed-page.bin').write_bytes(page)
    expect=bytearray(reserved)
    expect[0x820:0x830]=before[0x820:0x830]
    expect[0xa00:0xa80]=page[0xa00:0xa80]
    need(page==expect,'loader page changed outside test/report areas')
    need(snap(0xc0384000)[0x2a0:0xaa0]==owned[0x2a0:0xaa0],
         'owner records changed')
    need(snap(ptr+0x7e000)==stage_before,'stage was not restored')
    for off,length in ((0xa00,0x20),(0xa20,0x1c),(0xa40,0x20),(0xa60,0x20)):
        write(0xc000e000,off,before[off:off+length])
    need(snap(0xc000e000)==expect[:0xa00]+before[0xa00:],
         'loader page restore under grant')
    translate(original)
    (DEBUG/'accele-ram-admit/release').write_text('release\n')
    need(fields(DEBUG/'accele-ram-admit/status').get('released')=='1',
         'admit release uncertain')
    subprocess.run(['rmmod','admit_command'],check=True)
    subprocess.run(['rmmod','copy_command'],check=True)
    subprocess.run(['rmmod','digest_command'],check=True)
    write(0xc000e000,0x820,b'\xa5'*16)
    translate(original)
    (DEBUG/'accele-release/start').write_text('probe\n')
    end=time.monotonic()+5
    while time.monotonic()<end:
        s=fields(DEBUG/'accele-release/status')
        if s.get('done')=='1':break
        time.sleep(.01)
    need(s.get('done')=='1' and s.get('status')=='0' and
         s.get('residual')=='0','release uncertain')
    released=snap(0xc000e000)
    need(struct.unpack_from('<4I',released,0x820)==
         (0x45455246,0x16161051,ptr,0x80000),'release report')
    need(snap(0xc0384000)[0x2a0:0xaa0]==owner[0x2a0:0xaa0],
         'owner records not restored')
    write(0xc000e000,0x820,before[0x820:0x830])
    need(snap(0xc000e000)==before and
         snap(ptr+0x7e000)==stage_before,'final page/stage restore')
    translate(original)
    (DEBUG/'accele-release/release').write_text('release\n')
    subprocess.run(['rmmod','release_command'],check=True)
    (out/'result.json').write_text(json.dumps(dict(
        retained_page_sha256=sha(page),status=int(state['status']),grant_released=True,
        owner_restored=True,loader_page_restored=True,
        stage_restored=True),indent=2)+'\n')
finally:
    translate(original);bar.close();res.close();cfg.close()

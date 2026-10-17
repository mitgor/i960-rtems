#!/usr/bin/env python3
"""Finish the completed copy after the rejected even-page PCI readback."""
import fcntl,mmap,struct,subprocess,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'rtems/transport'))
from card_select import select
from run_lease import BDF,OLD,PAGE,DEVICE,DEBUG,fnv,need,fields

root=Path(sys.argv[1])
lock=open('/run/lock/i960-loadrun.lock','w')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
need(select(BDF,'accele160',driver='myrsread')['driver']=='myrsread' and
     select(OLD,'dac960pg')['driver'] is None,'card identity')
before=(root/'page-before.bin').read_bytes()
reserved=(root/'page-reserved.bin').read_bytes()
owner=(root/'owner-before.bin').read_bytes()
owned=(root/'owner-reserved.bin').read_bytes()
stage_before=(root/'stage-before.bin').read_bytes()
payload=(root/'timeout/stage-0.bin').read_bytes()
need(len(payload)==PAGE and fields(DEBUG/'accele-copy/status').get('done')=='1',
     'copy not complete')
cfg=(DEVICE/'config').open('r+b',buffering=0)
res=(DEVICE/'resource0').open('r+b',buffering=0)
bar=mmap.mmap(res.fileno(),2*PAGE)
cfg.seek(0x44);original=struct.unpack('<I',cfg.read(4))[0]
need(original==0xc0000000,'PIATVR unexpected')
def translate(addr):
    cfg.seek(0x44);cfg.write(struct.pack('<I',addr));cfg.seek(0x44)
    need(struct.unpack('<I',cfg.read(4))[0]==addr,'PIATVR readback')
def snap(addr):
    translate(addr);return bytes(bar[PAGE:2*PAGE])
def write(addr,off,data):
    translate(addr);bar[PAGE+off:PAGE+off+len(data)]=data
    need(bytes(bar[PAGE+off:PAGE+off+len(data)])==data,'PCI writeback')
try:
    ptr=struct.unpack_from('<I',reserved,0x828)[0]
    need(ptr==0xc0710000,'grant pointer')
    stage=ptr+0x7e000
    need(snap(stage)==payload,'stage contents')
    page=snap(0xc000e000)
    (root/'recovery-copy-page.bin').write_bytes(page)
    expect=bytearray(reserved)
    expect[0x820:0x830]=struct.pack('<4I',0x59504f43,0x16161061,0,fnv(payload))
    expect[0x860:0x870]=struct.pack('<4I',0x59504f43,0x16161061,0,fnv(payload))
    need(page==expect,'completed copy changed loader page')
    need(snap(0xc0384000)[0x2a0:0xaa0]==owned[0x2a0:0xaa0],
         'allocated owner records changed')
    write(stage,0,stage_before)
    need(snap(stage)==stage_before,'stage restoration')
    write(0xc000e000,0x860,before[0x860:0x870])
    write(0xc000e000,0x820,before[0x820:0x830])
    need(snap(0xc000e000)==
         reserved[:0x820]+before[0x820:0x830]+reserved[0x830:],
         'page not restored under grant')
    translate(original)
    (DEBUG/'accele-copy/release').write_text('release\n')
    subprocess.run(['rmmod','copy_command'],check=True)
    subprocess.run(['rmmod','digest_command'],check=True)
    subprocess.run(['rmmod','admit_command'],check=True)
    write(0xc000e000,0x820,b'\xa5'*16)
    translate(original)
    (DEBUG/'accele-release/start').write_text('probe\n')
    import time
    end=time.monotonic()+5
    while time.monotonic()<end:
        state=fields(DEBUG/'accele-release/status')
        if state.get('done')=='1':break
        time.sleep(.02)
    need(state.get('done')=='1' and state.get('status')=='0' and
         state.get('residual')=='0','release uncertain; retain module')
    page=snap(0xc000e000)
    need(struct.unpack_from('<4I',page,0x820)==
         (0x45455246,0x16161051,ptr,0x80000),'release report')
    need(snap(0xc0384000)[0x2a0:0xaa0]==owner[0x2a0:0xaa0],
         'owner records not restored')
    write(0xc000e000,0x820,before[0x820:0x830])
    need(snap(0xc000e000)==before,'loader page not restored')
    translate(original)
    (DEBUG/'accele-release/release').write_text('release\n')
    subprocess.run(['rmmod','release_command'],check=True)
    (root/'recovery-result.json').write_text(json.dumps(dict(
        copy_completed=True,grant_released=True,stage_restored=True,
        owner_restored=True,loader_page_restored=True),indent=2)+'\n')
finally:
    translate(original);bar.close();res.close();cfg.close()

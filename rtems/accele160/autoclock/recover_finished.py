#!/usr/bin/env python3
"""Finish a completed admission after a host-side validation failure.

Only handles a returned op-13 call with exact saved page, grant, and stage.
An active or ambiguous handler is intentionally left untouched.
"""
import fcntl,mmap,struct,sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'host/accele160/lease_probe'))
from run_lease import BDF,OLD,PAGE,DEVICE,DEBUG,need,status,release,command
sys.path.insert(0,str(ROOT/'rtems/transport'))
from card_select import select

def main():
    root=Path(sys.argv[1]); run=root/(sys.argv[2] if len(sys.argv)>2 else 'stop')
    lock=open('/run/lock/i960-loadrun.lock','w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    need(status('ram-admit').get('done')=='1' and
         status('ram-admit').get('status')=='0' and
         status('ram-admit').get('residual')=='0', 'admit not returned cleanly')
    need(status('release').get('started')=='0','release already started')
    need(select(BDF,'accele160',driver='myrsread')['bdf']==BDF and
         select(OLD,'dac960pg')['driver'] is None,'card selection')
    before=(root/'page-before.bin').read_bytes()
    reserved=(root/'page-reserved.bin').read_bytes()
    owned=(root/'owner-reserved.bin').read_bytes()
    page_after=(run/'page-after.bin').read_bytes()
    need(struct.unpack_from('<7I',page_after,0xa20)[0:3]==
         (0x314e5552,0x161610d1,0x31454e4f),'completed RTEMS report')
    cfg=(DEVICE/'config').open('r+b',buffering=0)
    res=(DEVICE/'resource0').open('r+b',buffering=0)
    bar=mmap.mmap(res.fileno(),2*PAGE)
    cfg.seek(0x44);original=struct.unpack('<I',cfg.read(4))[0]
    need(original==0xc0000000,'translation changed')
    def translate(addr):
        cfg.seek(0x44);cfg.write(struct.pack('<I',addr))
        cfg.seek(0x44);need(struct.unpack('<I',cfg.read(4))[0]==addr,'translation')
    def snap(addr):translate(addr);return bytes(bar[PAGE:2*PAGE])
    def write(addr,off,data):
        translate(addr);bar[PAGE+off:PAGE+off+len(data)]=data
        need(bytes(bar[PAGE+off:PAGE+off+len(data)])==data,'writeback')
    ptr=struct.unpack_from('<I',reserved,0x828)[0]
    need(ptr==0xc0710000 and snap(0xc000e000)==page_after and
         snap(0xc0384000)[0x2a0:0xaa0]==owned[0x2a0:0xaa0] and
         snap(ptr+0x7e000)==(root/'stage-before.bin').read_bytes(),
         'live state differs from saved completed call')
    try:
        for lo,hi in ((0xa00,0xa20),(0xa20,0xa3c),(0xa40,0xa60),
                      (0xa60,0xa80)):
            write(0xc000e000,lo,before[lo:hi])
        need(snap(0xc000e000)==
             reserved[:0x820]+before[0x820:0x830]+reserved[0x830:],
             'page restoration under grant')
        translate(original);release('ram-admit','admit')
        write(0xc000e000,0x820,b'\xa5'*16)
        translate(original);command('release',root)
        end=snap(0xc000e000)
        need(struct.unpack_from('<4I',end,0x820)==
             (0x45455246,0x16161051,ptr,0x80000),'grant release report')
        need(snap(0xc0384000)[0x2a0:0xaa0]==
             (root/'owner-before.bin').read_bytes()[0x2a0:0xaa0],
             'owner release')
        write(0xc000e000,0x820,before[0x820:0x830])
        need(snap(0xc000e000)==before,'final page')
        translate(original);release('release','release')
        subprocess.run(['rmmod','copy_command'],check=True)
        subprocess.run(['rmmod','digest_command'],check=True)
        (root/'host-recovery.txt').write_text(
            'Completed op13; exact page, grant, stage and owner restored. '
            'No active handler or loaded command module remains.\n')
    finally:
        translate(original);bar.close();res.close();cfg.close()

if __name__=='__main__':main()

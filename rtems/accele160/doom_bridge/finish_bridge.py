#!/usr/bin/env python3
"""Finish and audit a retained Doom bridge after host-side interruption."""
from run_bridge import *

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    lock=open('/run/lock/i960-loadrun.lock','w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    run=a.out/'persist'
    need(run.joinpath('frame.bin').exists() and
         run.joinpath('bridge-receipts.json').exists(),'transport evidence missing')
    need(status('ram-admit').get('started')=='1' and
         status('ram-admit').get('done')=='0','callback not retained')
    cfg=(DEVICE/'config').open('r+b',buffering=0)
    res=(DEVICE/'resource0').open('r+b',buffering=0)
    bar=mmap.mmap(res.fileno(),2*PAGE)
    cfg.seek(0x44);original=struct.unpack('<I',cfg.read(4))[0]
    need(original==0xc0000000,'PIATVR')
    def translate(addr):
        cfg.seek(0x44);cfg.write(struct.pack('<I',addr));cfg.seek(0x44)
        need(struct.unpack('<I',cfg.read(4))[0]==addr,'PIATVR readback')
    def snap(addr):
        translate(addr);return bytes(bar[PAGE:2*PAGE])
    def write(addr,off,data):
        translate(addr);bar[PAGE+off:PAGE+off+len(data)]=data
        need(bytes(bar[PAGE+off:PAGE+off+len(data)])==data,'PCI writeback')
    try:
        page=snap(0xc000e000)
        bank=struct.unpack_from('<16I',page,0xb00)
        claim=struct.unpack_from('<16I',page,0xb40)
        bridge=struct.unpack_from('<20I',page,0xb80)
        ready=(run/'ready-page.bin').read_bytes()
        need(page[0xb00:0xb40]==ready[0xb00:0xb40] and
             bridge[8]==232 and bridge[9]==0 and bridge[11:14]==(867792,1,1)
             and bridge[15]==867792 and bridge[17]==1,
             'complete bridge before STOP')
        need(claim[0:4]==(0x314d5241,2048,0x833aedc5,0) and
             claim[5:7]==(0,0),'claim and error state')
        (run/'prestop-page.bin').write_bytes(page)
        first=claim[4]
        time.sleep(.25)
        later=snap(0xc000e000)
        heart=struct.unpack_from('<16I',later,0xb40)
        need(heart[4]>first and heart[5:7]==(0,0) and
             status('ram-admit').get('done')=='0','live RTEMS heartbeat')
        write(0xc000e000,0xa4c,struct.pack('<I',0x504f5453))
        started=time.monotonic()
        while time.monotonic()-started<20:
            page=snap(0xc000e000)
            state=struct.unpack_from('<16I',page,0xb40)
            if state[5]==0x45495551:break
            time.sleep(.01)
        (run/'quiescent-page.bin').write_bytes(page)
        (run/'admit-pending-status.txt').write_text(
            (DEBUG/'accele-ram-admit/status').read_text())
        need(state[5]==0x45495551 and state[6]==0 and
             status('ram-admit').get('done')=='0' and
             struct.unpack_from('<I',page,0xa54)[0]==0x214b4341,
             'reboot-only quiescent ownership')
        need(struct.unpack_from('<16I',page,0xb00)==bank,
             'full-bank proof retained')
        owned=(a.out/'owner-reserved.bin').read_bytes()
        need(snap(0xc0384000)[0x2a0:0xaa0]==owned[0x2a0:0xaa0],
             'grant ownership retained')
        old=select(OLD,'dac960pg')
        need(old['driver'] is None,'old card untouched')
        frame=(run/'frame.bin').read_bytes()
        receipts=json.loads((run/'bridge-receipts.json').read_text())
        boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        save(a.out/'result.json',dict(boot_id=boot,image_sha256=IMAGE,
             kernel_sha256=KERNEL,firmware_sha256=FIRMWARE,
             full_audits_before=True,bank_report=[f'0x{x:08x}' for x in bank],
             claim_report=[f'0x{x:08x}' for x in state],
             bridge_report=[f'0x{x:08x}' for x in
                            struct.unpack_from('<20I',page,0xb80)],
             upload_bytes=867792,upload_commands=sum(x['op']==1 for x in receipts),
             frame_sha256=sha(frame),frame_fnv=f'0x{fnv(frame):08x}',
             heartbeat_before=first,heartbeat_after=heart[4],
             release='reboot-only',grant_retained=True,
             card=select(BDF,'accele160'),old=old))
        print('Doom image admitted; WAD header and diagnostic frame round-trip passed; STOP quiescent')
    finally:
        translate(original);bar.close();res.close();cfg.close()

if __name__=='__main__':main()

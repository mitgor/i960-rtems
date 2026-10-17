#!/usr/bin/env python3
"""One-lease, two-image RAM-only acceptance under full owner/page audits."""
import argparse, fcntl, hashlib, json, mmap, struct, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'rtems/transport'))
from card_select import select

BDF, OLD = '0000:37:09.1', '0000:37:04.1'
IMAGE_SHA = '1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
HANDLER_SHA = '8d8c79c3b8c206608ef7221000991c0d75eb101ce06581fedc2a74522648ad34'
PROBE_SHA = ('c390d091eeada11a10474b197d6f126bbaef1dc469eda981c9b67e56bc15f488',
             '7519cfca29606c0b2f9e9282a4823ef70a2025d99c1f84213658823cad4f0dc6')
NONCE = 0x161610d1
PAGE = 4096
DEVICE = Path('/sys/bus/pci/devices') / BDF
DEBUG = Path('/sys/kernel/debug')

def sha(data): return hashlib.sha256(data).hexdigest()
def need(test, why):
    if not test: raise RuntimeError(why)
def fields(path): return dict(p.split('=',1) for p in path.read_text().split())
def save(path, obj): path.write_text(json.dumps(obj,indent=2)+'\n')
def fnv(data):
    h=0x811c9dc5
    for b in data: h=((h^b)*0x01000193)&0xffffffff
    return h
def dbg(name): return DEBUG/f'accele-{name}'
def state(name): return fields(dbg(name)/'status')
def start(name, out, want=0):
    need(state(name).get('started')=='0', f'{name} already started')
    (dbg(name)/'start').write_text('probe\n')
    end=time.monotonic()+5
    while time.monotonic()<end:
        result=state(name)
        if result.get('done')=='1': break
        time.sleep(.02)
    (out/f'{name}-status.txt').write_text((dbg(name)/'status').read_text())
    need(result.get('done')=='1' and result.get('status')==str(want) and
         result.get('residual')=='0', f'{name} uncertain; retain command and grant')
    return result
def release(name):
    (dbg(name)/'release').write_text('release\n')
    need(state(name).get('released')=='1', f'{name} release failed')
def insmod(name,path): subprocess.run(['insmod',str(path),'bdf='+BDF],check=True)
def rmmod(name): subprocess.run(['rmmod',name+'_command'],check=True)

def verify_read(path, boot, card, old):
    req=json.loads((path/'request.json').read_text())
    result=json.loads((path/'result.json').read_text())
    status=fields(path/'status.txt')
    data=(path/'data.bin').read_bytes()
    need(req['boot_id']==boot and req['selector']==9 and req['length']==1048576 and
         len(data)==1048576 and sha(data)==result['sha256']==IMAGE_SHA and
         result['card_after']==card and result['old_after']==old and
         all(status.get(x)=='0' for x in ('status','residual','guard_changes')),
         f'full read failed: {path}')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('reserve_module','release_module','copy_module','digest_module',
                 'admit_module','handler','image','probe1','probe2','readback0',
                 'readback1','out'):
        p.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    a=p.parse_args()
    lock=open('/run/lock/i960-loadrun.lock','w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    need(sha(a.image.read_bytes())==IMAGE_SHA and
         sha(a.handler.read_bytes())==HANDLER_SHA,'firmware/handler identity')
    for i,path in enumerate((a.probe1,a.probe2)):
        need(sha(path.read_bytes())==PROBE_SHA[i] and len(path.read_bytes())==48,
             f'probe {i+1} identity')
    for name in ('reserve','release','copy','digest','admit'):
        path=getattr(a,name+'_module')
        directory = 'ram-admit' if name == 'admit' else name
        need(path.exists() and not dbg(directory).exists() and
             not Path('/sys/module',name+'_command').exists(),
             f'{name} module unavailable/already retained')
    card=select(BDF,'accele160',driver='myrsread')
    old=select(OLD,'dac960pg')
    need(old['driver'] is None,'old card bound')
    need(not list(DEVICE.glob('host*/target*/*/block/*')),'block device present')
    host,=DEVICE.glob('host*/scsi_host/host*')
    need((host/'stock_descriptor').read_text().startswith('state=0 '),
         'stock descriptor active')
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    for rd in (a.readback0,a.readback1): verify_read(rd,boot,card,old)
    a.out.mkdir(parents=True,exist_ok=False)
    save(a.out/'preflight.json',dict(boot_id=boot,card=card,old=old,
        image_sha256=IMAGE_SHA,handler_sha256=HANDLER_SHA,
        probe_sha256=PROBE_SHA,
        modules={n:sha(getattr(a,n+'_module').read_bytes()) for n in
                 ('reserve','release','copy','digest','admit')}))
    cfg=(DEVICE/'config').open('r+b',buffering=0)
    resource=(DEVICE/'resource0').open('r+b',buffering=0)
    bar=mmap.mmap(resource.fileno(),PAGE*2)
    cfg.seek(0x44); original=struct.unpack('<I',cfg.read(4))[0]
    need(original==0xc0000000,'PIATVR unexpected')
    def translate(address):
        cfg.seek(0x44);cfg.write(struct.pack('<I',address));cfg.seek(0x44)
        need(struct.unpack('<I',cfg.read(4))[0]==address,'PIATVR readback')
    def snap(address):
        translate(address);return bytes(bar[PAGE:2*PAGE])
    def write(address,offset,data):
        translate(address);bar[PAGE+offset:PAGE+offset+len(data)]=data
        need(bytes(bar[PAGE+offset:PAGE+offset+len(data)])==data,'MMIO readback')
    try:
        before=snap(0xc000e000); owner=snap(0xc0384000)
        (a.out/'page-before.bin').write_bytes(before)
        (a.out/'owner-before.bin').write_bytes(owner)
        tail=a.handler.read_bytes()[0xf000-0xe1d8:]
        need(before==tail+b'\xff'*(PAGE-len(tail)),'loader code tail/page preflight')
        for name in ('reserve','release','copy','digest','admit'):
            insmod(name,getattr(a,name+'_module'))
        write(0xc000e000,0x820,b'\xa5'*16)
        translate(original)
        start('reserve',a.out)
        reserved=snap(0xc000e000);(a.out/'page-reserved.bin').write_bytes(reserved)
        ptr=struct.unpack_from('<I',reserved,0x828)[0]
        need(struct.unpack_from('<4I',reserved,0x840)==
             (0x56525352,ptr,0x80000,0x96016004) and ptr==0xc0710000,
             'unexpected grant')
        owned=snap(0xc0384000);(a.out/'owner-reserved.bin').write_bytes(owned)
        first=(ptr-0xc0000000)//0x8000
        for i in range(256):
            bc,bo=(struct.unpack_from('<I',owner,0x2a0+i*4)[0],
                   struct.unpack_from('<I',owner,0x6a0+i*4)[0])
            rc,ro=(struct.unpack_from('<I',owned,0x2a0+i*4)[0],
                   struct.unpack_from('<I',owned,0x6a0+i*4)[0])
            need((rc,ro)==((16,0x96016004) if first<=i<first+16 else (bc,bo)),
                 'grant owner metadata')
            if first<=i<first+16: need((bc,bo)==(0,0),'grant overlap')
        write(0xc000e000,0x820,before[0x820:0x830])
        translate(original);release('reserve');rmmod('reserve')
        stage=ptr+0x7e000;stage_before=snap(stage)
        (a.out/'stage-before.bin').write_bytes(stage_before)
        outcomes=[]
        for ordinal,probe in enumerate((a.probe1,a.probe2),1):
            run=a.out/f'run-{ordinal}';run.mkdir()
            payload=probe.read_bytes().ljust(PAGE,b'\0')
            digest=fnv(payload)
            save(run/'manifest-host.json',dict(image_sha256=sha(payload),
                 bytes=len(payload),entry_offset=0,fnv=f'0x{digest:08x}'))
            write(stage,0,payload)
            need(snap(stage)==payload,'stage payload readback')
            (run/'stage-readback.bin').write_bytes(payload)
            copy=struct.pack('<4I',0x59504f43,0x16161061,0,digest)
            write(0xc000e000,0x860,copy)
            write(0xc000e000,0x820,b'\xa5'*16)
            translate(original);start('copy',run)
            copied=snap(0xc000e000);(run/'copy-page.bin').write_bytes(copied)
            need(struct.unpack_from('<4I',copied,0x820)==
                 (0x59504f43,0x16161061,0,digest) and
                 copied[:0x820]==reserved[:0x820] and
                 copied[0x830:0x860]==reserved[0x830:0x860] and
                 copied[0x870:]==reserved[0x870:], 'copy report/page drift')
            need(snap(0xc0384000)[0x2a0:0xaa0]==owned[0x2a0:0xaa0],
                 'owner drift after copy')
            write(0xc000e000,0x860,before[0x860:0x870])
            write(0xc000e000,0x820,before[0x820:0x830])
            write(stage,0,stage_before)
            need(snap(stage)==stage_before,'stage restore')
            translate(original);release('copy');rmmod('copy')
            # Confirm the whole admitted page by the card's existing digest.
            control=struct.pack('<4I',0x48534148,0x16161071,1,digest)
            write(0xc000e000,0x870,control)
            write(0xc000e000,0x830,b'\xa5'*16)
            translate(original);start('digest',run)
            hashed=snap(0xc000e000);(run/'digest-page.bin').write_bytes(hashed)
            need(struct.unpack_from('<4I',hashed,0x830)==
                 (0x48534148,0x16161071,1,digest),'card digest')
            write(0xc000e000,0x870,before[0x870:0x880])
            write(0xc000e000,0x830,before[0x830:0x840])
            translate(original);release('digest');rmmod('digest')
            # Each rejection must leave both the report and owner array alone.
            good=struct.pack('<8I',0x314d4152,NONCE,ptr,0x80000,1,0,digest,0)
            for label,bad in (('bad-hash',good[:24]+struct.pack('<I',digest^1)+good[28:]),
                              ('bad-entry',good[:20]+struct.pack('<I',4096)+good[24:]),
                              ('bad-nonce',good[:4]+struct.pack('<I',NONCE^1)+good[8:])):
                negative=run/label; negative.mkdir()
                write(0xc000e000,0xa00,bad)
                write(0xc000e000,0xa20,b'\xa5'*28)
                translate(original);start('ram-admit',negative,2)
                rejected=snap(0xc000e000)
                (negative/'page.bin').write_bytes(rejected)
                need(rejected[0xa20:0xa3c]==b'\xa5'*28 and
                     snap(0xc0384000)[0x2a0:0xaa0]==owned[0x2a0:0xaa0],
                     f'{label} rejection changed report/owners')
                write(0xc000e000,0xa00,before[0xa00:0xa20])
                write(0xc000e000,0xa20,before[0xa20:0xa3c])
                translate(original);release('ram-admit');rmmod('admit')
                insmod('admit',a.admit_module)
            write(0xc000e000,0xa00,good)
            write(0xc000e000,0xa20,b'\xa5'*28)
            translate(original)
            started=time.monotonic();start('ram-admit',run)
            elapsed=time.monotonic()-started
            page=snap(0xc000e000);(run/'page-after.bin').write_bytes(page)
            after_owner=snap(0xc0384000);(run/'owner-after.bin').write_bytes(after_owner)
            expected=bytearray(reserved)
            expected[0x820:0x830]=before[0x820:0x830]
            expected[0xa00:0xa20]=good
            expected[0xa20:0xa3c]=page[0xa20:0xa3c]
            need(page==expected,'admission wrote outside manifest/report')
            need(after_owner[0x2a0:0xaa0]==owned[0x2a0:0xaa0],
                 'owner drift after admission')
            words=struct.unpack_from('<7I',page,0xa20)
            need(words[:6]==(0x314e5552,NONCE,0x31454e4f,ptr,1,digest)
                 and words[6]==0x16010000+ordinal, 'payload/report mismatch')
            write(0xc000e000,0xa00,before[0xa00:0xa20])
            write(0xc000e000,0xa20,before[0xa20:0xa3c])
            need(snap(0xc000e000)==reserved[:0x820]+before[0x820:0x830]+reserved[0x830:],
                 'loader page not restored under grant')
            translate(original);release('ram-admit');rmmod('admit')
            outcomes.append(dict(ordinal=ordinal,probe_sha256=PROBE_SHA[ordinal-1],
                                 page_sha256=sha(payload),fnv=f'0x{digest:08x}',
                                 elapsed_ms=round(elapsed*1000,3),report=list(words)))
            if ordinal==1:
                insmod('copy',a.copy_module)
                insmod('digest',a.digest_module)
                insmod('admit',a.admit_module)
        write(0xc000e000,0x820,b'\xa5'*16)
        translate(original);start('release',a.out)
        released=snap(0xc000e000);(a.out/'page-after-release.bin').write_bytes(released)
        need(struct.unpack_from('<4I',released,0x820)==
             (0x45455246,0x16161051,ptr,0x80000),'release record')
        owner_after=snap(0xc0384000)
        (a.out/'owner-after.bin').write_bytes(owner_after)
        need(owner_after[0x2a0:0xaa0]==owner[0x2a0:0xaa0],
             'owner table not restored')
        write(0xc000e000,0x820,before[0x820:0x830])
        need(snap(0xc000e000)==before,'full loader page not restored')
        translate(original);release('release');rmmod('release')
        save(a.out/'result.json',dict(boot_id=boot,grant=ptr,
             runs=outcomes,full_audits=True,page_restored=True,
             owners_restored=True,staging_restored=True,
             card_after=select(BDF,'accele160'),old_after=select(OLD,'dac960pg')))
        print(json.dumps(outcomes,indent=2))
    finally:
        translate(original);bar.close();resource.close();cfg.close()

if __name__=='__main__': main()

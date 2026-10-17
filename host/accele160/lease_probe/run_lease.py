#!/usr/bin/env python3
"""RAM-only owned-stack, STOP and finite-poll admission tests on AcceleRAID."""
import argparse, fcntl, hashlib, json, mmap, struct, subprocess, sys, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'rtems/transport'))
from card_select import select

BDF,OLD='0000:37:09.1','0000:37:04.1'
FIRMWARE='1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
HANDLER='8d8c79c3b8c206608ef7221000991c0d75eb101ce06581fedc2a74522648ad34'
IMAGE='66c11b9cc5907ed8296240e37fa150ce34883ca798111f3670cb209a6a78082f'
PROBE='05d9733fadfc2d56fbe03f34188556571d0d27e3f648abe80c804d07f06f82bf'
ADMIT='528767e0f94c5ce36d156a71b73ea8bfd9ae5e99013211b89e46a44096acabe5'
MODULES={'reserve':'d5dc1cf2dddba559ea4ff5ebf7bac1ae32f462f27dd968b8964f0cd20b47c945',
         'release':'bbfbe079b86ba1503efcfcce4c0c7ee5e1ad2fc662ded669766bdb7d38a3ecfa',
         'copy':'6dd7dc40be4c51e65dce65978b3fdda3256e54928034d7acfe451a946caf1ec6',
         'digest':'db97abc60007d96017c4aaed6f86f5f155988b2948993f2f5b3f81cc964ad6b1',
         'admit':ADMIT}
NONCE=0x161610d1
PAGE=4096
DEVICE=Path('/sys/bus/pci/devices')/BDF
DEBUG=Path('/sys/kernel/debug')

def need(ok,reason):
    if not ok: raise RuntimeError(reason)
def sha(data):return hashlib.sha256(data).hexdigest()
def fields(path):return dict(x.split('=',1) for x in path.read_text().split())
def save(path,obj):path.write_text(json.dumps(obj,indent=2)+'\n')
def fnv(data):
    h=0x811c9dc5
    for b in data:h=((h^b)*0x01000193)&0xffffffff
    return h
def status(name):return fields(DEBUG/f'accele-{name}/status')
def insmod(path):subprocess.run(['insmod',str(path),'bdf='+BDF],check=True)
def done(name,out,want=0,limit=5):
    end=time.monotonic()+limit
    while time.monotonic()<end:
        s=status(name)
        if s.get('done')=='1':break
        time.sleep(.01)
    (out/f'{name}-status.txt').write_text((DEBUG/f'accele-{name}/status').read_text())
    need(s.get('done')=='1' and s.get('status')==str(want) and
         s.get('residual')=='0',f'{name} uncertain; retain module/grant')
    return s
def command(name,out,want=0):
    need(status(name).get('started')=='0',f'{name} already started')
    (DEBUG/f'accele-{name}/start').write_text('probe\n')
    return done(name,out,want)
def release(name,module):
    (DEBUG/f'accele-{name}/release').write_text('release\n')
    need(status(name).get('released')=='1',f'{name} release failed')
    subprocess.run(['rmmod',module+'_command'],check=True)
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
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('reserve_module','release_module','copy_module','digest_module',
              'admit_module','handler','firmware','probe','image',
              'readback0','readback1','out'):
        p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
    a=p.parse_args()
    lock=open('/run/lock/i960-loadrun.lock','w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for n,want in [('handler',HANDLER),('firmware',FIRMWARE),
                   ('probe',PROBE),('image',IMAGE)]:
        need(sha(getattr(a,n).read_bytes())==want,f'{n} identity')
    payload=a.image.read_bytes()
    need(len(payload)==2*PAGE and payload[:448]==a.probe.read_bytes() and
         payload[448:PAGE]==b'\0'*(PAGE-448) and
         payload[PAGE:]==b'\xa5'*PAGE,'two-page payload layout')
    digest=fnv(payload)
    need(digest==0x4462f72b,'whole-image FNV')
    for n,want in MODULES.items():
        path=getattr(a,n+'_module')
        debug='ram-admit' if n=='admit' else n
        need(sha(path.read_bytes())==want and
             not Path('/sys/module',n+'_command').exists() and
             not (DEBUG/f'accele-{debug}').exists(),f'{n} module preflight')
    card=select(BDF,'accele160',driver='myrsread')
    old=select(OLD,'dac960pg')
    need(old['driver'] is None,'old card bound')
    need(not list(DEVICE.glob('host*/target*/*/block/*')),'block device present')
    host,=DEVICE.glob('host*/scsi_host/host*')
    need((host/'stock_descriptor').read_text().startswith('state=0 '),
         'stock descriptor active')
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    for rd in (a.readback0,a.readback1):verify_read(rd,boot,card,old)
    a.out.mkdir(parents=True,exist_ok=False)
    save(a.out/'preflight.json',dict(boot_id=boot,card=card,old=old,
         firmware_sha256=FIRMWARE,handler_sha256=HANDLER,image_sha256=IMAGE,
         probe_sha256=PROBE,fnv=f'0x{digest:08x}',modules=MODULES))
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
    def ownercheck(base):
        got=snap(0xc0384000)
        need(got[0x2a0:0xaa0]==base[0x2a0:0xaa0],
             'allocator count/owner records changed')
        return got
    try:
        before=snap(0xc000e000);owner=snap(0xc0384000)
        (a.out/'page-before.bin').write_bytes(before)
        (a.out/'owner-before.bin').write_bytes(owner)
        tail=a.handler.read_bytes()[0xf000-0xe1d8:]
        need(before==tail+b'\xff'*(PAGE-len(tail)),'exact handler tail/page')
        for n in MODULES:insmod(getattr(a,n+'_module'))
        write(0xc000e000,0x820,b'\xa5'*16)
        translate(original);command('reserve',a.out)
        reserved=snap(0xc000e000)
        (a.out/'page-reserved.bin').write_bytes(reserved)
        ptr=struct.unpack_from('<I',reserved,0x828)[0]
        need(ptr==0xc0710000 and struct.unpack_from('<4I',reserved,0x840)==
             (0x56525352,ptr,0x80000,0x96016004),'grant')
        owned=snap(0xc0384000)
        (a.out/'owner-reserved.bin').write_bytes(owned)
        first=(ptr-0xc0000000)//0x8000
        for i in range(256):
            bc,bo=(struct.unpack_from('<I',owner,0x2a0+i*4)[0],
                   struct.unpack_from('<I',owner,0x6a0+i*4)[0])
            rc,ro=(struct.unpack_from('<I',owned,0x2a0+i*4)[0],
                   struct.unpack_from('<I',owned,0x6a0+i*4)[0])
            need((rc,ro)==((16,0x96016004) if first<=i<first+16 else (bc,bo)),
                 'owner grant metadata')
            if first<=i<first+16:need((bc,bo)==(0,0),'grant overlap')
        write(0xc000e000,0x820,before[0x820:0x830])
        translate(original);release('reserve','reserve')
        stage=ptr+0x7e000;stage_before=snap(stage)
        (a.out/'stage-before.bin').write_bytes(stage_before)
        results=[]
        for number,mode in enumerate(('timeout','stop')):
            run=a.out/mode;run.mkdir()
            for index in (0,1):
                page=payload[index*PAGE:(index+1)*PAGE]
                write(stage,0,page)
                need(snap(stage)==page,'staging readback')
                (run/f'stage-{index}.bin').write_bytes(page)
                copy=struct.pack('<4I',0x59504f43,0x16161061,index,fnv(page))
                write(0xc000e000,0x860,copy)
                write(0xc000e000,0x820,b'\xa5'*16)
                translate(original);command('copy',run)
                cp=snap(0xc000e000)
                (run/f'copy-{index}-page.bin').write_bytes(cp)
                need(struct.unpack_from('<4I',cp,0x820)==
                     (0x59504f43,0x16161061,index,fnv(page)),
                     'copy result')
                # BAR0 exposes only odd grant pages directly. Index 0 is an
                # even page: rely on the card's post-copy FNV and the whole
                # operation-7 digest, not an aliased PCI aperture read.
                if index==1:
                    need(snap(ptr+PAGE)==page,'odd owned target readback')
                ownercheck(owned)
                write(0xc000e000,0x860,before[0x860:0x870])
                write(0xc000e000,0x820,before[0x820:0x830])
                write(stage,0,stage_before)
                need(snap(stage)==stage_before,'stage restore')
                translate(original);release('copy','copy')
                insmod(a.copy_module)
            control=struct.pack('<4I',0x48534148,0x16161071,2,digest)
            write(0xc000e000,0x870,control)
            write(0xc000e000,0x830,b'\xa5'*16)
            translate(original);command('digest',run)
            dp=snap(0xc000e000)
            (run/'digest-page.bin').write_bytes(dp)
            need(struct.unpack_from('<4I',dp,0x830)==
                 (0x48534148,0x16161071,2,digest),'whole card digest')
            write(0xc000e000,0x870,before[0x870:0x880])
            write(0xc000e000,0x830,before[0x830:0x840])
            translate(original);release('digest','digest')
            insmod(a.digest_module)
            manifest=struct.pack('<8I',0x314d4152,NONCE,ptr,0x80000,
                                 2,0,digest,0)
            side=struct.pack('<4I',0x3145534c,NONCE,1,0)+b'\xa5'*16
            write(0xc000e000,0xa00,manifest)
            write(0xc000e000,0xa20,b'\xa5'*28)
            write(0xc000e000,0xa40,side)
            write(0xc000e000,0xa60,b'\xa5'*16)
            translate(original)
            need(status('ram-admit').get('started')=='0','admit already started')
            (DEBUG/'accele-ram-admit/start').write_text('probe\n')
            began=time.monotonic()
            ready=False
            while time.monotonic()-began<2:
                cur=snap(0xc000e000)
                if struct.unpack_from('<I',cur,0xa50)[0]==0x59444152:
                    ready=True;break
                if status('ram-admit').get('done')=='1':break
                time.sleep(.002)
            (run/'ready-page.bin').write_bytes(cur)
            (run/'ready-status.txt').write_text(
                (DEBUG/'accele-ram-admit/status').read_text())
            need(ready and status('ram-admit').get('done')=='0',
                 'READY missing or callback ended early; retain grant')
            stale_pending=None
            if mode=='stop':
                write(0xc000e000,0xa4c,struct.pack('<I',0xdeadbeef))
                time.sleep(.005)
                stale_pending=status('ram-admit').get('done')=='0'
                (run/'stale-page.bin').write_bytes(snap(0xc000e000))
                need(stale_pending,'stale STOP ended callback')
                write(0xc000e000,0xa4c,struct.pack('<I',0x504f5453))
            translate(original)
            done('ram-admit',run,0,5)
            elapsed=time.monotonic()-began
            page=snap(0xc000e000)
            (run/'page-after.bin').write_bytes(page)
            stack_after=snap(ptr+PAGE)
            (run/'stack-after.bin').write_bytes(stack_after)
            (run/'owner-after.bin').write_bytes(ownercheck(owned))
            need(page[:0xa00]==reserved[:0x820]+before[0x820:0x830]+reserved[0x830:0xa00]
                 and page[0xa70:]==before[0xa70:],
                 'loader page changed outside manifest/report/sideband')
            report=struct.unpack_from('<7I',page,0xa20)
            flag=0x504f5453 if mode=='stop' else 0x454d4954
            need(report==(0x314e5552,NONCE,0x31454e4f,ptr,2,digest,flag),
                 'admission report')
            words=struct.unpack_from('<8I',page,0xa40)
            if mode=='stop':
                need(words==(0x3145534c,NONCE,1,0x504f5453,
                      0x59444152,0x214b4341,NONCE,1),'STOP ACK')
            else:
                need(words==(0x3145534c,NONCE,1,0,0x454d4954)+
                     (0xa5a5a5a5,)*3,'finite-poll exit')
            firmware_sp,worker_sp,exit_sp,restored_sp=struct.unpack_from('<4I',page,0xa60)
            need(firmware_sp==restored_sp and
                 ptr+PAGE<=worker_sp<ptr+2*PAGE and
                 ptr+PAGE<=exit_sp<ptr+2*PAGE and
                 stack_after!=payload[PAGE:] and
                 stack_after[:256]==b'\xa5'*256,
                 'owned stack or firmware context restoration')
            write(0xc000e000,0xa00,before[0xa00:0xa20])
            write(0xc000e000,0xa20,before[0xa20:0xa3c])
            write(0xc000e000,0xa40,before[0xa40:0xa60])
            write(0xc000e000,0xa60,before[0xa60:0xa70])
            need(snap(0xc000e000)==
                 reserved[:0x820]+before[0x820:0x830]+reserved[0x830:],
                 'loader page restore under grant')
            translate(original);release('ram-admit','admit')
            results.append(dict(mode=mode,elapsed_ms=round(elapsed*1000,3),
                stale_pending=stale_pending,firmware_sp=f'0x{firmware_sp:08x}',
                worker_sp=f'0x{worker_sp:08x}',
                exit_sp=f'0x{exit_sp:08x}',
                restored_sp=f'0x{restored_sp:08x}',
                stack_changed_bytes=sum(x!=y for x,y in zip(stack_after,payload[PAGE:]))))
            if number==0:insmod(a.admit_module)
        write(0xc000e000,0x820,b'\xa5'*16)
        translate(original);command('release',a.out)
        endpage=snap(0xc000e000)
        (a.out/'page-after-release.bin').write_bytes(endpage)
        need(struct.unpack_from('<4I',endpage,0x820)==
             (0x45455246,0x16161051,ptr,0x80000),'release report')
        after=ownercheck(owner)
        (a.out/'owner-after.bin').write_bytes(after)
        write(0xc000e000,0x820,before[0x820:0x830])
        restored=snap(0xc000e000)
        (a.out/'page-restored.bin').write_bytes(restored)
        need(restored==before and snap(stage)==stage_before,
             'final loader/stage restore')
        translate(original);release('release','release')
        # Copy/digest are rearmed but never started after final call.
        subprocess.run(['rmmod','copy_command'],check=True)
        subprocess.run(['rmmod','digest_command'],check=True)
        save(a.out/'result.json',dict(boot_id=boot,runs=results,
             firmware_sha256=FIRMWARE,image_sha256=IMAGE,
             full_audits=True,owner_restored=True,page_restored=True,
             stage_restored=True,card_after=select(BDF,'accele160'),
             old_after=select(OLD,'dac960pg')))
        print(json.dumps(results,indent=2))
    finally:
        translate(original);bar.close();res.close();cfg.close()

if __name__=='__main__':main()

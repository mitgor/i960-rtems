#!/usr/bin/env python3
"""Replay AcceleRAID owned-stack/STOP captures and exact full flash audit."""
import hashlib,json,struct,sys
from pathlib import Path
from run_lease import FIRMWARE,HANDLER,IMAGE,PROBE,MODULES,NONCE,PAGE,fnv

def need(ok,why):
    if not ok:raise ValueError(why)
def sha(data):return hashlib.sha256(data).hexdigest()
def fields(path):return dict(x.split('=',1) for x in path.read_text().split())
def status(path,code=0):
    s=fields(path)
    need(s.get('done')=='1' and s.get('status')==str(code) and
         s.get('residual')=='0','command completion')
    return s
def read(path,boot=None):
    req=json.loads((path/'request.json').read_text())
    result=json.loads((path/'result.json').read_text())
    state=fields(path/'status.txt')
    data=(path/'data.bin').read_bytes()
    need(req['selector']==9 and req['length']==len(data)==1048576 and
         (boot is None or req['boot_id']==boot) and
         sha(data)==result['sha256']==FIRMWARE and
         all(state.get(k)=='0' for k in ('status','residual','guard_changes')) and
         result['card_after']['driver']=='myrsread' and
         result['old_after']['driver'] is None,'full flash read')
    return req['boot_id']
def owners(before,after):
    need(len(before)==len(after)==PAGE and
         before[0x2a0:0xaa0]==after[0x2a0:0xaa0],
         '512 count/owner records')
def check_run(page,before,reserved,ptr,digest,mode):
    need(len(page)==PAGE and page[:0xa00]==
         reserved[:0x820]+before[0x820:0x830]+reserved[0x830:0xa00] and
         page[0xa70:]==before[0xa70:],'loader-page bounds')
    need(struct.unpack_from('<8I',page,0xa00)==
         (0x314d4152,NONCE,ptr,0x80000,2,0,digest,0),
         'manifest')
    flag=0x504f5453 if mode=='stop' else 0x454d4954
    need(struct.unpack_from('<7I',page,0xa20)==
         (0x314e5552,NONCE,0x31454e4f,ptr,2,digest,flag),
         'admission report')
    words=struct.unpack_from('<8I',page,0xa40)
    expected=((0x3145534c,NONCE,1,0x504f5453,0x59444152,
               0x214b4341,NONCE,1) if mode=='stop' else
              (0x3145534c,NONCE,1,0,0x454d4954)+
              (0xa5a5a5a5,)*3)
    need(words==expected,'STOP/timeout control record')
    fw,worker,exit_sp,restored=struct.unpack_from('<4I',page,0xa60)
    need(fw==restored and ptr+PAGE<=worker<ptr+2*PAGE and
         ptr+PAGE<=exit_sp<ptr+2*PAGE,'owned stack/firmware SP')
    return fw,worker,exit_sp,restored

def verify(root,acceptance):
    source=Path(__file__).resolve().parent
    image=(source/'image.bin').read_bytes()
    probe=(source/'probe.bin').read_bytes()
    handler=(source.parent/'ram_admit/handler.bin').read_bytes()
    firmware=(source.parent/'ram_admit/candidate.bin').read_bytes()
    need(sha(image)==IMAGE and sha(probe)==PROBE and
         sha(handler)==HANDLER and sha(firmware)==FIRMWARE and
         len(image)==2*PAGE and image[:len(probe)]==probe and
         image[PAGE:]==b'\xa5'*PAGE,'source/image identities')
    live=root/'accept-1'
    pre=json.loads((live/'preflight.json').read_text())
    result=json.loads((live/'result.json').read_text())
    need(pre['boot_id']==result['boot_id'] and
         pre['firmware_sha256']==result['firmware_sha256']==FIRMWARE and
         pre['image_sha256']==result['image_sha256']==IMAGE and
         pre['modules']==MODULES and result['full_audits'] and
         result['owner_restored'] and result['page_restored'] and
         result['stage_restored'],'preflight/result')
    read(root/'postcall-flash',pre['boot_id'])
    previous=acceptance/'ram-admit'
    read(previous/'postcall-flash',pre['boot_id'])
    read(previous/'postcompat-flash',pre['boot_id'])
    before=(live/'page-before.bin').read_bytes()
    tail=handler[0xf000-0xe1d8:]
    need(before==tail+b'\xff'*(PAGE-len(tail)),'retained code tail')
    reserved=(live/'page-reserved.bin').read_bytes()
    owner=(live/'owner-before.bin').read_bytes()
    owned=(live/'owner-reserved.bin').read_bytes()
    ptr=struct.unpack_from('<I',reserved,0x828)[0]
    need(ptr==0xc0710000 and struct.unpack_from('<4I',reserved,0x840)==
         (0x56525352,ptr,0x80000,0x96016004),'grant record')
    status(live/'reserve-status.txt')
    first=(ptr-0xc0000000)//0x8000
    for i in range(256):
        bc,bo=(struct.unpack_from('<I',owner,0x2a0+i*4)[0],
               struct.unpack_from('<I',owner,0x6a0+i*4)[0])
        rc,ro=(struct.unpack_from('<I',owned,0x2a0+i*4)[0],
               struct.unpack_from('<I',owned,0x6a0+i*4)[0])
        need((rc,ro)==((16,0x96016004) if first<=i<first+16 else (bc,bo)),
             'grant owner table')
        if first<=i<first+16:need((bc,bo)==(0,0),'grant overlap')
    digest=fnv(image)
    need(digest==0x4462f72b,'whole-image FNV')
    modes=[]
    for number,mode in enumerate(('timeout','stop')):
        run=live/mode
        for index in (0,1):
            page=image[index*PAGE:(index+1)*PAGE]
            need((run/f'stage-{index}.bin').read_bytes()==page,
                 'stage readback')
            status(run/'copy-status.txt')
            cp=(run/f'copy-{index}-page.bin').read_bytes()
            need(struct.unpack_from('<4I',cp,0x820)==
                 (0x59504f43,0x16161061,index,fnv(page)),
                 'copy report')
        status(run/'digest-status.txt')
        dp=(run/'digest-page.bin').read_bytes()
        need(struct.unpack_from('<4I',dp,0x830)==
             (0x48534148,0x16161071,2,digest),'card whole-image digest')
        ready=(run/'ready-page.bin').read_bytes()
        need(struct.unpack_from('<I',ready,0xa50)[0]==0x59444152 and
             fields(run/'ready-status.txt').get('done')=='0',
             'independent READY')
        if mode=='stop':
            stale=(run/'stale-page.bin').read_bytes()
            need(struct.unpack_from('<I',stale,0xa4c)[0]==0xdeadbeef and
                 struct.unpack_from('<I',stale,0xa54)[0]==0xa5a5a5a5,
                 'stale STOP not pending')
        status(run/'ram-admit-status.txt')
        page=(run/'page-after.bin').read_bytes()
        fw,worker,exit_sp,restored=check_run(page,before,reserved,ptr,digest,mode)
        owners(owned,(run/'owner-after.bin').read_bytes())
        stack=(run/'stack-after.bin').read_bytes()
        changed=sum(a!=b for a,b in zip(stack,image[PAGE:]))
        need(len(stack)==PAGE and stack[:256]==b'\xa5'*256 and changed>0 and
             changed==result['runs'][number]['stack_changed_bytes'] and
             result['runs'][number]['mode']==mode and
             result['runs'][number]['firmware_sp']==f'0x{fw:08x}' and
             result['runs'][number]['worker_sp']==f'0x{worker:08x}' and
             result['runs'][number]['exit_sp']==f'0x{exit_sp:08x}' and
             result['runs'][number]['restored_sp']==f'0x{restored:08x}',
             'owned stack capture/result')
        modes.append(dict(mode=mode,elapsed_ms=result['runs'][number]['elapsed_ms'],
                          stack_changed_bytes=changed))
    need(result['runs'][1]['stale_pending'] is True,'stale token')
    status(live/'release-status.txt')
    page=(live/'page-after-release.bin').read_bytes()
    need(struct.unpack_from('<4I',page,0x820)==
         (0x45455246,0x16161051,ptr,0x80000),'grant release report')
    owners(owner,(live/'owner-after.bin').read_bytes())
    need((live/'page-restored.bin').read_bytes()==before and
         result['card_after']['driver']=='myrsread' and
         result['old_after']['driver'] is None,'final restoration')
    recovered=json.loads((root/'accept-0/recovery-result.json').read_text())
    need(all(recovered.values()),'first preflight recovery')
    return dict(firmware_sha256=FIRMWARE,postcall_full_read=True,
                owner_records=512,modes=modes,first_preflight_recovered=True)

if __name__=='__main__':
    print(json.dumps(verify(Path(sys.argv[1]),Path(sys.argv[2])),indent=2))

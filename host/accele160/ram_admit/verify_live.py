#!/usr/bin/env python3
"""Replay complete flash receipts, two RAM calls and page/owner captures."""
import hashlib, json, struct, sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from run_admit import IMAGE_SHA, HANDLER_SHA, PROBE_SHA, NONCE, fnv

OLD_SHA='93faf91f553822665cd4125d90b1066370c4bca0da76af8336daf98bc2dae094'
MODULE_SHA='528767e0f94c5ce36d156a71b73ea8bfd9ae5e99013211b89e46a44096acabe5'

def sha(data): return hashlib.sha256(data).hexdigest()
def need(test,why):
    if not test: raise ValueError(why)
def fields(path): return dict(p.split('=',1) for p in path.read_text().split())
def status(path,code=0):
    s=fields(path)
    need(s.get('done')=='1' and s.get('status')==str(code) and
         s.get('residual')=='0','command status')
    return s
def read(path, expected, boot=None):
    req=json.loads((path/'request.json').read_text())
    result=json.loads((path/'result.json').read_text())
    state=fields(path/'status.txt')
    data=(path/'data.bin').read_bytes()
    need(req['selector']==9 and req['length']==len(data)==1048576 and
         (boot is None or req['boot_id']==boot) and
         sha(data)==result['sha256']==expected and
         all(state.get(k)=='0' for k in ('status','residual','guard_changes')) and
         result['card_after']['driver']=='myrsread' and
         result['old_after']['driver'] is None,'full flash readback')
    return req['boot_id']
def owner_records(before,after):
    need(len(before)==len(after)==4096 and
         before[0x2a0:0xaa0]==after[0x2a0:0xaa0],
         '512 allocator count/owner records')
def check_accepted(page, before, reserved, ptr, nonce, digest, value):
    need(len(page)==len(before)==len(reserved)==4096,'page length')
    want=bytearray(reserved)
    want[0x820:0x830]=before[0x820:0x830]
    want[0xa00:0xa20]=struct.pack('<8I',0x314d4152,nonce,ptr,0x80000,
                                  1,0,digest,0)
    want[0xa20:0xa3c]=page[0xa20:0xa3c]
    need(page==want,'accepted loader page bounds')
    report=struct.unpack_from('<7I',page,0xa20)
    need(report==(0x314e5552,nonce,0x31454e4f,ptr,1,digest,value),
         'accepted report')
    return report
def check_rejected(page,before,reserved,nonce,ptr,digest,kind):
    want=bytearray(reserved)
    want[0x820:0x830]=before[0x820:0x830]
    manifest=[0x314d4152,nonce,ptr,0x80000,1,0,digest,0]
    if kind=='bad-hash':manifest[6]^=1
    elif kind=='bad-entry':manifest[5]=4096
    elif kind=='bad-nonce':manifest[1]^=1
    else: raise ValueError(kind)
    want[0xa00:0xa20]=struct.pack('<8I',*manifest)
    want[0xa20:0xa3c]=b'\xa5'*28
    need(page==want,f'{kind} changed loader page')

def verify(root):
    source=Path(__file__).resolve().parent
    live=root/'ram-admit'
    image=(source/'candidate.bin').read_bytes()
    handler=(source/'handler.bin').read_bytes()
    need(sha(image)==IMAGE_SHA and sha(handler)==HANDLER_SHA and
         sha((root/'admit_command.ko').read_bytes())==MODULE_SHA,
         'candidate/handler/companion identity')
    oldboot=read(live/'preflash-0',OLD_SHA)
    read(live/'preflash-1',OLD_SHA,oldboot)
    read(live/'staged-readback',IMAGE_SHA,oldboot)
    stage_req=json.loads((live/'stage/request.json').read_text())
    stage_result=json.loads((live/'stage/result.json').read_text())
    stage_status=fields(live/'stage/status.txt')
    need(stage_req['boot_id']==oldboot and
         stage_req['image_sha256']==IMAGE_SHA and
         stage_result['stage_completed'] and
         stage_result['flash_command_issued'] is False and
         all(stage_status.get(k)=='0' for k in ('status','residual','guard_changes')),
         'stage receipt')
    flash_pre=json.loads((live/'flash/preflight.json').read_text())
    flash_result=json.loads((live/'flash/result.json').read_text())
    flash_status=fields(live/'flash/status.txt')
    need(flash_pre['boot_id']==oldboot and flash_pre['image_sha256']==IMAGE_SHA and
         flash_result['command_completed'] and
         flash_status['done']=='1' and flash_status['status']=='0' and
         flash_status['residual']=='0','flash receipt')
    boot=read(live/'persistent-0',IMAGE_SHA)
    need(boot!=oldboot,'postflash boot did not change')
    read(live/'persistent-1',IMAGE_SHA,boot)
    read(live/'postcall-flash',IMAGE_SHA,boot)
    read(live/'postcompat-flash',IMAGE_SHA,boot)
    run=live/'run'
    pre=json.loads((run/'preflight.json').read_text())
    result=json.loads((run/'result.json').read_text())
    need(pre['boot_id']==result['boot_id']==boot and
         pre['image_sha256']==IMAGE_SHA and
         pre['handler_sha256']==HANDLER_SHA and
         pre['modules']['admit']==MODULE_SHA and
         result['full_audits'] and result['page_restored'] and
         result['owners_restored'] and result['staging_restored'],
         'run receipt')
    before=(run/'page-before.bin').read_bytes()
    tail=handler[0xf000-0xe1d8:]
    need(before==tail+b'\xff'*(4096-len(tail)),
         'exact live handler code tail')
    owner=(run/'owner-before.bin').read_bytes()
    reserved=(run/'page-reserved.bin').read_bytes()
    owned=(run/'owner-reserved.bin').read_bytes()
    ptr=struct.unpack_from('<I',reserved,0x828)[0]
    need(ptr==result['grant']==0xc0710000 and
         struct.unpack_from('<4I',reserved,0x840)==
         (0x56525352,ptr,0x80000,0x96016004),
         'grant record')
    status(run/'reserve-status.txt')
    first=(ptr-0xc0000000)//0x8000
    for i in range(256):
        b=(struct.unpack_from('<I',owner,0x2a0+i*4)[0],
           struct.unpack_from('<I',owner,0x6a0+i*4)[0])
        r=(struct.unpack_from('<I',owned,0x2a0+i*4)[0],
           struct.unpack_from('<I',owned,0x6a0+i*4)[0])
        need(r==((16,0x96016004) if first<=i<first+16 else b),
             'allocated owner table')
        if first<=i<first+16: need(b==(0,0),'grant overlap')
    reports=[]
    for ordinal in (1,2):
        child=run/f'run-{ordinal}'
        probe=(source/f'probe{ordinal}.bin').read_bytes()
        need(sha(probe)==PROBE_SHA[ordinal-1],'probe identity')
        payload=probe.ljust(4096,b'\0')
        digest=fnv(payload)
        host=json.loads((child/'manifest-host.json').read_text())
        need(host['image_sha256']==sha(payload) and
             host['fnv']==f'0x{digest:08x}' and
             (child/'stage-readback.bin').read_bytes()==payload,
             'staged page identity')
        status(child/'copy-status.txt')
        status(child/'digest-status.txt')
        cp=(child/'copy-page.bin').read_bytes()
        need(struct.unpack_from('<4I',cp,0x820)==
             (0x59504f43,0x16161061,0,digest),'copy report')
        dp=(child/'digest-page.bin').read_bytes()
        need(struct.unpack_from('<4I',dp,0x830)==
             (0x48534148,0x16161071,1,digest),'card digest')
        for kind in ('bad-hash','bad-entry','bad-nonce'):
            negative=child/kind
            status(negative/'ram-admit-status.txt',2)
            check_rejected((negative/'page.bin').read_bytes(),before,reserved,
                           NONCE,ptr,digest,kind)
        status(child/'ram-admit-status.txt')
        owner_records(owned,(child/'owner-after.bin').read_bytes())
        report=check_accepted((child/'page-after.bin').read_bytes(),before,
                 reserved,ptr,NONCE,digest,0x16010000+ordinal)
        need(list(report)==result['runs'][ordinal-1]['report'] and
             result['runs'][ordinal-1]['probe_sha256']==PROBE_SHA[ordinal-1],
             'run result/report mismatch')
        reports.append(report)
    status(run/'release-status.txt')
    released=(run/'page-after-release.bin').read_bytes()
    need(struct.unpack_from('<4I',released,0x820)==
         (0x45455246,0x16161051,ptr,0x80000),'release record')
    owner_records(owner,(run/'owner-after.bin').read_bytes())
    need(result['card_after']['driver']=='myrsread' and
         result['old_after']['driver'] is None,'card ownership')
    stop=live/'stop-compat'
    stop_result=json.loads((stop/'result.json').read_text())
    stop_before=(stop/'page-before.bin').read_bytes()
    stop_owner=(stop/'owner-before.bin').read_bytes()
    need(stop_before==before and stop_result['page_restored'] and
         stop_result['owner_records_unchanged'] and len(stop_result['runs'])==2,
         'STOP compatibility preflight')
    for ordinal,kind in enumerate(('stop','deadline')):
        status(stop/f'run-{ordinal}-status.txt',0 if kind=='stop' else 2)
        page=(stop/f'run-{ordinal}-page.bin').read_bytes()
        need(page[:0x960]==before[:0x960] and
             page[0x980:]==before[0x980:],'STOP page bounds')
        owner_records(stop_owner,(stop/f'run-{ordinal}-owner.bin').read_bytes())
        words=struct.unpack_from('<8I',page,0x960)
        want=((0x31504f54,0x161610b1,1,0x504f5453,0x59444152,
               0x214b4341,0x161610b1,1) if kind=='stop' else
              (0x31504f54,0x161610b1,1,0,0x454d4954,0xa5a5a5a5,
               0xa5a5a5a5,0xa5a5a5a5))
        need(words==want,'STOP compatibility result')
    need(stop_result['runs'][0]['stale_pending'] is True,
         'stale STOP token ended callback')
    rtems=live/'rtems-compat'
    rtems_result=json.loads((rtems/'result.json').read_text())
    need((rtems/'page-before.bin').read_bytes()==before and
         (rtems/'page-restored.bin').read_bytes()==before and
         (rtems/'staging-before.bin').read_bytes()==
         (rtems/'staging-restored.bin').read_bytes() and
         rtems_result['rtems_executed'] and rtems_result['pages']==15 and
         rtems_result['whole_digest']=='0x648486da',
         'fixed RTEMS compatibility receipts')
    owner_records((rtems/'table-before.bin').read_bytes(),
                  (rtems/'table-after.bin').read_bytes())
    for name,code in (('reserve',0),('digest',0),('rtems',0),('release',0),
                      ('bad-hash',2),('bad-count',2)):
        status(rtems/f'{name}-status.txt',code)
    rtems_page=(rtems/'rtems-page.bin').read_bytes()
    need(struct.unpack_from('<8I',rtems_page,0x800)==
         (0x4d455452,0x16161091,0x46600006,1,5,11,0xc071e270,0x1600a001),
         'fixed RTEMS result')
    need(struct.unpack_from('<4I',rtems_page,0x830)==
         (0x214d4552,0x16161091,0xc0710000,0x648486da),
         'fixed RTEMS firmware report')
    return dict(candidate_sha256=IMAGE_SHA,postboot_full_reads=2,
                postcall_full_reads=2,ram_images=2,negative_cases=6,
                stop_compat_calls=2,fixed_rtems_calls=1,
                owner_records=512,reports=[list(x) for x in reports])

if __name__=='__main__':
    print(json.dumps(verify(Path(sys.argv[1])),indent=2))

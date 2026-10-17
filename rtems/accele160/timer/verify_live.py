#!/usr/bin/env python3
"""Offline replay of the AcceleRAID timer-1/vector-18 hardware gate."""
import hashlib,json,struct,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'host/accele160/inventory_gate'))
import run_inventory as inventory
sys.path.insert(0,str(ROOT/'host/accele160/vector_gate'))
import run_vector as vector
FIRMWARE='1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
IMAGE='09064cdb91661727a6c10ab93a5f149998fb9d9ca6b4e95e071f905be1cc8038'
NONCE=0x161610d1
PTR=0xc0710000
PAGE=4096
def need(ok,label):
    if not ok:raise ValueError(label)
def read(path):return path.read_bytes()
def sha(data):return hashlib.sha256(data).hexdigest()
def words(data,off,n):return struct.unpack_from('<'+str(n)+'I',data,off)
def fields(path):return dict(x.split('=',1) for x in path.read_text().split())
def fnv(data):
    h=0x811c9dc5
    for b in data:h=((h^b)*0x01000193)&0xffffffff
    return h
def audit(path,boot,card,old):
    req=json.loads((path/'request.json').read_text())
    result=json.loads((path/'result.json').read_text())
    state=fields(path/'status.txt')
    data=read(path/'data.bin')
    need(req['boot_id']==boot and req['selector']==9 and
         req['length']==len(data)==1048576 and
         sha(data)==result['sha256']==FIRMWARE and
         result['card_after']==card and result['old_after']==old and
         all(state.get(k)=='0' for k in ('status','residual','guard_changes')),
         f'full flash audit {path}')

def verify(root):
    root=Path(root)
    image=read(Path(__file__).resolve().parent/'image.bin')
    need(len(image)==3*PAGE and sha(image)==IMAGE and
         image[PAGE:]==b'\xa5'*(2*PAGE) and
         fnv(image)==0x917f3e48,'timer image identity')
    probe=root/'timer-preflight-0'
    first=json.loads((probe/'preflight.json').read_text())
    boot,card,old=first['boot_id'],first['card'],first['old']
    need(card['bdf']=='0000:37:09.1' and card['driver']=='myrsread' and
         old['bdf']=='0000:37:04.1' and old['driver'] is None and
         first['firmware_sha256']==FIRMWARE and
         first['inventory_module_sha256']==inventory.MODULE_SHA and
         first['vector_module_sha256']==vector.MODULE_SHA,
         'initial identity/owner')
    for p in (root/'before-full',
              probe/'postcall-flash',
              root/'timer-postflight-0/postcall-flash',
              root/'timer-postflight-1/postcall-flash'):
        audit(p,boot,card,old)
    observations=[]
    for name in ('timer-preflight-0','timer-postflight-0','timer-postflight-1'):
        p=root/name
        pre=json.loads((p/'preflight.json').read_text())
        result=json.loads((p/'result.json').read_text())
        before=read(p/'page-before.bin')
        owner=read(p/'owner-before.bin')
        need(pre['boot_id']==boot and pre['card']==card and pre['old']==old and
             result['boot_id']==boot and result['card_after']==card and
             result['old_after']==old and result['page_restored'] and
             result['owner_restored'],'observation identity')
        reports={}
        for label,mod in (('inventory',inventory),('vector',vector)):
            state=fields(p/(label+'-status.txt'))
            need(state.get('done')=='1' and state.get('status')=='0' and
                 state.get('residual')=='0','observation status')
            page=read(p/(label+'-page.bin'))
            need(page[:mod.FIRST]==before[:mod.FIRST] and
                 page[mod.LAST:]==before[mod.LAST:] and
                 read(p/(label+'-owner.bin'))[0x2a0:0xaa0]==
                 owner[0x2a0:0xaa0], 'observation page/owner bounds')
            reports[label]=mod.decode(page)
        need(reports==result['observations'],'decoded observation')
        observations.append((before,owner[0x2a0:0xaa0],reports))
    baseline=observations[0][2]
    for before,owner,reports in observations[1:]:
        need(before==observations[0][0] and owner==observations[0][1],
             'between-call page/owner restoration')
        a=baseline['inventory']['registers']
        b=reports['inventory']['registers']
        need(all(a[k]==v for k,v in b.items() if k!='0xff000304') and
             baseline['vector']==reports['vector'],
             'timer/vector state changed across active calls')
    need(baseline['inventory']['registers']['0x0000003c']=='0xe0000ff0' and
         baseline['inventory']['registers']['0xff008520']=='0x00004444' and
         baseline['inventory']['registers']['0xff008524']=='0x00006754' and
         baseline['vector']['cached_vector18']=='0xaaaaaaaa' and
         baseline['vector']['mode']=='0x00000000',
         'initial timer/vector guard')
    results=[]
    for name in ('timer-active-0','timer-active-1'):
        p=root/name
        pre=json.loads((p/'preflight.json').read_text())
        result=json.loads((p/'result.json').read_text())
        before=read(p/'page-before.bin')
        reserved=read(p/'page-reserved.bin')
        owner=read(p/'owner-before.bin')
        owned=read(p/'owner-reserved.bin')
        need(pre['boot_id']==boot and pre['image_sha256']==IMAGE and
             pre['firmware_sha256']==FIRMWARE and
             pre['fnv']=='0x917f3e48' and
             result['boot_id']==boot and result['image_sha256']==IMAGE and
             result['firmware_sha256']==FIRMWARE and
             result['card_after']==card and result['old_after']==old and
             all(result[k] for k in
                 ('full_audits','owner_restored','page_restored','stage_restored')),
             'active identity/cleanup')
        need(before==observations[0][0] and
             owner[0x2a0:0xaa0]==observations[0][1] and
             read(p/'page-restored.bin')==before and
             read(p/'owner-after.bin')[0x2a0:0xaa0]==owner[0x2a0:0xaa0] and
             words(reserved,0x820,4)==(0x4f4c4c41,0x16161041,PTR,0x80000),
             'active loader/owner restoration')
        first_block=(PTR-0xc0000000)//0x8000
        for i in range(256):
            rc,ro=words(owned,0x2a0+4*i,1)[0],words(owned,0x6a0+4*i,1)[0]
            bc,bo=words(owner,0x2a0+4*i,1)[0],words(owner,0x6a0+4*i,1)[0]
            need((rc,ro)==((16,0x96016004) if
                 first_block<=i<first_block+16 else (bc,bo)),
                 f'active owner {i}')
        for index,mode in enumerate(('ticks','stop')):
            run=p/mode
            entry=result['runs'][index]
            need(entry['mode']==mode and entry['elapsed_ms']>0,'active result')
            receipts=json.loads((run/'copy-receipts.json').read_text())
            need(len(receipts)==3,'copy count')
            for i,r in enumerate(receipts):
                data=image[i*PAGE:(i+1)*PAGE]
                need(r==dict(index=i,sha256=sha(data),fnv=f'0x{fnv(data):08x}'),
                     f'copy {i}')
            for command in ('copy','digest','ram-admit'):
                state=fields(run/(command+'-status.txt'))
                need(state.get('done')=='1' and state.get('status')=='0' and
                     state.get('residual')=='0',command+' status')
            need(words(read(run/'digest-page.bin'),0x830,4)==
                 (0x48534148,0x16161071,3,0x917f3e48),'card digest')
            page=read(run/'page-after.bin')
            need(page[:0xa00]==reserved[:0x820]+before[0x820:0x830]+
                 reserved[0x830:0xa00] and page[0xa80:]==before[0xa80:],
                 'active loader bounds')
            flag=0x504f5453 if mode=='stop' else 0x4b434954
            epoch=1 if mode=='stop' else 2
            need(words(page,0xa00,8)==
                 (0x314d4152,NONCE,PTR,0x80000,3,0,0x917f3e48,0) and
                 words(page,0xa20,7)==
                 (0x314e5552,NONCE,0x31454e4f,PTR,3,0x917f3e48,flag),
                 'active manifest/report')
            side=words(page,0xa40,8)
            if mode=='stop':
                need(entry['stale_pending'] is True and
                     words(read(run/'stale-page.bin'),0xa4c,1)==(0xdeadbeef,) and
                     side==(0x3145534c,NONCE,1,0x504f5453,0x59444152,
                            0x214b4341,NONCE,1),'STOP/ACK')
            else:
                need(side==(0x3145534c,NONCE,2,0,0x4b434954)+
                     (0xa5a5a5a5,)*3,'fixed tick result')
            fw,guard,entry_sp,restored,irq_ticks,irq_sp,restore_ok,reason=words(
                page,0xa60,8)
            stack=read(run/'irq-stack-after.bin')
            need(fw==restored==0xc0002100 and guard==0 and
                 PTR+2*PAGE<=entry_sp<PTR+3*PAGE and
                 PTR+PAGE+192<=irq_sp<PTR+2*PAGE and
                 irq_ticks==entry['ticks'] and
                 (irq_ticks>=8 if mode=='ticks' else 2<=irq_ticks<1000) and
                 restore_ok==1 and reason==0 and stack[:64]==b'\xa5'*64 and
                 stack[-64:]==b'\xa5'*64 and
                 sum(x!=y for x,y in zip(stack,image[PAGE:2*PAGE]))==
                 entry['stack_changed_bytes'] and
                 read(run/'owner-after.bin')[0x2a0:0xaa0]==owned[0x2a0:0xaa0],
                 'interrupt stack/context/restoration')
            if entry.get('sampled_hz') is not None:
                t0,t1=entry['sample_first'],entry['sample_last']
                need(t1[0]>t0[0] and
                     round((t1[0]-t0[0])/(t1[1]-t0[1]),2)==
                     entry['sampled_hz'],'rate sample')
        results.append(result)
    return dict(boot_id=boot,full_flash_reads=4,active_runs=2,
                fixed_ticks=[r['runs'][0]['ticks'] for r in results],
                stop_ticks=[r['runs'][1]['ticks'] for r in results],
                sampled_hz=results[1]['runs'][1]['sampled_hz'],
                firmware_sha256=FIRMWARE,image_sha256=IMAGE)

if __name__=='__main__':print(json.dumps(verify(sys.argv[1]),indent=2))

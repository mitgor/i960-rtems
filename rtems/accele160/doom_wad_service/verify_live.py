#!/usr/bin/env python3
"""Offline replay of the bounded AcceleRAID WAD-service capture."""
import hashlib,json,struct,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
DEFAULT=ROOT/'artifacts/current/accele160-doom-wad-service-20261017'
PRIOR=ROOT/'artifacts/current/accele160-doom-bridge-20261017/inputs'
FW='1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
IMAGE='2748538e4140de26b560a2d2aa2ecaeee4f2b34d90eb744e10f86d266a5f9125'
KERNEL='96142197a385e6b5f3a035050bface009c32a99bc8c164496f3726f4bd6b9aea'

def need(ok,msg):
    if not ok:raise RuntimeError(msg)
def sha(data):return hashlib.sha256(data).hexdigest()
def fnv(data):
    h=0x811c9dc5
    for b in data:h=((h^b)*0x01000193)&0xffffffff
    return h
def words(data,offset,n):return struct.unpack_from('<%dI'%n,data,offset)
def load(path):return json.loads(path.read_text())

def verify(root=DEFAULT):
    live=root/'evidence';run=live/'persist';build=root/'build'
    result=load(live/'result.json');pre=load(live/'bank-preflight.json')
    image=(build/'image.bin').read_bytes();kernel=(build/'kernel.bin').read_bytes()
    need(len(image)==27*4096 and sha(image)==IMAGE==result['image_sha256'] and
         sha(kernel)==KERNEL==result['kernel_sha256'] and fnv(image)==0x835ea07d and
         image[:20*4096]==kernel[:20*4096] and
         image[20*4096:]==b'\xa5'*(7*4096),'exact RTEMS image')
    need(result['firmware_sha256']==FW and result['full_audits_before'] and
         pre['odd_pages']==1024 and pre['bytes']==4194304 and
         pre['first_sha256']==pre['second_sha256'] and
         pre['upper_sample_sha256']==sha((live/'upper-before.bin').read_bytes()),
         'preflight identity and stable read-only survey')
    ready=(run/'ready-page.bin').read_bytes()
    stop=(run/'quiescent-page.bin').read_bytes()
    bank=words(ready,0xb00,16);claim=words(ready,0xb40,16)
    need(bank[:4]==(0x314b4e42,0,2048,0x800000) and
         bank[4]==bank[5]==bank[6] and bank[7:11]==(2048,0,2048,0) and
         bank[11]!=0 and bank[12:14]==(0,0) and bank[14]==bank[15] and
         words(stop,0xb00,16)==bank,'full reversible bank audit')
    need(claim[:4]==(0x314d5241,2048,0x833aedc5,0) and
         claim[7:16]==(0xc0810010,0xc08ebbd0,0xc0eebbf0,
                       900000,6291456,65536,0x101,0x102,0x103),
         'guarded arena allocations')
    bridge=words(stop,0xb80,20);stopped=words(stop,0xb40,16)
    need(bridge[6:10]==(0x31475242,0x161610e1,316,15) and
         bridge[11:16]==(867792,1,1,claim[7]+355776,867792) and
         bridge[17:20]==(1,38,4),'bridge admission and WAD counters')
    need(stopped[4]>claim[4] and stopped[5:7]==(0x45495551,0) and
         words(stop,0xa54,1)==(0x214b4341,) and
         'started=1' in (run/'admit-pending-status.txt').read_text() and
         'done=0' in (run/'admit-pending-status.txt').read_text(),
         'retained STOP')
    template=(PRIOR/'template.bin').read_bytes()
    relocs=(PRIOR/'relocations.bin').read_bytes()
    wadhead=(PRIOR/'wad-header.bin').read_bytes()
    need(len(template)==431864 and
         sha(template)=='9f2472c900bb724e7a69b2490e083c4c633520e1d525623398db2e36f2c1e173' and
         len(relocs)==53472 and
         sha(relocs)=='4a0408886fe0a840b866219b62c0c1d19c7b6b6dcbc61574155fe88f49ba1a94' and
         sha(wadhead)=='93bd1ddcfc43fbf233207876f5cfcbaef4cf4e64a1093efa47be9517d93214bd',
         'pinned Doom and WAD inputs')
    receipts=load(run/'bridge-receipts.json')
    need(len(receipts)==316 and [r['seq'] for r in receipts]==list(range(1,317)),
         'ordered bridge receipts')
    need((receipts[0]['op'],receipts[0]['status'])==(4,1),
         'premature admission rejection')
    admission=template+bytes(814320-len(template))+relocs
    for i,off in enumerate(range(0,len(admission),4096),1):
        r=receipts[i];n=min(4096,len(admission)-off)
        need((r['op'],r['offset'],r['n'],r['status'],r['value'])==
             (1,off,n,0,off+n),f'upload receipt {i}')
    need((receipts[213]['op'],receipts[213]['status'])==(4,0) and
         (receipts[214]['op'],receipts[214]['status'])==(2,7) and
         (receipts[215]['op'],receipts[215]['status'])==(2,0),
         'image and WAD admission')
    frame=(run/'frame.bin').read_bytes()
    expected=bytes((((x>>3)^(y>>3)^wadhead[(x+y)&511])&255)
                   for y in range(200) for x in range(320))+bytes(1536)
    need(frame==expected and fnv(frame)==bridge[16] and
         sha(frame)==result['frame_sha256'] and
         (run/'frame.pgm').read_bytes()==b'P5\n320 200\n255\n'+frame[:64000],
         'independent diagnostic frame oracle')
    for i,r in enumerate(receipts[216:232]):
        need((r['op'],r['offset'],r['n'],r['status'],r['value'])==
             (3,i,4096,0,fnv(frame[i*4096:(i+1)*4096])),f'frame page {i}')
    need((receipts[232]['op'],receipts[232]['status'])==(5,10),
         'invalid EOF WAD request refused')
    wad=load(run/'wad-receipts.json')
    need(len(wad)==42 and [x['request_seq'] for x in wad]==list(range(1,43)),
         'ordered card-requested WAD reads')
    expected_modes=['good']*37+['bad-fnv','stale','timeout','good','stop']
    need([x['mode'] for x in wad]==expected_modes,'WAD refusal/recovery order')
    for i,x in enumerate(wad):
        n=x['n'];off=x['offset'];mode=x['mode']
        want={'good':0,'bad-fnv':12,'stale':11,'timeout':16,'stop':15}[mode]
        need(0<n<=4096 and off+n<=28795076 and x['status']==want and
             x['card_good']==sum(y['mode']=='good' for y in wad[:i+1]) and
             x['card_bad']==sum(y['mode']!='good' for y in wad[:i+1]) and
             receipts[x['seq']-1]['op']==5 and
             receipts[x['seq']-1]['status']==want and
             (x['card_value']==int(x['source_fnv'],16) if want==0 else
              x['card_value']==0),f'WAD request {i+1}')
        if i==0:need(x['source_sha256']==sha(wadhead),'WAD header source')
        if mode!='stop':
            cache=receipts[x['seq']]
            need(cache['op']==6 and cache['status']==0 and cache['n']==4096,
                 f'cache audit {i+1}')
    need(wad[-1]['seq']==316 and result['wad_requests']==42 and
         result['wad_good']==38 and result['wad_bad']==4 and
         result['release']=='reboot-only' and result['grant_retained'] and
         result['old']['driver'] is None,'final WAD ownership report')
    reset_boot=None
    for number in (0,1):
        folder=root/f'post-reset-{number}'
        req=load(folder/'request.json');post=load(folder/'result.json')
        status=dict(x.split('=',1) for x in
                    (folder/'status.txt').read_text().split())
        if reset_boot is None:reset_boot=req['boot_id']
        need(req['boot_id']==reset_boot!=result['boot_id'] and
             req['card']['bdf']=='0000:37:09.1' and
             req['card']['driver']=='myrsread' and req['selector']==9 and
             req['length']==post['bytes']==1048576 and
             post['sha256']==FW and post['card_after']==req['card'] and
             post['old_after']['driver'] is None and
             all(status[k]=='0' for k in ('status','residual','guard_changes')),
             f'post-reset full-flash audit {number}')
    return dict(wad_requests=42,good=38,rejected=4,frame_sha256=sha(frame),
                bank_pages=bank[7],boot_id=result['boot_id'],
                reset_boot_id=reset_boot)

if __name__=='__main__':
    print(json.dumps(verify(Path(sys.argv[1]) if len(sys.argv)>1 else DEFAULT),indent=2))

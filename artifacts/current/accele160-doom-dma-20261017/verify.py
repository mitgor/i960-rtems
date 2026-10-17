#!/usr/bin/env python3
"""Independent, hardware-free replay of bounded Doom ping-pong DMA evidence."""
import argparse,hashlib,json,statistics,struct,tarfile,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
STOCK='1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
def sha(b):return hashlib.sha256(b).hexdigest()
def fnv(b):
    h=2166136261
    for v in b:h=((h^v)*16777619)&0xffffffff
    return h
def load(p):return json.loads(p.read_text())
def check_capture(c,r):
    assert len(c)==77824
    assert c[:4096]==b'\xa5'*4096 and c[69664:]==b'\xa5'*8160
    gen=r['generation'];slot=r['slot']
    assert slot==((gen-1)&1)
    assert struct.unpack_from('<8I',c,69632)==(0x31505044,0x161610e1,gen,slot,65536,r['source'],r['card_tick'],(~gen)&0xffffffff)
    b=c[4096:69632]
    assert sha(b)==r['sha256'] and f'0x{fnv(b):08x}'==r['fnv']
    if r.get('card_fnv_mode','on')=='on':assert r.get('card_fnv',r['fnv'])==r['fnv']
    else:assert r['card_fnv_mode']=='off' and r['card_fnv']=='0x00000000'
    return b
def rejected(c,r):
    try:check_capture(c,r)
    except AssertionError:return True
    return False
def stats(v):
    s=sorted(v)
    return dict(count=len(v),mean=statistics.mean(v),min=s[0],p50=statistics.median(v),p95=s[int(.95*(len(s)-1))],max=s[-1])
def verify(case,post=True):
    run=case/'run';p=run/'persist';web=case/'http'
    result=load(run/'result.json');receipts=load(p/'live-frame-receipts.json')
    manifest=load(case/'source/live-32-manifest.json')
    assert result['firmware_sha256']==STOCK and result['old']['driver'] is None
    assert result['card']['bdf']=='0000:37:09.1' and result['release']=='reboot-only'
    assert result['grant_retained'] and result['full_audits_before']
    for name,key in [('kernel.bin','kernel_sha256'),('image.bin','image_sha256')]:
        assert sha((case/'build'/name).read_bytes())==manifest[key]==result[key]
    for name,key in [('app.c','source_sha256'),('frame_dma.h','dma_source_sha256'),('copy.h','copy_sha256'),('engine_identity.h','engine_identity_sha256'),('fnv_host.so','native_fnv_sha256')]:
        assert sha((case/'source'/name).read_bytes())==manifest[key]
    assert sha((case/'module/dma_frames.ko').read_bytes())==manifest['dma_module_sha256']==result['dma_module_sha256']
    engine=load(case/'engine/manifest.json')
    assert sha((case/'engine/manifest.json').read_bytes())==manifest['engine_manifest_sha256']
    for n,k in [('template.bin','template_sha256'),('relocations.bin','metadata_sha256')]:
        assert sha((case/'engine'/n).read_bytes())==engine[k]
    assert engine['double_buffer'] and engine['direct_frame'] and engine['no_fnv']
    assert [r['generation'] for r in receipts]==list(range(1,33))
    assert result['dma_frames']==32 and result['paired_frames'] in (4,32)
    references=load(case/'old-pixels.json')
    for r in receipts:
        gen=r['generation']
        assert r['source']==int(result['claim_report'][7],16)+engine['play_offset']+((gen-1)&1)*65536
        b=check_capture((p/f'dma-frame-{gen:04d}.bin').read_bytes(),r)
        assert b==(p/'live-frames'/f'frame-{gen:04d}.bin').read_bytes()
        assert sha(b[:64768])==references[str(gen)]
        assert r['paired_pio']==(gen<=result['paired_frames'])
        assert struct.unpack_from('<4I',b,64768)==(0x31524650,1,gen,2)
        assert struct.unpack_from('<4I',b,64832)==(0x31555043,1,1,10)
    # Independent negative tests reject payload, both guards, source, generation,
    # epoch, slot, marker size and inverted generation mutations.
    c=(p/'dma-frame-0001.bin').read_bytes();r=receipts[0]
    mutations=[0,4095,4096,69631,69664,77823]+list(range(69632,69664,4))
    for offset in mutations:
        changed=bytearray(c);changed[offset]^=1
        assert rejected(changed,r),f'tamper accepted at {offset}'
    for key in ('generation','slot','source','card_tick'):
        changed=dict(r);changed[key]^=1
        assert rejected(c,changed),f'tampered receipt accepted: {key}'
    http=load(web/'result.json');assert len(http['frames'])==32
    for x in http['frames']:
        gen=x['generation'];packet=(web/f'http-frame-{gen:04d}.bin').read_bytes()
        assert struct.unpack_from('<8I',packet)==(0x31424644,1,x['epoch'],gen,320,200,65536,0)
        assert len(packet)==65568 and sha(packet[32:])==x['sha256']==receipts[gen-1]['sha256']
    reads=load(p/'engine-reads.json');oracle=(case/'source/native-requests.bin').read_bytes()
    assert len(reads)==result['engine_wad_reads']==5045 and len(oracle)==5043*8
    assert sha(oracle)=='ce800a040facb00b2d4b0346b1babbc65a16cee0e7c2813f156e011d8efbf1b0'
    for row,pair in zip(reads,struct.iter_unpack('<II',oracle)):assert (row['offset'],row['n'])==pair
    page=(p/'quiescent-page.bin').read_bytes()
    assert [f'0x{x:08x}' for x in struct.unpack_from('<16I',page,0xb40)]==result['claim_report']
    assert struct.unpack_from('<II',page,0xb54)==(0x45495551,0)
    er=struct.unpack_from('<16I',page,0xc40);rr=struct.unpack_from('<12I',page,0xc80)
    assert er[:2]==(0x314d5246,2) and er[4:6]==(0x454e4702,32)
    assert er[9:11]==(0,1) and er[11]==er[12]
    assert rr[:3]==(0x454e4750,2,6291456) and rr[5]==32 and rr[9:12]==(2,1,210)
    final=(p/'game-frame.bin').read_bytes()
    assert final==(p/'live-frames/frame-0032.bin').read_bytes()
    assert sha(final)==result['game_frame_sha256'] and fnv(final)==er[6]
    live=struct.unpack_from('<16I',page,0xd00)
    assert live[:2]==(0x3145564c,0x161610e1)
    assert live[2]==live[5]==31 and live[6]==live[9]==32
    assert struct.unpack_from('<I',page,0xcf8)[0]==0
    d=struct.unpack_from('<32I',page,0xd80)
    assert d[:3]==(0x31464d44,0x161610e1,0) and d[11]==32 and d[14:16]==(0,0)
    assert d[13]==d[7]+32
    assert 'guard_changes=0 retained=1' in (p/'dma-pin-final.txt').read_text()
    assert (p/'dma-pin-release-denied.txt').stat().st_size
    stall=load(p/'dma-stall.json');assert stall['generation']==8 and stall['seconds']>=3 and stall['unchanged']
    bank=struct.unpack_from('<16I',page,0xb00)
    assert [f'0x{x:08x}' for x in bank]==result['bank_report']
    assert bank[:4]==(0x314b4e42,0,2048,0x800000)
    assert bank[4]==bank[5]==bank[6] and bank[7:11]==(2048,0,2048,0)
    assert bank[11] and bank[12:14]==(0,0) and bank[14]==bank[15]
    ticks=list(struct.unpack_from('<32I',page,0xe00))
    assert all(b>a for a,b in zip(ticks,ticks[1:]))
    assert result['frame_timing']['elapsed_ticks']==ticks[-1]-ticks[0]
    assert abs(result['frame_timing']['render_fps']-3100/(ticks[-1]-ticks[0]))<1e-9
    for stage in ('pre','post') if post else ('pre',):
        boots=[]
        for i in (0,1):
            audit=case/f'{stage}-{i}';req=load(audit/'request.json');rr=load(audit/'result.json')
            assert req['selector']==9 and req['length']==1048576
            assert rr['sha256']==STOCK and rr['bytes']==1048576 and rr['old_after']['driver'] is None
            assert sha((audit/'data.bin').read_bytes())==STOCK
            assert (audit/'status.txt').read_text().strip()=='done=1 status=0 residual=0 selector=9 length=1048576 released=0 guard_changes=0'
            boots.append(req['boot_id'])
        assert boots[0]==boots[1]
        assert (boots[0]==result['boot_id'])==(stage=='pre')
    # Fixed, predeclared steady window excludes first-four paired PIO captures
    # and the deliberate generation-eight stalled-host test.
    rows=receipts[11:31];hrows=http['frames'][11:31]
    frames=[(p/'live-frames'/f"frame-{r['generation']:04d}.bin").read_bytes() for r in rows]
    return dict(card_fnv_mode=result.get('card_fnv_mode','on'),frames=32,paired_pio=result['paired_frames'],native_wad_requests=5043,
        total_wad_requests=len(reads),tamper_rejections=len(mutations)+4,
        identical_old_pixels_palette=True,post_reset_flash_audits=post,
        inclusive_card_fps=result['frame_timing']['render_fps'],
        steady_frames=[12,31],steady_card_fps=1900/(ticks[30]-ticks[11]),
        steady_http_observer_fps=19e9/(hrows[-1]['received_monotonic_ns']-hrows[0]['received_monotonic_ns']),
        observed_to_http_ms=stats([r['observed_to_http_ns']/1e6 for r in rows]),
        renderer_wall_ms=stats([struct.unpack_from('<I',b,64784)[0] for b in frames]),
        renderer_sampled_cpu_ms=stats([10*struct.unpack_from('<I',b,64848)[0] for b in frames]))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--case',type=Path);a.add_argument('--without-post',action='store_true');a.add_argument('--archive',type=Path,default=ROOT/'accepted.tar.gz');args=a.parse_args()
    if args.case:report=verify(args.case,not args.without_post)
    else:
        with tempfile.TemporaryDirectory(prefix='i960-doom-dma-replay-') as d:
            with tarfile.open(args.archive) as t:t.extractall(d,filter='data')
            report=verify(Path(d)/'case',not args.without_post)
    print(json.dumps(report,indent=2))

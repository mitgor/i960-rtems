#!/usr/bin/env python3
"""Explicit hardware acceptance test; never imported by offline test discovery."""
import argparse,base64,errno,fcntl,hashlib,json,os,re,subprocess,time,zipfile
from pathlib import Path
from session import Session,bio
from tetris_replay import next_request,stats
DBG=Path('/sys/kernel/debug/dac960session')
ROM_SHA='a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0'
def sha(b):return hashlib.sha256(b).hexdigest()
def capture(out):
    out.mkdir()
    for p in DBG.iterdir(): (out/p.name).write_bytes(p.read_bytes())
def close_check(out):
    capture(out)
    log=(out/'result.txt').read_text()
    assert 'SESSION CLOSE rc=0 pending=0 exec-dirty=0 stage-dirty=0' in log,log
    original=(out/'stage-before-a5.bin').read_bytes()
    assert sha(original)==ROM_SHA
    for n in ['stage-before-5a.bin','stage-restored-a5.bin','stage-restored-5a.bin']:
        assert (out/n).read_bytes()==original,n
    for a,b in [('exec-ram-before-a5.bin','exec-ram-restored-a5.bin'),('exec-flash-before-a5.bin','exec-flash-restored-a5.bin'),('upload-test.bin','exec-flash-followup.bin')]:
        assert (out/a).read_bytes()==(out/b).read_bytes(),(a,b)
    return log

def main():
    p=argparse.ArgumentParser();p.add_argument('--payload',type=Path,required=True);p.add_argument('--module',type=Path,required=True);p.add_argument('--oracle',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--steps',type=int,default=3)
    a=p.parse_args();a.output.mkdir()
    code=a.payload.read_bytes();image=bio.prepare(code,b'',8192,1)
    with open('/run/lock/i960-loadrun.lock','w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not any(Path('/sys/module/'+m).exists() for m in ['dac960dump','dac960loadrun','dac960program','dac960session'])
        assert not Path('/sys/bus/pci/devices/0000:37:09.1/driver').exists()
        name='i960/session-'+sha(image)+'.bin';fw=Path('/lib/firmware')/name
        fw.parent.mkdir(exist_ok=True);fw.write_bytes(image)
        subprocess.run(['insmod',str(a.module),'firmware_name='+name,'pointer_check=1','runtime_check=1','stage_check=1','buffer_io=1',f'payload_argument={bio.BASE}'],check=True)
        capture(a.output/'preflight')
        assert 'experiment-result=0 pending=0;' in (a.output/'preflight/result.txt').read_text()
        rows=[];state=None
        with zipfile.ZipFile(a.output/'steps.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            t=time.monotonic_ns();s=Session();open_ns=time.monotonic_ns()-t
            try:
                capture(a.output/'open')
                try:other=Session()
                except OSError as e:assert e.errno==errno.EBUSY
                else:other.close();raise AssertionError('second owner admitted')
                for i in range(a.steps):
                    kind,request=next_request(state,i)
                    expected=subprocess.run([str(a.oracle)],input=request,stdout=subprocess.PIPE,check=True).stdout
                    block=bio.prepare(code,request,8192,i+1)[bio.OFFSET:]
                    t=time.monotonic_ns();status,output,response=s.step(block);elapsed=time.monotonic_ns()-t
                    assert status==0 and output==expected
                    before=DBG.joinpath('stage-before-a5.bin').read_bytes()
                    after=DBG.joinpath('payload-after-a5.bin').read_bytes()
                    assert DBG.joinpath('payload-after-5a.bin').read_bytes()==after
                    full=image[:bio.OFFSET]+block+before[bio.IMAGE_SIZE:]
                    assert len(after) in (bio.IMAGE_SIZE,524288)
                    assert bio.response(full,after+before[len(after):])==(status,expected)
                    log=DBG.joinpath('result.txt').read_text()
                    submits=re.findall(r'^submit op=(\w+) id=(\d+)',log,re.M)
                    completes=re.findall(r'^complete op=(\w+) id=(\w+) status=(\w+).*guard-changed=(\d+)',log,re.M)
                    assert len(submits)==len(completes)
                    for (op,tag),(cop,ctag,cs,cguard) in zip(submits,completes):
                        assert op==cop and int(tag)==int(ctag,16) and cguard=='0'
                        assert int(cs,16) in ([0x17d,0x17e,0x17f] if op=='6f' else [0])
                    assert sum(int(c[2],16)==0x17f for c in completes)==1
                    row=dict(index=i,kind=kind,elapsed_ns=elapsed,commands=len(submits),request=base64.b64encode(request).decode(),response_sha256=sha(output),audit_bytes=len(after),image_sha256=sha(after))
                    z.writestr(f'{i:05d}/result.txt',log)
                    z.writestr(f'{i:05d}/response.bin',response)
                    delta=(int.from_bytes(after,'little')^int.from_bytes(before[:len(after)],'little')).to_bytes(len(after),'little')
                    z.writestr(f'{i:05d}/image.xor',delta)
                    rows.append(row);state=output[:240]
                    with (a.output/'progress.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
                    if i==0:
                        try:os.write(s.fd,block)
                        except OSError as e:assert e.errno==errno.EINVAL
                        else:raise AssertionError('stale request admitted')
                    if (i+1)%100==0:print('verified',i+1,flush=True)
            finally:
                t=time.monotonic_ns();s.close();close_ns=time.monotonic_ns()-t
            close_check(a.output/'close')
        subprocess.run(['rmmod','dac960session'],check=True)
        assert not Path('/sys/bus/pci/devices/0000:37:09.1/driver').exists()
        summary=dict(steps=len(rows),latency=stats([r['elapsed_ns'] for r in rows]),open_ms=open_ns/1e6,close_ms=close_ns/1e6,commands=sorted(set(r['commands'] for r in rows)),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),payload_sha256=sha(code),module_sha256=sha(a.module.read_bytes()),restored=True,unloaded=True)
        (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()

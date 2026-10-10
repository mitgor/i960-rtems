#!/usr/bin/env python3
"""Explicit Linux/card lifecycle test. SIGKILL is directed only at our children."""
import argparse,base64,errno,json,os,signal,subprocess,sys,time
from pathlib import Path
from session import Session,bio
from live_test import capture,close_check,sha,DBG
from tetris_wire import request

def child(mode,block):
    print('opening',flush=True)
    s=Session();print('opened',flush=True)
    if mode=='open':time.sleep(10)
    elif mode=='step':
        sys.stdin.readline();print('stepping',flush=True)
        s.step(block);print('stepped',flush=True);time.sleep(10)
    else:
        s.step(block);sys.stdin.readline();print('closing',flush=True)
        s.close();print('closed',flush=True);time.sleep(10)

def main():
    p=argparse.ArgumentParser();p.add_argument('--module',type=Path,required=True);p.add_argument('--payload',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir()
    code=a.payload.read_bytes();image=bio.prepare(code,request(seed=1),8192,1);block=image[bio.OFFSET:]
    name='i960/session-lifecycle-'+sha(image)+'.bin';(Path('/lib/firmware')/name).write_bytes(image)
    subprocess.run(['insmod',str(a.module),'firmware_name='+name,'pointer_check=1','runtime_check=1','stage_check=1','buffer_io=1',f'payload_argument={bio.BASE}'],check=True)
    capture(a.output/'preflight');results=[]
    for mode,delays in [('open',[0.001,0.020,0.050,0.075]),('step',[0.001,0.010,0.025,0.040,0.060]),('close',[0.001,0.030,0.060,0.100])]:
        for delay in delays:
            cmd=[sys.executable,'-c','from lifecycle_test import child;import base64;child('+repr(mode)+',base64.b64decode('+repr(base64.b64encode(block).decode())+'))']
            proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
            assert proc.stdout.readline().strip()=='opening'
            if mode!='open':
                assert proc.stdout.readline().strip()=='opened';proc.stdin.write('go\n');proc.stdin.flush()
                assert proc.stdout.readline().strip()==('stepping' if mode=='step' else 'closing')
            time.sleep(delay);proc.kill();assert proc.wait(timeout=10)==-signal.SIGKILL
            label=f'{mode}-{int(delay*1000):03d}ms';close_check(a.output/label)
            results.append(dict(test=label,restored=True));print(label,'restored',flush=True)
    with Session() as s:
        try:os.read(s.fd,bio.SIZE)
        except OSError as e:assert e.errno==errno.EAGAIN
        else:raise AssertionError('read without response')
        try:os.write(s.fd,b'bad')
        except OSError as e:assert e.errno==errno.EINVAL
        else:raise AssertionError('short write admitted')
        assert os.write(s.fd,block)==bio.SIZE
        try:os.write(s.fd,block)
        except OSError as e:assert e.errno==errno.EBUSY
        else:raise AssertionError('unread response overwritten')
        assert len(os.read(s.fd,bio.SIZE))==bio.SIZE
        unload=subprocess.run(['rmmod','dac960session'],capture_output=True,text=True)
        assert unload.returncode!=0
        (a.output/'owned-rmmod.txt').write_text(unload.stdout+unload.stderr)
    close_check(a.output/'protocol-close');results.append(dict(test='protocol-and-module-ownership',restored=True))
    s=Session()
    proc=subprocess.Popen([sys.executable,'-c','import sys;print("inherited",flush=True);sys.stdin.readline()'],pass_fds=[s.fd],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
    assert proc.stdout.readline().strip()=='inherited';s.close(verify=False)
    try:other=Session()
    except OSError as e:assert e.errno==errno.EBUSY
    else:other.close();raise AssertionError('inherited owner lost')
    proc.stdin.write('exit\n');proc.stdin.flush();assert proc.wait(timeout=10)==0
    close_check(a.output/'inherited-close');results.append(dict(test='last-inherited-descriptor',restored=True))
    subprocess.run(['rmmod','dac960session'],check=True)
    assert not Path('/sys/bus/pci/devices/0000:37:09.1/driver').exists()
    (a.output/'summary.json').write_text(json.dumps(dict(tests=results,unloaded=True,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip()),indent=2)+'\n')
if __name__=='__main__':main()

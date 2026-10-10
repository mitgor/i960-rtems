#!/usr/bin/env python3
"""Explicit paced card test, with oracle preparation and archival outside timing."""
import argparse,json,subprocess,time,zipfile
from pathlib import Path
from session import Session,bio
from live_test import capture,close_check,sha,DBG
from tetris_replay import next_request,stats

def main():
    p=argparse.ArgumentParser();p.add_argument('--module',type=Path,required=True);p.add_argument('--payload',type=Path,required=True);p.add_argument('--oracle',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--steps',type=int,default=400);a=p.parse_args();a.output.mkdir()
    code=a.payload.read_bytes();state=None;trace=[]
    for i in range(a.steps):
        kind,r=next_request(state,i);expected=subprocess.run([str(a.oracle)],input=r,stdout=subprocess.PIPE,check=True).stdout
        trace.append((bio.prepare(code,r,8192,i+1)[bio.OFFSET:],expected));state=expected[:240]
    image=bio.prepare(code,b'',8192,1);name='i960/session-'+sha(image)+'.bin';(Path('/lib/firmware')/name).write_bytes(image)
    subprocess.run(['insmod',str(a.module),'firmware_name='+name,'pointer_check=1','runtime_check=1','stage_check=1','buffer_io=1',f'payload_argument={bio.BASE}'],check=True)
    responses=[];times=[];period=50_000_000
    with Session() as s:
        capture(a.output/'open');start=time.monotonic_ns()
        for i,(block,expected) in enumerate(trace):
            target=start+i*period;time.sleep(max(0,(target-time.monotonic_ns())/1e9))
            t=time.monotonic_ns();status,output,response=s.step(block);end=time.monotonic_ns()
            assert status==0 and output==expected
            times.append(dict(index=i,start_ns=t-start,elapsed_ns=end-t,late_ns=max(0,end-(target+period))))
            responses.append((response,DBG.joinpath('result.txt').read_bytes()))
        elapsed=time.monotonic_ns()-start
    close_check(a.output/'close');subprocess.run(['rmmod','dac960session'],check=True)
    with zipfile.ZipFile(a.output/'steps.zip','w',zipfile.ZIP_DEFLATED) as z:
        for i,((block,expected),(response,log)) in enumerate(zip(trace,responses)):
            z.writestr(f'{i:05d}/request.bin',block);z.writestr(f'{i:05d}/response.bin',response);z.writestr(f'{i:05d}/result.txt',log)
    (a.output/'timing.json').write_text(json.dumps(times,indent=2)+'\n')
    summary=dict(steps=len(trace),target_hz=20,elapsed_s=elapsed/1e9,achieved_hz=len(trace)/(elapsed/1e9),latency=stats([r['elapsed_ns'] for r in times]),late_frames=sum(r['late_ns']>0 for r in times),max_late_ms=max(r['late_ns'] for r in times)/1e6,restored=True,unloaded=True)
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()

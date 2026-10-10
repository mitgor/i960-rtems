#!/usr/bin/env python3
"""Validate every recorded terminal request/response against the native C core."""
import argparse,ctypes,gzip,hashlib,json,struct
from pathlib import Path
from terminal import TRACE
from validate import verify_close

def validate(folder,library):
    lib=ctypes.CDLL(str(library.resolve()));fn=lib.tetris_request
    fn.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_void_p,ctypes.c_uint];fn.restype=ctypes.c_uint
    meta=json.loads((folder/'metadata.json').read_text());summary=json.loads((folder/'summary.json').read_text())
    previous=None;count=0;restarts=0;keys={};phases={};tick_total=0;first_ns=None;last_ns=0
    digest=hashlib.sha256()
    with gzip.open(folder/'frames.bin.gz','rb') as f:
        while data:=f.read(TRACE.size):
            assert len(data)==TRACE.size,'truncated frame record'
            start,latency,late,request,response=TRACE.unpack(data)
            assert start>=last_ns and latency>0;last_ns=start
            if first_ns is None:first_ns=start
            op,seed,key,ticks=struct.unpack_from('<4I',request)
            if op==1:
                assert seed==meta['seed'] and not key and not ticks and request[16:]==bytes(240)
                restarts+=previous is not None
            else:
                assert op==0 and not seed and previous==request[16:] and ticks<=20
            expected=ctypes.create_string_buffer(2160)
            assert fn(request,len(request),expected,2160)==0
            assert expected.raw==response,f'frame {count} differs from native C'
            assert all(32<=b<=126 for b in response[240:])
            previous=response[:240];count+=1;tick_total+=ticks
            keys[str(key)]=keys.get(str(key),0)+1
            phase=struct.unpack_from('<I',previous,32)[0];phases[str(phase)]=phases.get(str(phase),0)+1
            digest.update(data)
    assert count>0
    if 'frames' in summary:assert summary['frames']==count
    if 'restarts' in summary:assert summary['restarts']==restarts
    assert summary['restored'] and summary['unloaded'] and not summary['driver_bound']
    verify_close(folder/'close')
    return dict(valid=True,frames=count,restarts=restarts,phases=phases,keys=keys,ticks=tick_total,
                trace_sha256=digest.hexdigest(),recorded_span_s=(last_ns-first_ns)/1e9,restored=True,unloaded=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('--library',type=Path,required=True);a=p.parse_args()
    print(json.dumps(validate(a.folder,a.library),indent=2))

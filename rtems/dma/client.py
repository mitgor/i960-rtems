"""Bounded DMA acceptance. Preserve complete coherent buffers and all audit pairs."""
import errno,fcntl,json,struct,time
from pathlib import Path
CMD=0xc4204d07

def exercise(fd,epoch,out,audit):
 log=out/'dma-journal.jsonl'
 def call(op,n,offset,seq,seed=0,e=epoch):
  raw=bytearray(struct.pack('<8I',op,e,n,offset,seq,seed,0,0)+bytes(1024));before=raw.hex();start=time.monotonic_ns()
  try:fcntl.ioctl(fd,CMD,raw,True)
  except OSError as exc:
   with log.open('a') as f:f.write(json.dumps(dict(request=before,errno=exc.errno,ns=time.monotonic_ns()-start))+'\n')
   raise
  with log.open('a') as f:f.write(json.dumps(dict(request=before,response=raw.hex(),ns=time.monotonic_ns()-start))+'\n')
  return raw
 def refuse(op,n,offset,seq,seed=0,e=epoch,expected=errno.EINVAL):
  try:call(op,n,offset,seq,seed,e)
  except OSError as exc:assert exc.errno==expected
  else:raise AssertionError('invalid DMA request accepted')
 refuse(1,0,0,1);refuse(1,65537,0,1);refuse(1,1,4096,1)
 refuse(1,1,0,1,e=epoch^0x8000 or 1,expected=errno.ESTALE)
 refuse(2,1024,0,1,expected=errno.ESTALE)
 cases=[(1,0),(3,1),(4,2),(31,3),(64,0),(511,1),(1024,0),(2048,0),(4095,3),(4096,0),(65536,0),(65536,4095)]*2
 results=[]
 for seq,(n,offset) in enumerate(cases,1):
  audit();seed=0x13570000+seq;start=time.monotonic_ns();raw=call(1,n,offset,seq,seed);elapsed=time.monotonic_ns()-start
  report=list(struct.unpack_from('<32I',raw,32));assert report[0:2]==[0x31414d44,seq] and report[3:5]==[n,seed] and report[14:16]==[1,0]
  data=b''.join(call(2,1024,i,seq)[32:] for i in range(0,73728,1024))
  expected=bytearray(b'\xa5'*73728);expected[4096+offset:4096+offset+n]=bytes((i*13^seed^(i>>8))&255 for i in range(n));assert data==expected
  (out/f'dma-{seq:03}.bin').write_bytes(data)
  refuse(1,n,offset,seq,seed,expected=errno.ESTALE)
  if seq>1:refuse(2,1024,0,seq-1,expected=errno.ESTALE)
  audit();results.append(dict(seq=seq,length=n,offset=offset,seed=seed,ns=elapsed,report=report))
  (out/'dma-results.json').write_text(json.dumps(results,indent=2)+'\n');print('DMA exact buffer/audits passed',seq,n,flush=True)
 refuse(2,1024,73728,seq);refuse(2,1024,1,seq)
 return results

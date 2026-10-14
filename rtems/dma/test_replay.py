#!/usr/bin/env python3
"""Exercise the actual capture client against a model, then independent replay."""
import contextlib,errno,io,json,struct,subprocess,tempfile
from pathlib import Path
from types import SimpleNamespace
import client
from verify import verify
# Captures carry Linux errno values even when this test runs on macOS.
errno=SimpleNamespace(EINVAL=22,ESTALE=116)
client.errno=errno
with tempfile.TemporaryDirectory() as temp:
 root=Path(temp);out=root/'live';out.mkdir();(root/'residentnet').mkdir()
 (root/'residentnet/kernel.symbols').write_text('c0f70000 b _dma_desc_storage\nc0f80000 b _dma_source\n')
 # Use a source interval fitting the real mutable allocation.
 (root/'residentnet/kernel.symbols').write_text('c0f50000 b _dma_desc_storage\nc0f60000 b _dma_source\n')
 (out/'controls.json').write_text(json.dumps([dict(words=[],epoch=42)]));seq=0;data=None;snaps=[dict(words=[0,0,1])]*4
 def audit():snaps.append(dict(words=[0,0,1]))
 def ioctl(fd,cmd,raw,mutate):
  global seq,data
  op,e,n,off,s,seed,_,_=struct.unpack_from('<8I',raw)
  def fail(code):raise OSError(code,'modeled refusal')
  if (op==1 and (not n or n>65536 or off>4095)) or (op==2 and (off>73728-1024 or off&1023)):fail(errno.EINVAL)
  if e!=42 or (op==1 and s!=seq+1) or (op==2 and (not seq or s!=seq)):fail(errno.ESTALE)
  if op==1:
   seq=s;data=bytearray(b'\xa5'*73728);data[4096+off:4096+off+n]=bytes((i*13^seed^(i>>8))&255 for i in range(n))
   report=[0x31414d44,s,0x101000+off,n,seed,0,1,0xc0f50000,0,0,7,2,0,0,1,0]+[0]*16
   struct.pack_into('<32I',raw,32,*report)
  else:raw[32:]=data[off:off+1024]
 client.fcntl.ioctl=ioctl
 with contextlib.redirect_stdout(io.StringIO()):client.exercise(1,42,out,audit)
 snaps[-1]=dict(words=[0,0,2]);(out/'snapshots.json').write_text(json.dumps(snaps))
 result=verify(root,out);assert result['transfers']==24 and result['refusals']==54
 r=subprocess.run(['python3',str(Path(__file__).with_name('tamper.py')),str(root)],capture_output=True,text=True,check=True)
 assert json.loads(r.stdout)['rejected']==23
 print('Capture client and independent replay: 24 buffers, 54 refusals, 23 mutations rejected')

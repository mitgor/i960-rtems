#!/usr/bin/env python3
"""Offline verification of original paired evidence; never accesses hardware."""
import argparse,gzip,hashlib,json,struct,subprocess,tempfile
from pathlib import Path
from live import decode
from test_gate import compile_gate,pack
from run import verify_close
import wire

def verify(root,out,module,gate,initial=False):
 code=(root/'ownirq/kernel.bin').read_bytes();mod=(root/module/'dac960rtems.ko').read_bytes();identity=json.loads((out/'request.json').read_text())
 for key,data in [('payload_sha256',code),('image_sha256',wire.prepare(code)),('module_sha256',mod)]:assert identity[key]==hashlib.sha256(data).hexdigest()
 control=json.loads((out/'control.json').read_text());epoch=control['epoch'];mode=control['mode'];req=struct.pack('<3I',0x31505453,epoch,mode)
 assert control['pending'] and control['reply'][6]==0x75000000|epoch and control['reply'][7]==1 and not(control['reply'][3]&1) and not(control['reply'][5]&1)
 failed=initial or mode==5;cap=out/('failure-000001' if failed else 'close')
 first=(cap/'payload-after-a5.bin').read_bytes();second=(cap/'payload-after-5a.bin').read_bytes()
 first=first[:wire.bio.IMAGE_SIZE];second=second[:wire.bio.IMAGE_SIZE];assert first==second
 original=(out/'open/stage-before-a5.bin').read_bytes();before=wire.prepare(code,req)+original[wire.bio.IMAGE_SIZE:]
 status,raw=wire.response(before,first+original[len(first):]);assert status==0 and len(raw)==1024
 w=list(struct.unpack('<256I',raw));assert w[3:5]==[mode,epoch]
 result=subprocess.check_output([str(gate)],input=raw);assert result==(b'0' if initial else b'R' if mode==5 else b'1'),result
 if initial:
  assert w[51]==0;fixed=w.copy();fixed[51]=1;assert subprocess.check_output([str(gate)],input=pack(fixed))==b'1'
  row=dict(mode=mode,epoch=epoch,initial_padding_bug=True,word51=0)
 else:
  row=decode(raw);assert (out/'ownirq.bin').read_bytes()==raw
 if not failed:
  trace=gzip.decompress((out/'trace.bin.gz').read_bytes());elapsed,n=struct.unpack_from('<QI',trace);assert elapsed>0 and n==12 and trace[12:24]==req and struct.unpack_from('<I',trace,24)[0]==1024 and trace[28:]==raw
  assert gzip.decompress((out/'audit-000001.bin.gz').read_bytes())==first
  verify_close(cap);summary=json.loads((out/'summary.json').read_text());assert summary['restored'] and summary['unloaded'] and not summary['driver_bound']
  log=(out/'control-log.txt').read_text();assert log.index('OWNIRQ verified resource ownership')<log.index('STOP1 callback returned; MU words/masks restored')
  before_mu=json.loads((out/'mu-before.json').read_text());after=json.loads((out/'mu-after.json').read_text())
  for sample in after['samples']:
   for name in ('IMR1','OMR1','IIMR','OIMR'):assert sample[name]==before_mu['samples'][0][name]
   for name in ('IISR','OISR'):assert int(sample[name],16)&2==int(before_mu['samples'][0][name],16)&2
 else:
  log=(cap/'result.txt').read_text();assert 'CONCURRENT QUIESCED ioctl' in log and 'OWNIRQ resource proof rejected after callback completion' in log
  assert 'submit op=' not in log.split('OWNIRQ resource proof rejected after callback completion',1)[1]
  if not initial:
   e=json.loads((out/'acceptance.json').read_text());assert e['report']==row and e['write_errno']==61 and e['before_unload']==e['after_unload'] and e['unload']['returncode']!=0
   r=e['before_unload'];assert r['retained']==[1,0,0,0,1,1,1,1] and r['refcount']>0 and r['bound'] and r['debugfs']
  else:
   r=(root/'ownirq-initial-retention.txt').read_text();assert r.count('1,0,0,0,1,1,1,1')==2 and 'Module dac960rtems is in use' in r
 bad=[]
 if not initial:
  for index in (2,17,18,19,20,22,23,24,26,27,31,32,34,40,44,51,53,54,88,170,247,249,250,251,252,253,254,255):
   x=w.copy();x[index]=0 if x[index] else 1;bad.append(pack(x))
  assert subprocess.check_output([str(gate)],input=b''.join(bad))==b'0'*len(bad)
 return dict(path=str(out),report=row,paired_response_verified=True,cleanup_verified=not failed,gate=result.decode(),damaged_reports_rejected=len(bad))

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--module',default='ownirq-module-v3');p.add_argument('--initial',action='store_true');p.add_argument('--output',type=Path);p.add_argument('paths',type=Path,nargs='+');a=p.parse_args()
 with tempfile.TemporaryDirectory() as tmp:
  gate=compile_gate(Path(tmp));result=[verify(a.root,path,a.module,gate,a.initial) for path in a.paths]
 if (a.root/'http-after-ownership/close').exists():verify_close(a.root/'http-after-ownership/close')
 text=json.dumps(result,indent=2)+'\n';print(text,end='')
 if a.output:a.output.write_text(text)
if __name__=='__main__':main()

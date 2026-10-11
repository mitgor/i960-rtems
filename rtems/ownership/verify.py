#!/usr/bin/env python3
"""Independently replay saved card records through native policy and report gates."""
import argparse,gzip,hashlib,json,os,struct,subprocess,tempfile
from pathlib import Path
from live import decode
from run import verify_close
import wire
HERE=Path(__file__).resolve().parent

def verify(out,oracle,gate,root):
 code=(root/"ownership/kernel.bin").read_bytes();module=(root/"ownership-module/dac960rtems.ko").read_bytes();image=wire.prepare(code)
 identity=json.loads((out/"request.json").read_text())
 for key,data in (("payload_sha256",code),("image_sha256",image),("module_sha256",module)):assert identity[key]==hashlib.sha256(data).hexdigest()
 original=(out/"open/stage-before-a5.bin").read_bytes()
 assert original==(out/"open/stage-before-5a.bin").read_bytes()
 rows=json.loads((out/'ownership.json').read_text());trace=gzip.decompress((out/'trace.bin.gz').read_bytes());offset=0
 requests=b'';reports=b'';expected=b''
 for i,row in enumerate(rows,1):
  req=bytes.fromhex(row['request']);report=bytes.fromhex(row['report']);w=decode(report)
  assert w[2]==i and w[3]==struct.unpack('<4I',req)[1]
  elapsed,n=struct.unpack_from('<QI',trace,offset);offset+=12;assert elapsed>0 and n==16
  assert trace[offset:offset+n]==req;offset+=n
  n,=struct.unpack_from('<I',trace,offset);offset+=4;assert n==256 and trace[offset:offset+n]==report;offset+=n
  requests+=req;reports+=report;expected+=struct.pack('<20I',*(w[4:17]+w[29:35]+[0]))
 assert offset==len(trace)
 actual=subprocess.run([str(oracle)],input=requests,stdout=subprocess.PIPE,check=True).stdout
 assert actual==expected,'hardware policy differs from native oracle'
 gate_result=subprocess.run([str(gate)],input=reports,stdout=subprocess.PIPE,check=True).stdout.decode().strip()
 for audit in out.glob('audit-*.bin.gz'):
  data=gzip.decompress(audit.read_bytes());assert len(data) in (wire.bio.IMAGE_SIZE,524288)
  seq=int(audit.name.split('-')[1].split('.')[0]);assert seq<=len(rows)
  before=image[:wire.bio.OFFSET]+wire.block(bytes.fromhex(rows[seq-1]['request']),seq)+original[wire.bio.IMAGE_SIZE:]
  assert wire.response(before,data+original[len(data):])==(0,bytes.fromhex(rows[seq-1]['report']))
 capture=out/('close' if (out/'close').exists() else 'retained')
 first=(capture/'payload-after-a5.bin').read_bytes();second=(capture/'payload-after-5a.bin').read_bytes();assert first==second
 before=image[:wire.bio.OFFSET]+wire.block(req,len(rows))+original[wire.bio.IMAGE_SIZE:]
 assert wire.response(before,first+original[len(first):])==(0,report)
 # Full original image restoration is required for normal sessions only.
 if (out/'close').exists():
  verify_close(out/'close');log=(out/'close/result.txt').read_text()
  if (out/'final-step.txt').exists():
   final_log=(out/'final-step.txt').read_text();assert final_log.index('OWNERSHIP FINALIZED: all workers suspended, no external leases, callback returned')<final_log.index('SESSION STEP sequence=')
  assert w[5]==1
  summary=json.loads((out/'summary.json').read_text());assert summary['restored'] and summary['unloaded'] and not summary['driver_bound'] and summary['steps']==len(rows)
 else:
  log=(out/'retained/result.txt').read_text();assert 'OWNERSHIP refuses restore before finalization' in log and not w[5]
  assert 'submit op=' not in log.split('OWNERSHIP refuses restore before finalization',1)[1]
  assert 'SESSION CLOSE rc=0' not in log and 'SESSION FAILED: retained DMA/module; reboot required' in log
  evidence=json.loads((out/'acceptance.json').read_text());assert evidence['before_unload']==evidence['after_unload']
  state=evidence['before_unload'];assert state['retained']==[1,0,1,1,1,1] and state['refcount']>0 and state['bound'] and state['debugfs']
  assert evidence['unload']['returncode']!=0 and evidence['boot_id']==identity['boot_id']
 return dict(path=str(out),callbacks=len(rows),native_policy_match=True,report_gate=gate_result,normal_close=(out/'close').exists())

def main():
 p=argparse.ArgumentParser();p.add_argument('paths',type=Path,nargs='+');p.add_argument('--output',type=Path);p.add_argument('--root',type=Path,required=True);a=p.parse_args()
 with tempfile.TemporaryDirectory() as tmp:
  exe=[]
  for source in ('test_oracle.c','test_reports.c'):
   target=Path(tmp)/source[:-2];subprocess.run([os.environ.get('CC','cc'),'-std=c99','-Wall','-Wextra','-fsanitize=address,undefined',str(HERE/source),'-o',str(target)],check=True);exe.append(target)
  result=[verify(path,*exe,a.root) for path in a.paths]
 if (a.root/'http-after-containment-batch/close').exists():verify_close(a.root/'http-after-containment-batch/close')
 text=json.dumps(result,indent=2)+'\n';print(text,end='')
 if a.output:a.output.write_text(text)
if __name__=='__main__':main()

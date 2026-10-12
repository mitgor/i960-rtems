"""Independent owned control journal and stable proof postconditions."""
import hashlib,importlib.util,json,struct
from pathlib import Path
MAGIC=0x3252444f

def prepare(capture,build,requests,responses):
 r=json.loads((capture/'owned-results.json').read_text());m=json.loads((build/'manifest.json').read_text());b=(build/'template.bin').read_bytes();assert r['manifest']==m and (capture/'owned-template.bin').read_bytes()==b and hashlib.sha256(b).hexdigest()==m['sha256']
 rows=[w for p,w in zip(requests,responses) if struct.unpack_from('<I',p,8)[0]==16]
 assert [w[2] for w in rows]==[1,2,0,0,0] and [w[5] for w in rows]==[0,0]+[MAGIC^0x49393630^code for code in (37,53,37)]
 result_rows=[w[5] for p,w in zip(requests,responses) if struct.unpack_from('<I',p,8)[0]==17]
 assert len(result_rows)==24 and [run['stop'] for run in r['runs']]==[False,True,False]
 for i,run in enumerate(r['runs']):
  value=result_rows[8*i:8*i+8];assert run['result']==value and value[:3]==[0x49393630^7,3,2] and value[5:]==[int(i==1),53 if i==1 else 37,0]
  assert run['value']==rows[2+i][5] and 0<=value[4]<=12000 and (i==1 or value[4]>=10000) and 0<=value[3]<=1200
  ctl=run['control'];assert ctl[0:4]==[MAGIC,i+1,0,int(i==1)] and ctl[5:]==[i+1,i+1,int(i>=1)]
  assert run['seconds']>=0 and (i==1 or run['seconds']>=10)
  assert len(run['requests'])==int(i==1)
 bases=[w[5] for p,w in zip(requests,responses) if struct.unpack_from('<I',p,8)[0]==14]
 if (capture/'engine-results.json').exists():bases=bases[:-3]
 base=bases[-1];assert r['base']==0xc02d0040+base and base%16==0
 epochs={struct.unpack_from('<I',bytes.fromhex(row['request']),4)[0] for row in map(json.loads,(capture/'upload-journal.jsonl').read_text().splitlines()) if 'errno' not in row}
 assert len(epochs)==1
 states=[];errors=[];stops=[];last=None
 for row in map(json.loads,(capture/'owned-journal.jsonl').read_text().splitlines()):
  req=bytes.fromhex(row['request']);assert len(req)==1056;op,epoch,n,*zero=struct.unpack_from('<8I',req);assert op in (5,6) and epoch in epochs and not any(zero)
  if op==6:
   body=struct.unpack_from('<8I',req,32);assert n==32 and body[0]==MAGIC and body[1] and not any(body[2:]) and not any(req[64:])
   if 'errno' in row:assert row['errno']==116;errors.append(body[1]);continue
  else:assert not n
  res=bytes.fromhex(row['response']);assert len(res)==1056;head=struct.unpack_from('<8I',res);assert head[:2]==(op,epoch) and head[2:]==(32,1,0,0,0,0)
  if op==6:
   assert last and last[1:4]==(2,1,0) and body[1]==2 and res[32:64]==req[32:64];stops.append(body[1])
  else:
   w=struct.unpack_from('<8I',res,32);assert w[0]==MAGIC and w[1] in range(4) and w[2] in (0,1) and w[3] in (0,1) and w[5]<=w[1] and w[6]<=w[1] and w[7]<=w[5]
   if last:assert all(w[index]>=last[index] for index in (1,4,5,6,7))
   last=w;states.append(w)
 assert stops==[2] and errors==[1,1,3,2,3],(stops,errors)
 assert states[-1]==tuple(r['runs'][-1]['control'])
 request=r['runs'][1]['requests'][0];assert request['generation']==2 and tuple(request['snapshot']) in states and request['snapshot'][1:4]==[2,1,0]
 threshold=request['snapshot'][4]-r['runs'][0]['control'][4];assert 16<=threshold<1000
 return dict(probe_bytes=len(b),relocations=len(m['relocations']),normal_entries=2,cancelled_entries=1,nonlocal_exits=6,threshold=threshold,epochs=list(epochs),refused_stop_generations=errors)

def native(prefix,t,build,info):
 spec=importlib.util.spec_from_file_location('owned_native',Path(__file__).resolve().parents[2]/'game/doom/runtime/owned/native.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
 prefix=helper.prefix(prefix);(t/'owned_probe_bytes.h').write_bytes((build/'owned_probe_bytes.h').read_bytes())
 prefix=prefix.replace('static const struct {unsigned n,w[136];} recorded[]=', 'static void owned_native_service(void);\nstatic const struct {unsigned n,w[136];} recorded[]=')
 prefix=prefix.replace('static void runtime_service(void){unsigned i;', 'static void runtime_service(void){unsigned i;owned_native_service();')
 prefix += '''
static unsigned native_seen,native_start,native_stopped;
static void owned_native_service(void){
 if(!owned_running)return;
 if(native_seen!=owned_generation){native_seen=owned_generation;native_start=owned_yields;}
 if(owned_generation==2&&!native_stopped&&owned_yields-native_start>='''+str(info['threshold'])+'''){
  assert(doom_runtime_owned_control(0x7a,0,3,1)==~0u);
  assert(!doom_runtime_owned_control(0x7a,0,2,1));native_stopped=1;
 }
}
'''
 return prefix

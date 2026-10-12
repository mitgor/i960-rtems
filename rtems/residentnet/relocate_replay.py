"""Check captured outcomes against trusted build metadata and journal order."""
import hashlib,json,struct

def prepare_relocated(capture,build,requests,responses):
 m=json.loads((build/'manifest.json').read_text());b=(build/'template.bin').read_bytes()
 result=json.loads((capture/'relocate-results.json').read_text())
 assert result['manifest']==m and (capture/'relocate-template.bin').read_bytes()==b
 assert hashlib.sha256(b).hexdigest()==m['sha256']
 rows=[w for p,w in zip(requests,responses) if struct.unpack_from('<I',p,8)[0]==13]
 assert [w[2] for w in rows]==[1,1,1,1,2,1,2,1,0,0]
 assert [w[5] for w in rows]==[0]*8+[(5*33)^0x49393630]*2
 bases=[w[5] for p,w in zip(requests,responses) if struct.unpack_from('<I',p,8)[0]==14]
 if (capture/'batch-results.json').exists():bases=bases[:-1]
 if (capture/'engine-results.json').exists():bases=bases[:-3]
 if (capture/'owned-results.json').exists():bases=bases[:-1]
 if (capture/'cache-results.json').exists():bases=bases[:-1]
 assert len(bases)==4 and all(16<=v<8*1048576-m['memory_bytes'] and v%16==0 for v in bases)
 assert [r['base_offset'] for r in result['runs']]==bases+[bases[-1]]
 assert all(r['base']==0xc02d0040+r['base_offset'] for r in result['runs'])
 selected=[rows[i] for i in (2,4,6,8,9)]
 assert [r['mode'] for r in result['runs']]==['entry','code','data','valid','valid']
 for r,w in zip(result['runs'],selected):
  assert (r['rc'],r['value'],r['handle'])==(w[2],w[5],w[15]) and r['seconds']>=0
 return dict(template_sha256=m['sha256'],file_bytes=m['file_bytes'],memory_bytes=m['memory_bytes'],relocations=len(m['relocations']),bss_bytes=128,successful_entries=2,admission_refusals=8,oracle=(5*33)^0x49393630)

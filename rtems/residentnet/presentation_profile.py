"""Versioned timing trailer; frame guards and whole-buffer audits stay separate."""
import struct
OFFSET=64768
NAMES=('magic','version','frame','mode','render_ms','bsp_ms','planes_ms','sprites_ms','screen_copy_ms','adapter_ms','previous_publish_wait_ms','display_ms','pixel_fnv','palette_fnv','clock_resolution_ms','reserved')
def fnv(data):
 h=2166136261
 for b in data:h=((h^b)*16777619)&0xffffffff
 return h
def decode(raw,g,test=False,options=None):
 options=options or {}
 assert len(raw)==65536
 w=struct.unpack_from('<16I',raw,OFFSET);d=dict(zip(NAMES,w))
 assert w[:3]==(0x31524650,1,g) and w[3] in (0,1,2,3) and w[14:]==(10,0)
 if test:assert w[3]==(0 if 17<=g<=28 else 2 if 29<=g<=40 else 1)
 assert w[4]==sum(w[5:8]) and all(x<60000 for x in w[4:12])
 end=OFFSET+64
 if options.get('cpu_profile'):
  c=struct.unpack_from('<12I',raw,end);end+=48
  assert c[:2]==(0x31555043,1) and c[3]==10
  if options.get('column_test'):
   expected=1 if 17<=g<=28 else 2 if 29<=g<=40 else 0
   assert c[10:]==(expected,96)
   d['column_mode']=c[10];d['column_cases']=c[11]
  else:assert c[10:]==(0,0)
  detail=int(17<=g<=40) if options.get('detail_test') else int(options.get('low_detail',False))
  assert c[2]==detail and c[4]==sum(c[5:8]) and all(x<6000 for x in c[4:10])
  assert all(samples*10<=wall+10 for samples,wall in zip(c[4:10],(w[4],w[5],w[6],w[7],w[8],w[9])))
  d['cpu_samples']=dict(zip(('render','bsp','planes','sprites','screen_copy','adapter'),c[4:10]));d['detail']=detail
 if options.get('detail_test') or options.get('column_test'):assert w[3]==2
 assert not any(raw[end:])
 if w[3]&1:assert w[12]==fnv(raw[:64000]) and w[13]==fnv(raw[64000:64768])
 else:assert w[12:14]==(0,0)
 return d

def preflight(admission,pipeline,pipeline_test,wad_load_test):
 if any(admission.get(k) for k in ('frame_profile','no_fnv','direct_frame','presentation_test','low_detail','detail_test','cpu_profile','column_test')):
  assert pipeline and admission.get('double_buffer'), 'presentation features require admitted two-slot ownership'
 if admission.get('presentation_test'):
  assert admission.get('frame_profile') and pipeline_test and not wad_load_test, 'mixed presentation engine requires bounded no-input comparison'
  assert not admission.get('no_fnv') and not admission.get('direct_frame')

 if admission.get('detail_test'):
  assert admission.get('cpu_profile') and admission.get('frame_profile') and pipeline_test and not wad_load_test
  assert admission.get('no_fnv') and admission.get('direct_frame') and not admission.get('presentation_test') and not admission.get('low_detail')

 if admission.get('column_test'):
  assert pipeline_test and not wad_load_test and admission.get('cpu_profile') and admission.get('frame_profile') and admission.get('low_detail')
  assert admission.get('no_fnv') and admission.get('direct_frame') and not admission.get('detail_test') and not admission.get('presentation_test')

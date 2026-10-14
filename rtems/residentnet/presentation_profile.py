"""Versioned timing trailer; frame guards and whole-buffer audits stay separate."""
import struct
OFFSET=64768
NAMES=('magic','version','frame','mode','render_ms','bsp_ms','planes_ms','sprites_ms','screen_copy_ms','adapter_ms','previous_publish_wait_ms','display_ms','pixel_fnv','palette_fnv','clock_resolution_ms','reserved')
def fnv(data):
 h=2166136261
 for b in data:h=((h^b)*16777619)&0xffffffff
 return h
def decode(raw,g,test=False):
 assert len(raw)==65536
 w=struct.unpack_from('<16I',raw,OFFSET);d=dict(zip(NAMES,w))
 assert w[:3]==(0x31524650,1,g) and w[3] in (0,1,2,3) and w[14:]==(10,0)
 if test:assert w[3]==(0 if 17<=g<=28 else 2 if 29<=g<=40 else 1)
 assert w[4]==sum(w[5:8]) and all(x<60000 for x in w[4:12])
 assert not any(raw[OFFSET+64:])
 if w[3]&1:assert w[12]==fnv(raw[:64000]) and w[13]==fnv(raw[64000:64768])
 else:assert w[12:14]==(0,0)
 return d

def preflight(admission,pipeline,pipeline_test,wad_load_test):
 if any(admission.get(k) for k in ('frame_profile','no_fnv','direct_frame','presentation_test')):
  assert pipeline and admission.get('double_buffer'), 'presentation features require admitted two-slot ownership'
 if admission.get('presentation_test'):
  assert admission.get('frame_profile') and pipeline_test and not wad_load_test, 'mixed presentation engine requires bounded no-input comparison'
  assert not admission.get('no_fnv') and not admission.get('direct_frame')

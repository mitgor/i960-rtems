#!/usr/bin/env python3
"""Derive an audited 32-frame delay profiler from the accepted new-card gate."""
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[4]
src=root/'rtems/accele160/doom_play'
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
def replace(s,a,b):
    assert s.count(a)==1,(a,s.count(a))
    return s.replace(a,b)
s=(src/'app.c').read_text()
s=replace(s,'static unsigned int frame_ticks[DOOM_FPS_FRAMES];','static unsigned int frame_ticks[DOOM_FPS_FRAMES];\nstatic unsigned int phase_ticks[DOOM_FPS_FRAMES][4];')
s=replace(s,' for(i=0;i<FRAME_BYTES;i++)\n  (slot?frame2_base:frame_base)[i]=', ' phase_ticks[z-1u][0]=ticks;\n for(i=0;i<FRAME_BYTES;i++)\n  (slot?frame2_base:frame_base)[i]=')
s=replace(s,' if(z==DOOM_FPS_FRAMES){',' phase_ticks[z-1u][1]=ticks;\n if(z==DOOM_FPS_FRAMES){')
s=replace(s,' /* PIATVR exposes only the odd page', ' if(z==DOOM_FPS_FRAMES){\n  unsigned int *t=(unsigned int*)((slot?frame2_base:frame_base)+64896u);\n  t[0]=0x31464f50u;t[1]=1u;t[2]=DOOM_FPS_FRAMES-1u;t[3]=100u;\n  for(i=0;i<(DOOM_FPS_FRAMES-1u)*4u;i++)t[4u+i]=((unsigned int*)phase_ticks)[i];\n }\n /* PIATVR exposes only the odd page')
s=replace(s,' live[base+1u]=byte_fnv(slot?frame2_base:frame_base,FRAME_BYTES);',' phase_ticks[z-1u][2]=ticks;\n live[base+1u]=byte_fnv(slot?frame2_base:frame_base,FRAME_BYTES);\n phase_ticks[z-1u][3]=ticks;')
(out/'app.c').write_text(s)
s=(src/'run_bridge.py').read_text()
s=replace(s,'                image=read_card_bytes(live[14+slot],65536)','                observed_ns=time.monotonic_ns()\n                image=read_card_bytes(live[14+slot],65536)\n                read_done_ns=time.monotonic_ns()')
s=replace(s,"                     'live frame payload checksum')","                     'live frame payload checksum')\n                checksum_done_ns=time.monotonic_ns()")
s=replace(s,'                if browser:browser.publish(generation,image)','                if browser:browser.publish(generation,image)\n                http_ready_ns=time.monotonic_ns()')
s=replace(s,'                    sha256=sha(image)))','                    sha256=sha(image), observed_ns=observed_ns,\n                    pci_read_ns=read_done_ns-observed_ns,\n                    host_fnv_ns=checksum_done_ns-read_done_ns,\n                    save_and_http_ns=http_ready_ns-checksum_done_ns,\n                    observed_to_http_ns=http_ready_ns-observed_ns,\n                    engine_elapsed_s=time.monotonic()-began_engine))')
s=replace(s,'                live_seen[slot]=generation','                live_receipts[-1]["ack_write_ns"]=time.monotonic_ns()-http_ready_ns\n                live_seen[slot]=generation')
(out/'run_bridge.py').write_text(s)

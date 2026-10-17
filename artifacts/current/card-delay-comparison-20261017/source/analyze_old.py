#!/usr/bin/env python3
import bisect,hashlib,json,statistics,struct,sys
from pathlib import Path
run,prior,out=map(Path,sys.argv[1:])
def rows(n):return [json.loads(s) for s in (run/n).read_text().splitlines()]
def summary(v):
 v=sorted(v);return dict(count=len(v),mean=statistics.mean(v),p50=statistics.median(v),p95=v[int((len(v)-1)*.95)],min=v[0],max=v[-1])
frames=rows('play-frames.jsonl');assert [x['frame'] for x in frames]==list(range(1,121))
for r in frames:
 b=(run/f"play-0-{r['frame']}.bin").read_bytes()
 assert len(b)==65536 and hashlib.sha256(b).hexdigest()==r['sha256']
 assert b[:64768]==(prior/f"play-0-{r['frame']}.bin").read_bytes()[:64768]
identity=json.loads((run/'request.json').read_text());assert identity['card']['bdf']=='0000:37:04.1'
assert identity['card']['ids']==[0x1069,0x10,0x1069,0x10]
selected=[x for x in frames if 80<=x['frame']<=118]
assert all(x['transport']=='pingpong' and x['profile']['detail']==1 for x in selected)
pub={x['frame']:x for x in rows('browser-publish.jsonl')}
release={}
for x in rows('pingpong-journal.jsonl'):
 if 'request' in x:
  op,e,g,off=struct.unpack_from('<4I',bytes.fromhex(x['request']))
  if op==4:assert g not in release;release[g]=x
mixed=[x for x in frames if 24<=x['frame']<=118]
pre=[x for x in frames if 24<=x['frame']<=59]
result=dict(including_scripted_level_reload_fps=94/(mixed[-1]['seconds']-mixed[0]['seconds']),
            pre_reload_window=[24,59],pre_reload_fps=35/(pre[-1]['seconds']-pre[0]['seconds']),
            boot_id=identity['boot_id'],profile='optimized low detail, textured planes, full height, no FNV/CRC',
            total_frames=len(frames),window=[80,118],samples=len(selected),
            endpoint_fps=(len(selected)-1)/(selected[-1]['seconds']-selected[0]['seconds']),
            publication_fps=1000*(len(selected)-1)/(selected[-1]['marker'][5]-selected[0]['marker'][5]),
            endpoint_intervals_ms=summary([1000*(b['seconds']-a['seconds']) for a,b in zip(selected,selected[1:])]),
            observed_to_http_ms=summary([1000*(pub[x['frame']]['published']-pub[x['frame']]['observed']) for x in selected]),
            render_ms=summary([x['profile']['render_ms'] for x in selected]),
            render_sampled_cpu_ms=summary([x['profile']['cpu_samples']['render']*10 for x in selected]),
            screen_copy_ms=summary([x['profile']['screen_copy_ms'] for x in selected]),
            adapter_ms=summary([x['profile']['adapter_ms'] for x in selected]),
            release_gate_wait_ms=summary([release[x['frame']]['gate_wait_ns']/1e6 for x in selected]),
            release_ioctl_ms=summary([release[x['frame']]['ioctl_ns']/1e6 for x in selected]),
            ready_to_release_ms=summary([x['ready_to_release_seconds']*1000 for x in selected]),
            engine_ready_to_first_frame_s=frames[0]['engine_seconds'],
            first_frame_wad_requests=frames[0]['wad_requests'],
            full_paired_audits=len(json.loads((run/'snapshots.json').read_text())),
            stall=json.loads((run/'doom-pingpong-stall.json').read_text()),
            stopped_held=json.loads((run/'doom-pingpong-result.json').read_text())['stopped_held'],
            all_pixels_palette_match_prior=True)
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

import json,statistics,sys
from pathlib import Path
p=Path(sys.argv[1]);rows=[json.loads(l) for l in (p/'stress-frames.jsonl').read_text().splitlines()];r=json.loads((p/'stress-result.json').read_text());snaps=json.loads((p/'snapshots.json').read_text())
times=[x['transfer_seconds'] for x in rows]
print(json.dumps(dict(frames=len(rows),producer='deterministic byte pattern; not Doom FPS',elapsed_first_to_last=rows[-1]['seconds']-rows[0]['seconds'],fps_first_to_last=(len(rows)-1)/(rows[-1]['seconds']-rows[0]['seconds']),transfer_seconds=dict(mean=statistics.mean(times),median=statistics.median(times),min=min(times),max=max(times)),paired_frames=sum(x['paired'] for x in rows),isolation_checks=r['isolation_checks'],full_monitor_ram_pairs=len(snaps),final_tick=snaps[-1]['words'][5],stop_reason=snaps[-1]['words'][3],full_dma_bytes=len(rows)*73728,zero_wad_reads=r['zero_wad_reads']),indent=2))

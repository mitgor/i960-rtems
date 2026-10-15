#!/usr/bin/env python3
"""Additional overhead accounting; no filtering of slow steady-state frames."""
import json,statistics,sys
from pathlib import Path
out=Path(sys.argv[1]);rows=lambda n:[json.loads(l) for l in (out/n).read_text().splitlines()]
f=rows('pingpong-frames.jsonl');steady=f[20:]
lo=steady[0]['detected_monotonic'];hi=steady[-1]['detected_monotonic']+steady[-1]['ready_to_copy_release_seconds']
queries=[e for e in rows('upload-journal.jsonl') if e['op']==2 and lo<=e['start_ns']/1e9<=hi]
intervals=[(b['seconds']-a['seconds'])*1000 for a,b in zip(steady,steady[1:])]
print(json.dumps(dict(full_audit_pairs=len(json.loads((out/'snapshots.json').read_text())),steady_frame_interval_ms=dict(min=min(intervals),max=max(intervals),mean=statistics.mean(intervals),median=statistics.median(intervals)),ordinary_upload_queries_during_steady_frames=len(queries),ordinary_upload_query_mean_ms=statistics.mean(e['ns']/1e6 for e in queries),ordinary_upload_query_total_ms=sum(e['ns']/1e6 for e in queries),note=f'10 baseline intervals versus {len(intervals)} ring intervals in one ordered run; no outliers removed; excludes deliberate stall/setup/paired-mailbox windows.'),indent=2))

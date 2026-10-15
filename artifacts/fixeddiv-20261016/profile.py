#!/usr/bin/env python3
"""Per-call-site inclusive elapsed costs, with explicit measurement limits."""
import json,sys,statistics
from pathlib import Path
root=Path(sys.argv[1]);sites=json.loads(Path(sys.argv[2]).read_text());result={};reference_counts=None
for name in ('a1','b1','b2','a2'):
 rows=[json.loads(x) for x in (root/('live-'+name)/'play-frames.jsonl').read_text().splitlines()]
 counts=[r['profile']['fixed_div']['counts'] for r in rows]
 if reference_counts is None:reference_counts=counts
 assert counts==reference_counts, (name,'per-frame call counts differ')
 selected=[r['profile']['fixed_div'] for r in rows if 100<=r['frame']<=499];assert len(selected)==400
 assert all(r['sites']==len(sites) and r['fast']==name.startswith('b') for r in selected)
 table=[]
 for s in sites:
  i=s['id'];calls=sum(r['counts'][i] for r in selected);ticks=sum(r['ticks'][i] for r in selected)
  table.append(dict(**s,calls=calls,calls_per_frame=calls/400,elapsed_ms_per_frame=ticks/4166.7/400,elapsed_us_per_call=ticks/4.1667/calls if calls else None))
 table.sort(key=lambda s:s['elapsed_ms_per_frame'],reverse=True)
 result[name]=dict(frames=400,checks=rows[-1]['profile']['fixed_div']['checks'],calls_per_frame=sum(t['calls_per_frame'] for t in table),elapsed_ms_per_frame=sum(t['elapsed_ms_per_frame'] for t in table),clock_pair_us=(selected[-1]['clock_read_ticks']-selected[0]['clock_read_ticks'])/399/4.1667,sites=table)
print(json.dumps(dict(timer_hz=4166700,includes_interrupts_preemption_calls_and_timer_read=True,not_cpu_cycles=True,all_520_call_count_traces_equal=True,runs=result),indent=2))

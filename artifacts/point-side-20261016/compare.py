#!/usr/bin/env python3
"""Compare complete matched 100–499 windows, including every interval."""
import json,statistics,sys
from pathlib import Path
runs=json.loads(Path(sys.argv[1]).read_text())['runs']
def group(prefix):
 rows=[next(b for b in v if b['first']==100 and b['last']==499) for k,v in runs.items() if k.startswith('live-'+prefix)]
 assert len(rows)==2
 return dict(runs=2,frames=800,intervals=798,host_fps=2/sum(1/r['host_fps'] for r in rows),publication_fps=2/sum(1/r['publication_fps'] for r in rows),renderer_ms=statistics.mean(r['render_ms']['mean'] for r in rows),renderer_cpu_ms=statistics.mean(r['render_cpu_sample_ms'] for r in rows),components_ms={k:statistics.mean(r['renderer_components_ms'][k] for r in rows) for k in rows[0]['renderer_components_ms']},cpu_components_ms={k:statistics.mean(r['cpu_components_sample_ms'][k] for r in rows) for k in rows[0]['cpu_components_sample_ms']},observed_to_http_ms=statistics.mean(r['observed_to_browser_ms']['mean'] for r in rows),gate_wait_ms=statistics.mean(r['gate_wait_ms']['mean'] for r in rows),ioctl_ms=statistics.mean(r['ioctl_ms']['mean'] for r in rows),card_start_to_http_bounds_ms=[statistics.mean(r['card_start_to_browser_mean_bounds_ms'][i] for r in rows) for i in range(2)])
a,b=group('a'),group('b')
print(json.dumps(dict(baseline=a,candidate=b,fps_gain_percent=100*(b['host_fps']/a['host_fps']-1),renderer_reduction_percent=100*(1-b['renderer_ms']/a['renderer_ms'])),indent=2))

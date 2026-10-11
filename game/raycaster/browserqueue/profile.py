#!/usr/bin/env python3
"""Join actual browser draws to completed host updates and kernel profiles."""
import argparse
import json
import statistics
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('browser',type=Path);a=p.parse_args()
phases=json.loads((a.capture/'phases.json').read_text())
host=json.loads((a.capture/'browser-timing.json').read_text())
byid={s['update_id']:s for s in host};assert len(byid)==len(host)
reports=json.loads((a.browser/'summary.json').read_text());groups={};seen=set()
for report in reports:
    filename=f"{report['round']}-{report['pacing']}.json"
    data=json.loads((a.browser/filename).read_text());samples=data['samples']
    assert len(samples)==80 and data['max_in_flight']==1
    for sample in samples:
        key=sample['update_id'];assert key not in seen;seen.add(key);actual=byid[key]
        assert sample['keys']==actual['keys'] and sample['reset']==actual['reset'] and sample['frame_id']==actual['frame_id']
        assert abs(sample['callback_ms']-(actual['end']-actual['start'])*1000)<1e-6
    steady=[s for s in samples[5:] if not s['reset'] and s['interval']>0]
    groups.setdefault(report['pacing'],[]).extend(steady)
assert seen==set(byid)
def stats(values):
    return dict(mean=statistics.mean(values),median=statistics.median(values),min=min(values),max=max(values))
result=dict(draws=len(seen),host_updates=len(host),full_audits=len(phases),combined_requests=sum(s['label']=='browser-combined' for s in phases),pacing={})
for name,rows in groups.items():
    interval=stats([s['interval'] for s in rows]);callback=stats([s['callback_ms'] for s in rows])
    result['pacing'][name]=dict(draw_interval_ms=interval,host_step_ms=callback,delivered_fps=1000/interval['mean'])
steady=[s for s in phases if s['label']=='browser-combined']
result['host_stage_ms']={name:stats([s[name]/1e6 for s in steady]) for name in ['host_oracle_ns','host_snapshot_read_ns','host_archive_ns','host_slot_check_ns','host_log_check_ns']}
result['board_step_ms']=stats([s['wall_ns']/1e6 for s in steady])
result['kernel_ms']=stats([s['kernel_ns']/1e6 for s in steady])
result['kernel_execute_ms']=stats([s['execute_ns']/1e6 for s in steady])
result['full_audit_ms']=stats([s['full_audit_ns']/1e6 for s in steady])
old,new=[result['pacing'][k]['draw_interval_ms']['mean'] for k in ('legacy-delay','raf-single-flight')]
result['draw_interval_reduction_percent']=(old-new)/old*100
print(json.dumps(result,indent=2))

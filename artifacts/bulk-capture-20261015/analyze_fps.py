#!/usr/bin/env python3
"""Decompose host FPS windows into publication time and delivery-lag change.
Card publication timestamps resolve 10 ms; no cross-clock offset is needed.
These are retrospective diagnostics, not replacement acceptance windows.
"""
import argparse,json,statistics
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);p.add_argument('candidate',type=Path);a=p.parse_args()
def analyze(path):
 f=[json.loads(x) for x in (path/'play-frames.jsonl').read_text().splitlines()]
 out={}
 for lo,hi in [(21,50),(21,59),(51,59),(69,98)]:
  x,y=f[lo-1],f[hi-1];host=y['seconds']-x['seconds'];card=(y['marker'][5]-x['marker'][5])/1000
  out[f'{lo}-{hi}']=dict(intervals=hi-lo,host_seconds=host,publication_seconds=card,delivery_lag_change_seconds=host-card,host_fps=(hi-lo)/host,publication_fps=(hi-lo)/card)
 out['renderer_mean_ms']=statistics.mean(x['profile']['render_ms'] for x in f[20:50])
 out['publication_wait_mean_ms_22_50']=statistics.mean(x['profile']['previous_publish_wait_ms'] for x in f[21:50])
 return out
b,c=analyze(a.baseline),analyze(a.candidate);x,y=b['21-50'],c['21-50']
extra=y['host_seconds']-x['host_seconds'];lag=y['delivery_lag_change_seconds']-x['delivery_lag_change_seconds'];pub=y['publication_seconds']-x['publication_seconds']
assert abs(extra-lag-pub)<1e-9
result=dict(baseline=b,candidate=c,window_decomposition=dict(extra_host_seconds=extra,publication_seconds_change=pub,delivery_lag_change_difference_seconds=lag,lag_share_percent=100*lag/extra),target_5_19=dict(frame_budget_ms=1000/5.19,current_publication_interval_ms=1000/y['publication_fps'],required_interval_reduction_ms=1000/y['publication_fps']-1000/5.19))
print(json.dumps(result,indent=2))

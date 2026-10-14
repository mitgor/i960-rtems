#!/usr/bin/env python3
"""Measured same-run modes; no additive claims for overlapping timings."""
import argparse,json,statistics
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--native',type=Path,required=True);p.add_argument('--previous',type=Path);a=p.parse_args()
f=[json.loads(s) for s in (a.capture/'play-frames.jsonl').read_text().splitlines()];assert len(f)==52
native_diffs=[]
for g,row in enumerate(f,1):
 b=(a.capture/f'play-0-{g}.bin').read_bytes();n=(a.native/f'frame-{g}.bin').read_bytes()
 assert len(b)==len(n)==65536 and b[64000:64768]==n[64000:64768]
 diff=sum(x!=y for x,y in zip(b[:64000],n[:64000]));native_diffs.append(diff);assert diff==7,(g,diff)
 if a.previous:assert b[:64768]==(a.previous/f'play-0-{g}.bin').read_bytes()[:64768],g
reports=[json.loads(s) for s in (a.capture/'frame-dma-results.jsonl').read_text().splitlines()]
blocks=[]
for lo,hi,name in [(5,16,'fnv-copy-before'),(17,28,'no-fnv-copy'),(29,40,'no-fnv-direct'),(41,52,'fnv-copy-after')]:
 rows=f[lo-1:hi];ms={k:statistics.mean(r['profile'][k] for r in rows) for k in rows[0]['profile'] if k.endswith('_ms')}
 dma={k:statistics.mean(r['profile']['dma'][k] for r in rows) for k in ('prepare_ms','hardware_ms','cleanup_ms','total_ms')}
 host={k:statistics.mean(r[k] for r in reports[lo-1:hi])*1000 for k in ('submit_seconds','completion_wait_seconds','guarded_readback_seconds')}
 elapsed=rows[-1]['seconds']-rows[0]['seconds'];blocks.append(dict(name=name,first=lo,last=hi,fps=11/elapsed,interval_ms=elapsed*1000/11,card_ms=ms,dma_ms=dma,host_ms=host,profile_read_ms=statistics.mean(r['profile_read_seconds'] for r in rows)*1000))
baseline=22/sum(11/blocks[i]['fps'] for i in (0,3));fast=blocks[2]['fps']
print(json.dumps(dict(blocks=blocks,baseline_fps=baseline,optimized_fps=fast,speedup=fast/baseline,improvement_percent=100*(fast/baseline-1),native_pixel_differences=native_diffs,previous_card_pixels_palette_equal=bool(a.previous),full_audit_pairs=len(json.loads((a.capture/'snapshots.json').read_text())),clock_resolution_ms=10),indent=2))

#!/usr/bin/env python3
"""Derive observed memory figures and explicit provisional RTEMS reservations."""
import argparse,json,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();root=a.root
runs=json.loads((root/'profiles.json').read_text());good=[r for r in runs if r['returncode']==0 and r.get('profile',{}).get('frames')==2100]
sections={}
for line in (root/'cross/i960/sections.txt').read_text().splitlines():
 m=re.fullmatch(r'(\.\S+)\s+(\d+)\s+\d+',line)
 if m:sections[m[1]]=int(m[2])
raw=[line.split()[-1] for line in (root/'cross/i960/undefined.txt').read_text().splitlines() if line.strip()]
symbols=[s[1:] for s in raw] # i960 object ABI prepends one underscore.
groups={
 'platform_hooks':[s for s in symbols if s.startswith('DG_')],
 'compiler_helpers':[s for s in symbols if s.startswith('__') and s not in ('__errno','__swbuf')],
 'newlib_state':[s for s in symbols if s in ('__errno','__swbuf','_ctype_','_impure_ptr')],
 'allocation':[s for s in symbols if s in ('malloc','calloc','realloc','free','strdup')],
 'files_and_process':[s for s in symbols if s in ('fopen','fclose','fflush','fread','fseek','ftell','fwrite','mkdir','remove','rename','system','exit')],
}
assigned=sum(groups.values(),[]);groups['format_strings_math']=[s for s in symbols if s not in assigned]
assert sorted(sum(groups.values(),[]))==sorted(symbols)
full=[r['profile'] for r in good if r['mb']==6]
reservation=dict(engine_sections=sum(sections.values()),zone=6*1024*1024,non_zone_heap_including_output=256*1024,game_stack=64*1024,two_guarded_frame_slots=2*(64000+64),wad_transfer_window=64*1024,rtems_runtime_and_helpers_allowance=512*1024,guards_and_alignment_allowance=64*1024)
report=dict(engine_sections=sections,compiled_sources=json.loads((root/'cross/i960/build.json').read_text())['source_count'],undefined_symbols=groups,undefined_count=len(symbols),workloads=len(runs),completed_capped_workloads=len(good),profiled_frames=sum(r['profile']['frames'] for r in good),observed_6mib=dict(direct_allocation_peak=max(r['engine_malloc_peak'] for r in full),outside_zone_peak=max(r['engine_malloc_peak']-r['zone_reserved'] for r in full),zone_nonpurgeable_peak=max(r['zone_nonpurgeable_peak'] for r in full),zone_total_used_peak=max(r['zone_used_peak_including_headers'] for r in full),instrumented_stack_span=max(r['instrumented_engine_stack_span'] for r in full),largest_wad_read=max(r['wad_max_request'] for r in full)),provisional_reservation=reservation,provisional_total=sum(reservation.values()),requested_arena=8*1024*1024,headroom=8*1024*1024-sum(reservation.values()))
print(json.dumps(report,indent=2))

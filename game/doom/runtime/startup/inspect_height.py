#!/usr/bin/env python3
"""Read-only comparison of validated height and frame-delivery checkpoint records.
Incomplete diagnostics never establish an accepted engine result or a fault PC.
"""
import argparse,json,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'rtems/residentnet'))
from checkpoint_replay import check,describe
p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
build=a.root/'admission';capture=a.root/'live';verified=check(capture,build)
raw=list(struct.iter_unpack('<8I',(build/'startup-checkpoints.bin').read_bytes()))
observed=[json.loads(l) for l in (capture/'startup-checkpoints.jsonl').read_text().splitlines()]
def selected(rows):
 return [describe(w) for w in rows if w[3] in (27,37,38,40,41,42,43,44,50,51,60,61,62) or 63<=w[3]<=98]
out=dict(accepted=False,diagnostic_only=True,wire_validation=verified,host=selected(raw),card_by_generation={str(g):selected([w for w in observed if w[2]==g]) for g in sorted({w[2] for w in observed})},limits=['Absent captured marker is not a fault PC or proof of the last executed instruction.','Matching counts or height fingerprints do not establish every geometry field.','Full snapshot/RAM/WAD audits and final STOP/repeat/drain gates remain separate.'])
a.output.write_text(json.dumps(out,indent=2)+'\n');print('Validated checkpoint wire log and wrote height/delivery comparison; diagnostic only')

#!/usr/bin/env python3
"""Derive the two missing convenience files; never modify the raw capture.
The original harness failed at its obsolete 14-cancellation assertion AFTER
STOP/drain. The parked reply is raw ioctl evidence; monitor text comes from
retained dmesg, not a claimed debugfs capture. Original error remains intact.
"""
import argparse,hashlib,json,shutil,struct
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
s=a.root/'live';t=a.root/'replay-view';assert not t.exists()
e=json.loads((s/'upload-journal.jsonl').read_text().splitlines()[-1]);assert 'errno' not in e
req=bytes.fromhex(e['request']);res=bytes.fromhex(e['response']);assert len(req)==len(res)==1056
q=struct.unpack_from('<16I',res,32);assert struct.unpack_from('<I',req)[0]==2
assert q[0]==0x31525055 and q[3]==q[4]==q[15]==0 and q[9]==15
err=(s/'error.txt').read_text();assert 'q[9]==(14 if' in err and err.rstrip().endswith('AssertionError')
log=(a.root/'dmesg-after-live.txt').read_text();assert 'MONITOR enter' in log and 'submit op=' not in log[log.index('MONITOR enter'):]
shutil.copytree(s,t)
(t/'upload-parked.json').write_text(json.dumps(list(q))+'\n')
(t/'last-control.txt').write_text(log)
record={'original_harness_passed':False,'reason':'obsolete 14 vs 15 cancellation assertion after successful physical STOP; missing convenience files derived from raw records', 'last_control_source':'dmesg-after-live.txt (ring-buffer tail, not original debugfs result; same no-submit-since-monitor check)', 'source_sha256':{n:hashlib.sha256((a.root/n).read_bytes()).hexdigest() for n in ['live/upload-journal.jsonl','live/error.txt','live/controls.json','live/control-journal.jsonl','live/failure-snapshot.json','live/snapshots.json','live/ram-diagnostics.jsonl','dmesg-after-live.txt']},'parked_reply':q}
# Separate the exception handler's extra diagnostic page from the completed
# acceptance stream; it has no paired RAM page and is not a new test snapshot.
controls=json.loads((s/'controls.json').read_text());tail=controls[-65:]
assert tail[0]['op']==7 and tail[0]['arg']==0
assert [(e['op'],e['arg']) for e in tail[1:]]==[(5,i) for i in range(64)]
epoch=json.loads((s/'request.json').read_text()).get('epoch',tail[0]['epoch'])
for e in tail:
 w=e['words'];assert e['epoch']==epoch and w[0]==e['op'] and w[1]==epoch and w[3:5]==[1,0] and w[6:]==[0,0]
 assert w[5]==((0x95000000 if e['op']==7 else 0x92000000|(e['arg']<<16))|epoch)
failure=[e['words'][2] for e in tail[1:]]
assert failure==json.loads((s/'failure-snapshot.json').read_text())
last=json.loads((s/'snapshots.json').read_text())[-1]['words']
assert failure[2]==last[2]==2 and failure[4:]==last[4:] and failure[1]>last[1]
assert [json.loads(l) for l in (s/'control-journal.jsonl').read_text().splitlines()]==controls
(t/'exception-controls.json').write_text(json.dumps(tail,indent=2)+'\n')
(t/'controls.json').write_text(json.dumps(controls[:-65],indent=2)+'\n')
(t/'control-journal.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in controls[:-65]))
record['exception_diagnostics']='Last 65 raw control records separated after validating all tags and exact parked state against final regular snapshot; retained in exception-controls.json'
ram=[json.loads(l)['words'] for l in (s/'ram-diagnostics.jsonl').read_text().splitlines()]
assert ram and all(len(w)==64 and w[40:52]==[0]*12 for w in ram)
record['irq_rejection_records_checked']=len(ram)
record['irq_rejection_records_all_zero']=True
(t/'recovery-provenance.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))

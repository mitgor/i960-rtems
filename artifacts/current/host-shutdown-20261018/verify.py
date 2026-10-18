#!/usr/bin/env python3
"""Replay the shutdown investigation and private-workqueue card acceptance.

The final physical power-off test and post-reset ROM pair remain deferred.
No archived executable or driver is executed by this verifier.
"""
import hashlib,json,struct,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def unpack(path):
 with tarfile.open(path) as t:return {m.name:t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
a=unpack(HERE/'acceptance.tar.xz')
b=unpack(HERE.parent/'accele160-flat-20261018/acceptance-pre-reset.tar.xz')
name,=[n for n in a if n.endswith('/run/result.json')];prefix=name[:-len('result.json')]
result=json.loads(a[name]);game=result['games'][0];g=prefix+'persist/game-0001/'
rows=[json.loads(x) for x in a[g+'live-frame-receipts.jsonl'].splitlines()]
assert len(rows)==result['frames']==result['dma_frames']==218 and result['full_audits_before']
assert sum(r['paired_pio'] for r in rows)==32 and game['idle_verified']
assert result['claim_report'][5:7]==['0x45495551','0x00000000'] and result['grant_retained']
assert game['keyboard']['published']==game['keyboard']['consumed']==16 and game['keyboard']['pending']==0
module=sha(a['build/admit_command.ko'])
assert module=='2886bd370752621fd82013f27c435c76cf6b40a10e928c12a68e928b0d6e1825'
assert json.loads(a[prefix+'preflight.json'])['modules']['admit']==module
m=json.loads(a['bundle/project/rtems/accele160/doom_dma/persistent-manifest.json'])
assert m['admit_module_sha256']==module and m['admit_source_sha256']==sha(a['build/admit_command.c'])
assert a['build/admit_command.c']==a['bundle/project/host/accele160/ram_admit/admit_command.c']
source=a['build/admit_command.c']
assert b'queue_work(command_queue, &work)' in source and b'schedule_work(&work)' not in source
assert b'wait_for_completion(&completed)' in source and b'__module_get(THIS_MODULE)' in source
assert b'alloc_workqueue("accele_ram_admit", WQ_UNBOUND | WQ_MEM_RECLAIM, 1)' in source
baseline_root,={n.split('/run/')[0] for n in b if n.endswith('/run/result.json')}
for r in rows:
 assert r['generation']==r['local_frame'] and r['game_run']==1
 raw=a.get(g+f'live-frames/frame-{r["generation"]:04d}.bin')
 if raw is None:continue
 cap=a[g+f'dma-frame-{r["generation"]:04d}.bin']
 assert cap[:4096]==b'\xa5'*4096 and cap[69664:]==b'\xa5'*8160 and cap[4096:69632]==raw
 assert sha(raw)==r['sha256']
 assert struct.unpack_from('<8I',cap,69632)==(0x31505044,0x161610e1,r['generation'],r['slot'],65536,r['source'],r['card_tick'],~r['generation']&0xffffffff)
 if r['local_frame']<=32:
  reference=b[baseline_root+f'/run/persist/game-0004/live-frames/frame-{384+r["local_frame"]:04d}.bin']
  assert raw[:64768]==reference[:64768]
reads=[json.loads(x) for x in a[g+'engine-reads.jsonl'].splitlines()]
oracle=list(struct.iter_unpack('<II',b['bundle/inputs/native-requests.bin']))
assert len(reads)==game['wad_reads']==5045 and [(r['offset'],r['n']) for r in reads[:len(oracle)]]==oracle
s=json.loads((HERE/'private-queue-live.json').read_text())
assert s['gdm_stop_returncode']==0 and s['gdm_stop_seconds']<2
assert 'started=1 done=0' in s['after_graphics_stop'] and 'Xorg' not in s['after_graphics_stop']
assert s['gdm_restore_returncode']==0 and s['final']['state']=='idle'
for r in s['probe']['frames']:assert rows[r['generation']-1]['sha256']==r['sha256']
old=(HERE/'previous-kernel.txt').read_text();shutdown=(HERE/'previous-shutdown.txt').read_text()
assert 'Workqueue: events worker [admit_command]' in old and 'Workqueue: myrs_wq_7 myrs_monitor' in old
assert 'os_flush_work_queue' in old and 'session-c1.scope: Stopping timed out' in shutdown
assert 'Killing process 1110 (Xorg)' in shutdown
nv=json.loads(a['nvidia-flush-source.json'])
assert 'NV_WORKQUEUE_FLUSH();' in nv[0]['excerpt'] and 'flush_scheduled_work();' in nv[1]['excerpt']
print(json.dumps(dict(frames=218,paired_pio=32,native_baseline_matches=32,native_wad_oracle_reads=len(oracle),module_sha256=module,
 gdm_stop_seconds=s['gdm_stop_seconds'],card_command_still_pending=True,global_shutdown_quiescent=True,
 physical_bare_host_poweroff='user confirmed fans stopped',final_retained_card_poweroff='deferred by user',
 post_reset_flash_pair=False,ordinary_launcher_changed=False),indent=2))

"""Read-only progress from already-written journals; no card commands."""
import json,struct
from pathlib import Path
p=Path('/home/mit/i960-doom-dma-fixed-20261014/live')
row={'frames':len(list(p.glob('play-0-*.bin')))}
s=p/'snapshots.json'
if s.exists():
 a=json.loads(s.read_text());row['full_snapshots']=len(a)
 if a:row.update(ticks=a[-1]['words'][5],state=a[-1]['words'][2],faults=a[-1]['words'][11])
w=p/'wad-journal.jsonl'
if w.exists():
 with w.open('rb') as f:
  f.seek(0,2);size=f.tell();f.seek(max(0,size-12000));lines=f.read().splitlines()
 for line in reversed(lines[:-1]):
  try:r=json.loads(line)
  except Exception:continue
  if r.get('op')==4:
   words=struct.unpack_from('<8I',bytes.fromhex(r['request']),32);row['wad_sequence']=words[1];row['wad_offset']=words[3];break
 row['wad_journal_bytes']=size
row['error']=(p/'error.txt').read_text() if (p/'error.txt').exists() else None
print(json.dumps(row))

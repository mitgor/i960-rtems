"""Full packet evidence with constant-size per-exchange append work."""
import json

def append_packet(out,record):
 with (out/'packet-journal.jsonl').open('a') as stream:
  stream.write(json.dumps(record)+'\n')

def finish_packets(out,records):
 (out/'packets.json').write_text(json.dumps(records)+'\n')

def read_packets(out):
 records=json.loads((out/'packets.json').read_text())
 journal=out/'packet-journal.jsonl'
 if journal.exists():
  raw=journal.read_text()
  assert not raw or raw.endswith('\n'),'incomplete packet journal'
  assert [json.loads(row) for row in raw.splitlines()]==records,'packet evidence mismatch'
 return records
